# encoding: utf-8

import os
import sys

import requests

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import (
    transaction,
    DatabaseError,
    IntegrityError,
)
from django.db.models.signals import post_save

from coop_local.models import (
    Contact,
    Organization,
    Person,
    Engagement,
    Role,
)

from ...models import (
    ForeignOrganization,
    ForeignPerson,
    ForeignRole,
)
from ...signals import (
    organization_saved,
    person_saved,
)
from ...serializers import (
    deserialize_contact,
    deserialize_organization,
    deserialize_person,
    deserialize_role,
)


def get_or_create_object(model, uuid):
    try:
        return model.objects.get(uuid=uuid)
    except ObjectDoesNotExist:
        return model(uuid=uuid)


def update_contact(content_object, data):
    contact = get_or_create_object(Contact, uuid=data['uuid'])

    if contact.content_object and contact.content_object != content_object:
        return

    deserialize_contact(content_object, contact, data)
    contact.save()


def is_old_contact(content_object, contact, contact_uuids):
    return (
        contact.uuid not in contact_uuids
        and contact.content_object == content_object
    )


def delete_old_contacts(content_object, data):
    contact_uuids = [
        contact_data['uuid']
        for contact_data in data
    ]

    for contact in content_object.contacts.all():
        if is_old_contact(content_object, contact, contact_uuids):
            contact.delete()


class PesImport(object):

    def _map(self, instance, data):
        self._deserialize(instance, data)
        self._save(instance)

        if 'contacts' in data:
            for contact_data in data['contacts']:
                update_contact(instance, contact_data)

        self._save(instance)

    def _exists(self, data):
        return bool(self.model.objects.filter(**{
            self.key: data[self.key]
        }).values())

    def _update(self, data):
        instance = self.model.objects.get(**{
            self.key: data[self.key]
        })

        self._map(instance, data)
        delete_old_contacts(instance, data.get('contacts', []))

    def _create(self, data):
        instance = self.model()
        self._save(instance)
        self._map(instance, data)

        self.foreign_model(
            local_object=instance
        ).save()

        return instance

    def get_data(self):
        url = os.path.join(settings.PES_HOST, self.endpoint)
        sys.stdout.write('GET %s\n' % url)
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @transaction.commit_manually
    def handle(self):
        for data in self.get_data():
            try:
                instance_info = (self.model.__name__, data['uuid'])
                sid = transaction.savepoint()
                if self._exists(data):
                    sys.stdout.write('Update %s %s ' % instance_info)
                    self._update(data)
                else:
                    sys.stdout.write('Create %s %s ' % instance_info)
                    self._create(data)
                transaction.savepoint_commit(sid)
                sys.stdout.write('Done\n')
            except DatabaseError as e:
                sys.stderr.write('DatabaseError\n%s\n' % e)
                transaction.savepoint_rollback(sid)
            except IntegrityError as e:
                sys.stderr.write('IntegrityError\n%s\n' % e)
                transaction.savepoint_rollback(sid)
            except Exception as e:
                sys.stderr.write('%s\n%s\n' % (type(e).__name__, e))
                transaction.savepoint_rollback(sid)

        transaction.commit()


class PesImportOrganisations(PesImport):
    endpoint = 'api/organizations/'
    model = Organization
    foreign_model = ForeignOrganization
    key = 'uuid'

    _deserialize = staticmethod(deserialize_organization)

    def _save(self, organization):
        post_save.disconnect(organization_saved, Organization)
        organization.save()
        post_save.connect(organization_saved, Organization)

    def _delete_old_engagements(self, organization):
        Engagement.objects.filter(organization=organization).delete()

    def _create_engagement(self, organization, data):
        person = Person.objects.get(uuid=data['person'])
        role_uuid = self.translations['roles'].get(data['role'])
        if role_uuid:
            role = Role.objects.filter(uuid=role_uuid)[0]
        else:
            role = None

        engagement = Engagement(organization=organization,
                                person=person,
                                role=role,
                                role_detail=data.get('role_detail', ''))
        engagement.save()

    def _update_members(self, organization, data):
        if 'members' in data:
            self._delete_old_engagements(organization)

            for engagement_data in data['members']:
                self._create_engagement(organization, engagement_data)

    def _map(self, organization, data):
        super(PesImportOrganisations, self)._map(organization, data)
        self._update_members(organization, data)
        self._save(organization)


class PesImportPersons(PesImport):
    endpoint = 'api/persons/'
    model = Person
    foreign_model = ForeignPerson
    key = 'uuid'

    _deserialize = staticmethod(deserialize_person)

    def _save(self, person):
        post_save.disconnect(person_saved, Person)
        person.save()
        post_save.connect(person_saved, Person)


class PesImportRoles(PesImport):
    endpoint = 'api/roles/'
    model = Role
    foreign_model = ForeignRole
    key = 'label'

    _deserialize = staticmethod(deserialize_role)

    def __init__(self):
        self.translations = {}

    def _save(self, role):
        role.save()

    def handle(self):
        for data in self.get_data():
            if self._exists(data):
                sys.stdout.write('Update %s %s ' % (self.model.__name__,
                                                    data['uuid']))
                role = Role.objects.filter(label=data['label'])[0]
            else:
                sys.stdout.write('Create %s %s ' % (self.model.__name__,
                                                    data['uuid']))
                role = self._create(data)

            self.translations[data['uuid']] = role.uuid
            sys.stdout.write('Done\n')


class PesImportCommand(BaseCommand):
    help = 'Imports data from the PES'

    def import_roles(self):
        handler = PesImportRoles()
        handler.handle()
        self.translations['roles'] = handler.translations

    def import_organizations(self):
        handler = PesImportOrganisations()
        handler.translations = self.translations
        handler.handle()

    def import_persons(self):
        handler = PesImportPersons()
        handler.handle()

    def handle(self, *args, **options):
        self.translations = {}
        self.import_roles()
        self.import_persons()
        self.import_organizations()

Command = PesImportCommand
