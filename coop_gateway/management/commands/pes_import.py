# encoding: utf-8

import os
import sys

import requests

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from coop_local.models import (
    Contact,
    Organization,
    Person,
)

from ...models import (
    ForeignOrganization,
    ForeignPerson,
)
from ...signals import (
    organization_saved,
    person_saved,
)
from ...serializers import (
    deserialize_contact,
    deserialize_organization,
    deserialize_person,
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

    def _is_update(self, data):
        return self.foreign_model.objects.filter(uuid=data['uuid']).all()

    def _is_create(self, data):
        return not self.model.objects.filter(uuid=data['uuid']).all()

    def _update(self, data):
        sys.stdout.write('Update %s %s\n' % (self.model, data['uuid']))
        instance = self.model.objects.get(uuid=data['uuid'])

        self._map(instance, data)
        delete_old_contacts(instance, data.get('contacts', []))

    def _create(self, data):
        sys.stdout.write('Create %s %s\n' % (self.model, data['uuid']))
        self.foreign_model(uuid=data['uuid']).save()
        instance = self.model()

        self._map(instance, data)

    def handle(self):
        url = os.path.join(settings.PES_HOST, self.endpoint)
        sys.stdout.write('GET %s\n' % url)
        response = requests.get(url)
        response.raise_for_status()
        sid = transaction.savepoint()

        try:
            for data in response.json():
                if self._is_update(data):
                    self._update(data)
                elif self._is_create(data):
                    self._create(data)
                sid = transaction.savepoint_commit(sid)
        except Exception as e:
            sys.stdout.write('Error %s\n' % e)
            transaction.rollback(sid)
        else:
            transaction.commit()


class PesImportOrganisation(PesImport):
    endpoint = 'api/organizations/'
    model = Organization
    foreign_model = ForeignOrganization

    _deserialize = staticmethod(deserialize_organization)

    def _save(self, organization):
        post_save.disconnect(organization_saved, Organization)
        organization.save()
        post_save.connect(organization_saved, Organization)


class PesImportPerson(PesImport):
    endpoint = 'api/persons/'
    model = Person
    foreign_model = ForeignPerson

    _deserialize = staticmethod(deserialize_person)

    def _save(self, person):
        post_save.disconnect(person_saved, Person)
        person.save()
        post_save.connect(person_saved, Person)


class PesImportCommand(BaseCommand):
    help = 'Imports data from the PES'

    def import_organizations(self):
        handler = PesImportOrganisation()
        handler.handle()

    def import_persons(self):
        handler = PesImportPerson()
        handler.handle()

    def handle(self, *args, **options):
        self.import_organizations()
        self.import_persons()

Command = PesImportCommand
