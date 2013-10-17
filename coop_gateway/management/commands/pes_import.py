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


class PesImportOrganisation(object):
    def __init__(self):
        self.sid = None

    def _save_organization(self, organization):
        post_save.disconnect(organization_saved, Organization)
        organization.save()
        post_save.connect(organization_saved, Organization)

    def _map(self, organization, data):
        deserialize_organization(organization, data)
        self._save_organization(organization)

        if 'contacts' in data:
            for contact_data in data['contacts']:
                update_contact(organization, contact_data)

        self._save_organization(organization)

    def _is_update(self, data):
        return ForeignOrganization.objects.filter(uuid=data['uuid']).all()

    def _is_create(self, data):
        return not Organization.objects.filter(uuid=data['uuid']).all()

    def _update(self, data):
        sys.stdout.write('Update organization %s\n' % data['uuid'])
        organization = Organization.objects.get(uuid=data['uuid'])

        self._map(organization, data)
        delete_old_contacts(organization, data.get('contacts', []))

    def _create(self, data):
        sys.stdout.write('Create organization %s\n' % data['uuid'])
        ForeignOrganization(uuid=data['uuid']).save()
        organization = Organization()

        self._map(organization, data)

    def handle(self):
        url = os.path.join(settings.PES_HOST, 'api/organizations/')
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


class PesImportPerson(object):

    def _save_person(self, person):
        post_save.disconnect(person_saved, Person)
        person.save()
        post_save.connect(person_saved, Person)

    def _update_person(self, person, data):
        deserialize_person(person, data)
        self._save_person(person)

        if 'contacts' in data:
            for contact_data in data['contacts']:
                update_contact(person, contact_data)

        self._save_person(person)

    def _is_update(self, data):
        return ForeignPerson.objects.filter(uuid=data['uuid']).all()

    def _is_create(self, data):
        return not Person.objects.filter(uuid=data['uuid']).all()

    def handle(self):
        url = os.path.join(settings.PES_HOST, 'api/persons/')
        sys.stdout.write('GET %s\n' % url)
        response = requests.get(url)
        response.raise_for_status()

        for data in response.json():
            if self._is_update(data):
                try:
                    sys.stdout.write('Update person %s\n' % data['uuid'])
                    person = Person.objects.get(uuid=data['uuid'])

                    self._update_person(person, data)
                    delete_old_contacts(person, data.get('contacts', []))
                except Exception as e:
                    sys.stdout.write('Error %s\n' % e)
                    transaction.rollback()
            elif self._is_create(data):
                try:
                    sys.stdout.write('Create person %s\n' % data['uuid'])
                    ForeignPerson(uuid=data['uuid']).save()
                    person = Person()

                    self._update_person(person, data)
                except Exception as e:
                    sys.stdout.write('Error %s\n' % e)
                    transaction.rollback()


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
