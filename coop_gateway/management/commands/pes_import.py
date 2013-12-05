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
from django.db.models.signals import post_save, post_delete

from coop_local.models import (
    Calendar,
    Contact,
    Engagement,
    Event,
    Exchange,
    Organization,
    Person,
    Product,
    Role,
)

from ...models import (
    ForeignCalendar,
    ForeignEvent,
    ForeignExchange,
    ForeignOrganization,
    ForeignPerson,
    ForeignProduct,
    ForeignRole,
)
from ...signals import (
    calendar_deleted,
    calendar_saved,
    event_deleted,
    event_saved,
    exchange_deleted,
    exchange_saved,
    organization_deleted,
    organization_saved,
    person_deleted,
    person_saved,
    product_deleted,
    product_saved,
)
from ...serializers import (
    deserialize_contact,
    deserialize_calendar,
    deserialize_event,
    deserialize_exchange,
    deserialize_organization,
    deserialize_person,
    deserialize_product,
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

    def _before_map(self, instance, data):
        pass

    def _after_map(self, instance, data):
        pass

    def _map(self, instance, data):
        self._deserialize(instance, data)
        self._save(instance)

    def _exists(self, data):
        return bool(self.model.objects.filter(**{
            self.key: data[self.key]
        }).values())

    def _after_update(self, instance, data):
        pass

    def _update(self, data):
        instance = self.model.objects.get(**{
            self.key: data[self.key]
        })

        self._map(instance, data)
        self._after_update(instance, data)

    def _create(self, data):
        instance = self.model()
        self._before_map(instance, data)
        self._map(instance, data)
        self._after_map(instance, data)

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
        keys = []

        for data in self.get_data():
            keys.append(data[self.key])
            try:
                instance_info = (self.model.__name__, data[self.key])
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

        self.delete_missing(keys)

        transaction.commit()

    def delete_missing(self, keys):
        for foreign_model in self.foreign_model.objects.all():
            key = getattr(foreign_model.local_object, self.key, None)
            if key not in keys:
                try:
                    sid = transaction.savepoint()
                    instance_info = (self.model.__name__, key)
                    sys.stdout.write('Delete %s %s ' % instance_info)
                    self._delete(foreign_model.local_object)
                    sys.stdout.write('Done\n')
                    transaction.savepoint_commit(sid)
                except Exception as e:
                    sys.stderr.write('%s\n%s\n' % (type(e).__name__, e))
                    transaction.savepoint_rollback(sid)


class HasContacts(object):

    def _before_map(self, instance, data):
        self._save(instance)

    def _update_contacts(self, content_object, data):
        if 'contacts' in data:
            for contact_data in data['contacts']:
                update_contact(content_object, contact_data)

    def _after_update(self, instance, data):
        delete_old_contacts(instance, data.get('contacts', []))


class PesImportOrganisations(HasContacts, PesImport):
    endpoint = 'api/organizations/'
    model = Organization
    foreign_model = ForeignOrganization
    key = 'uuid'

    _deserialize = staticmethod(deserialize_organization)

    def _save(self, organization):
        post_save.disconnect(organization_saved, Organization)
        organization.save()
        post_save.connect(organization_saved, Organization)

    def _delete(self, organization):
        post_delete.disconnect(organization_deleted, Organization)
        organization.delete()
        post_delete.connect(organization_deleted, Organization)

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

    def _after_map(self, organization, data):
        self._update_members(organization, data)
        self._update_contacts(organization, data)
        self._save(organization)


class PesImportPersons(HasContacts, PesImport):
    endpoint = 'api/persons/'
    model = Person
    foreign_model = ForeignPerson
    key = 'uuid'

    _deserialize = staticmethod(deserialize_person)

    def _save(self, person):
        post_save.disconnect(person_saved, Person)
        person.save()
        post_save.connect(person_saved, Person)

    def _delete(self, person):
        post_delete.disconnect(person_deleted, Person)
        person.delete()
        post_delete.connect(person_deleted, Person)

    def _after_map(self, organization, data):
        self._update_contacts(organization, data)
        self._save(organization)


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

    def _delete(self, role):
        role.delete()

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


class PesImportCalendars(PesImport):
    endpoint = 'api/calendars/'
    model = Calendar
    foreign_model = ForeignCalendar
    key = 'uuid'

    _deserialize = staticmethod(deserialize_calendar)

    def _save(self, calendar):
        post_save.disconnect(calendar_saved, Calendar)
        calendar.save()
        post_save.connect(calendar_saved, Calendar)

    def _delete(self, calendar):
        post_delete.disconnect(calendar_deleted, Calendar)
        calendar.delete()
        post_delete.connect(calendar_deleted, Calendar)


class PesImportEvents(PesImport):
    endpoint = 'api/events/'
    model = Event
    foreign_model = ForeignEvent
    key = 'uuid'

    _deserialize = staticmethod(deserialize_event)

    def _before_map(self, event, data):
        event.calendar = Calendar.objects.get(uuid=data['calendar'])
        self._save(event)

    def _save(self, event):
        post_save.disconnect(event_saved, Event)
        event.save()
        post_save.connect(event_saved, Event)

    def _delete(self, event):
        post_delete.disconnect(event_deleted, Event)
        event.delete()
        post_delete.connect(event_deleted, Event)


class PesImportExchanges(PesImport):
    endpoint = 'api/exchanges/'
    model = Exchange
    foreign_model = ForeignExchange
    key = 'uuid'

    _deserialize = staticmethod(deserialize_exchange)

    def _save(self, exchange):
        post_save.disconnect(exchange_saved, Exchange)
        exchange.save()
        post_save.connect(exchange_saved, Exchange)

    def _delete(self, exchange):
        post_delete.disconnect(exchange_deleted, Exchange)
        exchange.delete()
        post_delete.connect(exchange_deleted, Exchange)


class PesImportProducts(PesImport):
    endpoint = 'api/products/'
    model = Product
    foreign_model = ForeignProduct
    key = 'uuid'

    _deserialize = staticmethod(deserialize_product)

    def _save(self, product):
        post_save.disconnect(product_saved, Product)
        product.save()
        post_save.connect(product_saved, Product)

    def _delete(self, product):
        post_delete.disconnect(product_deleted, Product)
        product.delete()
        post_delete.connect(product_deleted, Product)


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

    def import_calendar(self):
        handler = PesImportCalendars()
        handler.handle()

    def import_events(self):
        handler = PesImportEvents()
        handler.handle()

    def import_products(self):
        handler = PesImportProducts()
        handler.handle()

    def import_exchanges(self):
        handler = PesImportExchanges()
        handler.handle()

    def handle(self, *args, **options):
        self.translations = {}
        self.import_roles()
        self.import_persons()
        self.import_organizations()
        self.import_calendar()
        self.import_events()
        self.import_products()
        self.import_exchanges()

Command = PesImportCommand
