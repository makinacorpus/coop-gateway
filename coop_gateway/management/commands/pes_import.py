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
        raise Exception('Contact %s do not belong to %s %s' % (
            contact.uuid, type(content_object), content_object.uuid
        ))

    deserialize_contact(content_object, contact, data)
    contact.save()
    return contact


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
        return self.foreign_model.objects.filter(**{
            self.foreign_key: data[self.foreign_key]
        }).all()

    def _is_create(self, data):
        return not self.model.objects.filter(**{
            self.foreign_key: data[self.foreign_key]
        }).all()

    def _update(self, data):
        sys.stdout.write('Update %s %s\n' % (self.model, data['uuid']))
        instance = self.model.objects.get(**{
            self.foreign_key: data[self.foreign_key]
        })

        self._map(instance, data)
        delete_old_contacts(instance, data.get('contacts', []))

    def _create(self, data):
        sys.stdout.write('Create %s %s\n' % (self.model, data['uuid']))
        self.foreign_model(**{
            self.foreign_key: data[self.foreign_key]
        }).save()
        instance = self.model()

        self._map(instance, data)
        return instance

    def get_data(self):
        url = os.path.join(settings.PES_HOST, self.endpoint)
        sys.stdout.write('GET %s\n' % url)
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def handle(self):
        sid = transaction.savepoint()
        try:
            for data in self.get_data():
                if self._exists(data):
                    self._update(data)
                    sid = transaction.savepoint_commit(sid)
                elif self._is_create(data):
                    self._create(data)
                    sid = transaction.savepoint_commit(sid)
        except DatabaseError as e:
            sys.stdout.write('Error %s %s\n' % (type(e), e))
            transaction.rollback(sid)
        else:
            transaction.commit()


class PesImportOrganisations(PesImport):
    endpoint = 'api/organizations/'
    model = Organization
    foreign_model = ForeignOrganization
    foreign_key = 'uuid'

    _deserialize = staticmethod(deserialize_organization)

    def _save(self, organization):
        post_save.disconnect(organization_saved, Organization)
        organization.save()
        post_save.connect(organization_saved, Organization)

    def _delete_old_engagements(self, organization):
        Engagement.objects.filter(organization=organization).delete()

    def _create_engagement(self, organization, data):
        person = Person.objects.get(uuid=data['person'])
        role_uuid = self.role_translations.get(data['role'])
        if role_uuid:
            role = Role.objects.get(uuid=role_uuid)
        else:
            role = None

        engagement = Engagement(organization=organization,
                                person=person,
                                role=role)
        engagement.save()

    def _update_members(self, organization, data):
        if 'members' in data:
            self._delete_old_engagements(organization)

            for engagement_data in data['members']:
                self._create_engagement(organization, engagement_data)

    def _map(self, organization, data):
        super(PesImportOrganisations, self)._map(organization, data)
        self._update_members(organization, data)


class PesImportPersons(PesImport):
    endpoint = 'api/persons/'
    model = Person
    foreign_model = ForeignPerson
    foreign_key = 'uuid'

    _deserialize = staticmethod(deserialize_person)

    def _save(self, person):
        post_save.disconnect(person_saved, Person)
        person.save()
        post_save.connect(person_saved, Person)


class PesImportRoles(PesImport):
    endpoint = 'api/roles/'
    model = Role
    foreign_model = ForeignRole
    foreign_key = 'slug'

    _deserialize = staticmethod(deserialize_role)

    def __init__(self):
        self.role_translations = {}

    def _save(self, role):
        role.save()

    def _exists(self, data):
        return self.model.objects.filter(
            slug=data['slug']
        ).all()

    def handle(self):
        sid = transaction.savepoint()
        try:
            for data in self.get_data():
                if self._exists(data):
                    role = Role.objects.get(slug=data['slug'])
                else:
                    role = self._create(data)
                    sid = transaction.savepoint_commit(sid)

                self.role_translations[data['uuid']] = role.uuid
        except DatabaseError as e:
            sys.stdout.write('Error %s %s\n' % (type(e), e))
            transaction.rollback(sid)
        else:
            transaction.commit()


class PesImportCommand(BaseCommand):
    help = 'Imports data from the PES'

    def import_roles(self):
        handler = PesImportRoles()
        handler.handle()
        self.role_translations = handler.role_translations

    def import_organizations(self):
        handler = PesImportOrganisations()
        handler.role_translations = self.role_translations
        handler.handle()

    def import_persons(self):
        handler = PesImportPersons()
        handler.handle()

    def handle(self, *args, **options):
        self.import_roles()
        self.import_persons()
        self.import_organizations()

Command = PesImportCommand
