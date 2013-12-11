# encoding: utf-8

import json
import os
import sys
from time import time

import dateutil
import requests
import shortuuid

from django.conf import settings
from django.core import serializers

from coop.exchange.models import (
    EWAY,
    ETYPE,
)

from coop_local.models import (
    Contact,
    Engagement,
    Organization,
    Role,
)
from coop_local.models.local_models import STATUTS

organization_default_fields = [
    'uuid',
    'title',
    'description',
    'acronym',
    'testimony',
    'annual_revenue',
    'workforce',
    'statut',
    'birth',
    'web',
    'contacts',
    'members',
    'pref_phone',
    'pref_email',
]

person_default_fields = [
    'uuid',
    'first_name',
    'last_name',
    'contacts',
    'pref_email',
]


def serialize(obj, include):
    fields = json.loads(serializers.serialize('json', [obj]))[0]['fields']
    result = {
        'uuid': fields['uuid']
    }

    for name in include:
        if name in fields:
            result[name] = fields[name]

    return result


_roles = []
_roles_last_update = time()


def get_pes_roles_by_slug():
    global _roles, _roles_last_update

    if (time() - _roles_last_update) > 120:
        url = os.path.join(settings.PES_HOST, 'api/roles/')
        sys.stdout.write('GET %s ' % url)

        response = requests.get(url)
        response.raise_for_status()
        _roles = dict([
            (role['slug'], role['uuid'])
            for role in response.json()
        ])
        _roles_last_update = time()

    return _roles


_legal_statuses = []
_legal_statuses_last_update = time()


def get_pes_legal_statuses():
    global _legal_statuses, _legal_statuses_last_update

    if (time() - _legal_statuses_last_update) > 120:
        url = os.path.join(settings.PES_HOST, 'api/legal_statuses/')
        sys.stdout.write('GET %s\n' % url)

        response = requests.get(url)
        response.raise_for_status()
        _legal_statuses = response.json()
        _legal_statuses_last_update = time()

    return _legal_statuses


def get_pes_legal_statuses_by_label():
    return dict([
        (role['label'], role['slug'])
        for role in get_pes_legal_statuses()
    ])


def get_pes_legal_statuses_by_slug():
    return dict([
        (role['slug'], role['label'])
        for role in get_pes_legal_statuses()
    ])


def translate_role_uuid(role_uuid):
    pes_roles_by_slug = get_pes_roles_by_slug()
    local_roles_by_uuid = dict([
        (role.uuid, role.slug)
        for role in Role.objects.all()
    ])
    return pes_roles_by_slug[local_roles_by_uuid[role_uuid]]


def status_slug(status):
    legal_statuses_by_label = get_pes_legal_statuses_by_label()
    return legal_statuses_by_label.get(STATUTS.CHOICES_DICT[status])


def serialize_contact(contact):
    return {
        'contact_medium': contact.contact_medium_id,
        'uuid': contact.uuid,
        'content': contact.content,
    }


def serialize_contacts(queryset):
    return [
        serialize_contact(contact)
        for contact in queryset.all()
    ]


def serialize_location(location):
    result = serialize(location, (
        'uuid',
        'label',
        'adr1',
        'adr2',
        'zipcode',
        'city',
        'country'))
    return result


def serialize_members(queryset):
    return [
        {
            'person': engagement.person.uuid,
            'role': translate_role_uuid(engagement.role.uuid),
            'role_detail': engagement.role_detail,
        }
        for engagement in queryset.all()
    ]


def serialize_organization(organization, include=organization_default_fields):
    result = serialize(organization, include)

    if 'contacts' in include:
        result['contacts'] = serialize_contacts(organization.contacts)

    if 'members' in include:
        engagements = Engagement.objects.filter(organization=organization)
        result['members'] = serialize_members(engagements)

    if 'pref_phone' in include and organization.pref_phone:
        result['pref_phone'] = organization.pref_phone.uuid

    if 'pref_email' in include and organization.pref_email:
        result['pref_email'] = organization.pref_email.uuid

    if 'statut' in include and organization.statut:
        result['legal_status'] = status_slug(organization.statut)

    return result


def serialize_person(person, include=person_default_fields):
    result = serialize(person, include)

    if 'contacts' in include:
        result['contacts'] = serialize_contacts(person.contacts)

    if 'pref_email' in include and person.pref_email:
        result['pref_email'] = person.pref_email.uuid

    return result


def serialize_calendar(event):
    return serialize(event, ('uuid', 'title', 'description'))


def serialize_event(event):
    result = serialize(event, (
        'uuid',
        'title',
        'description',
        'other_organizations',
        'source_info'))

    result['calendar'] = event.calendar.uuid
    result['organization'] = getattr(event.organization, 'uuid', None)
    result['organizations'] = [
        organization.uuid
        for organization in event.organizations.all()
    ]
    result['occurrences'] = [
        serialize(occurrence, ('start_time', 'end_time'))
        for occurrence in event.occurrence_set.all()
    ]

    return result


def serialize_product(product):
    result = serialize(product, (
        'uuid',
        'title',
        'description'))
    result['organization'] = getattr(product.organization, 'uuid', None)
    return result


def serialize_exchange(exchange):
    result = serialize(exchange, (
        'uuid',
        'title',
        'permanent',
        'expiration',
        'description'))
    result['person'] = getattr(exchange.person, 'uuid', None)
    result['products'] = [
        product.uuid
        for product in exchange.products.all()
    ]
    result['methods'] = [
        method.id
        for method in exchange.methods.all()
    ]
    result['eway'] = EWAY.REVERTED_CHOICES_CONST_DICT[int(exchange.eway)]
    result['etype'] = ETYPE.REVERTED_CHOICES_CONST_DICT[exchange.etype]
    return result


def setattr_from(obj, attr, data, default=None, parse=lambda x: x):
    if attr in data:
        value = parse(data[attr])
        setattr(obj, attr, value)
    else:
        setattr(obj, attr, default)


def parse_date(value):
    if value is None:
        return
    return dateutil.parser.parse(value)


def get_legal_status(slug):
    try:
        legal_statuses_by_slug = get_pes_legal_statuses_by_slug()
        return STATUTS.REVERTED_CHOICES_DICT[legal_statuses_by_slug[slug]]
    except Exception:
        return 0


def get_contact(uuid):
    try:
        return Contact.objects.get(uuid=uuid)
    except Exception:
        return None


def deserialize_location(location, data):
    location.uuid = data['uuid']
    location.title = data['label']

    setattr_from(location, 'adr1', data)
    setattr_from(location, 'adr2', data)
    setattr_from(location, 'zipcode', data)
    setattr_from(location, 'city', data)
    setattr_from(location, 'country', data)


def deserialize_organization(organization, data):
    organization.uuid = data['uuid']
    organization.title = data['title']

    setattr_from(organization, 'description', data)
    setattr_from(organization, 'acronym', data)
    setattr_from(organization, 'annual_revenue', data)
    setattr_from(organization, 'birth', data, parse=parse_date)
    setattr_from(organization, 'pref_email', data, parse=get_contact)
    setattr_from(organization, 'pref_phone', data, parse=get_contact)
    setattr_from(organization, 'testimony', data, '')
    setattr_from(organization, 'web', data)
    setattr_from(organization, 'workforce', data)

    organization.statut = get_legal_status(data.get('legal_status'))


def deserialize_person(person, data):
    person.uuid = data['uuid']
    person.first_name = data['first_name']
    person.last_name = data['last_name']
    setattr_from(person, 'pref_email', data, parse=get_contact)

    person.username = shortuuid.uuid()


def deserialize_contact(content_object, contact, data):
    contact.contact_medium_id = data['contact_medium']
    contact.uuid = data['uuid']
    contact.content = data['content']
    contact.content_object = content_object


def deserialize_role(role, data):
    role.uuid = data['uuid']
    role.label = data['label']


def get_organization(uuid):
    try:
        return Organization.objects.get(uuid=uuid)
    except Exception:
        return None


def get_organizations(uuids):
    try:
        return [
            organization
            for organization in Organization.filter(uuid__in=uuids).all()
        ]
    except Exception:
        return []


def deserialize_calendar(calendar, data):
    calendar.uuid = data['uuid']
    calendar.title = data['title']
    setattr_from(calendar, 'description', data)


def deserialize_event(event, data):
    event.uuid = data['uuid']
    event.title = data['title']
    setattr_from(event, 'description', data)
    setattr_from(event, 'other_organizations', data)
    setattr_from(event, 'source_info', data)
    setattr_from(event, 'organization', data, parse=get_organization)
    setattr_from(event, 'organizations', data, parse=get_organizations)


def deserialize_exchange(exchange, data):
    exchange.uuid = data['uuid']
    exchange.title = data['title']
    exchange.title = data['permanent']
    exchange.eway = EWAY.CHOICES_CONST_DICT[data['eway']]
    exchange.etype = ETYPE.CHOICES_CONST_DICT[data['etype']]

    setattr_from(exchange, 'expiration', data, parse=parse_date)
    setattr_from(exchange, 'description', data)


def deserialize_product(product, data):
    product.uuid = data['uuid']
    product.first_name = data['title']

    setattr_from(product, 'description', data)
    setattr_from(product, 'organization', data, parse=get_organization)
