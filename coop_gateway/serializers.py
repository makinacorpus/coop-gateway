import json
import os
import sys
from datetime import datetime

import dateutil
import requests
import shortuuid

from django.conf import settings
from django.core import serializers

from coop_local.models import Engagement
from coop_local.models import (
    Contact,
    LegalStatus,
    Role,
)

organization_default_fields = [
    'uuid',
    'title',
    'acronym',
    'testimony',
    'annual_revenue',
    'workforce',
    'legal_status',
    'birth',
    'web',
    'contacts',
    'transverse_themes',
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


def memcache(seconds):

    def decorator(func):
        timestamp = None
        cache = None

        def wrapper():
            if timestamp is None or timestamp - datetime.now() > seconds:
                cache = func()
            return cache

        return wrapper

    return decorator


@memcache(3600)
def get_pes_roles_by_slug():
    url = os.path.join(settings.PES_HOST, 'api/roles/')
    sys.stdout.write('GET %s\n' % url)
    response = requests.get(url)
    response.raise_for_status()
    return dict([
        (role['slug'], role['uuid'])
        for role in response.json()
    ])


def translate_role_uuid(role_uuid):
    pes_roles_by_slug = get_pes_roles_by_slug()
    local_roles_by_uuid = dict([
        (role.uuid, role.slug)
        for role in Role.objects.all()
    ])
    return pes_roles_by_slug[local_roles_by_uuid[role_uuid]]


def serialize_organization(organization, include=organization_default_fields):
    result = serialize(organization, include)
    if 'contacts' in include:
        result['contacts'] = [
            {
                'uuid': contact.uuid,
                'content': contact.content,
            }
            for contact in organization.contacts.all()
        ]

    if 'transverse_themes' in include:
        result['transverse_themes'] = [
            theme.pk
            for theme in organization.transverse_themes.all()
        ]

    if 'members' in include:
        result['members'] = [
            {
                'person': engagement.person.uuid,
                'role': translate_role_uuid(engagement.role.uuid),
            }
            for engagement in Engagement.objects.filter(
                organization=organization
            ).all()
        ]

    if 'pref_phone' in include and organization.pref_phone:
        result['pref_phone'] = organization.pref_phone.uuid

    if 'pref_email' in include and organization.pref_email:
        result['pref_email'] = organization.pref_email.uuid

    if 'legal_status' in include and organization.legal_status:
        result['legal_status'] = organization.legal_status.slug

    return result


def serialize_person(person, include=person_default_fields):
    result = serialize(person, include)

    if 'contacts' in include:
        result['contacts'] = [
            {
                'uuid': contact.uuid,
                'content': contact.content,
            }
            for contact in person.contacts.all()
        ]

    if 'pref_email' in include and person.pref_email:
        result['pref_email'] = person.pref_email.uuid

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
        return LegalStatus.objects.get(slug=slug)
    except Exception:
        return None


def get_contact(uuid):
    try:
        return Contact.objects.get(uuid=uuid)
    except Exception:
        return None


def deserialize_organization(organization, data):
    organization.uuid = data['uuid']
    organization.title = data['title']

    setattr_from(organization, 'acronym', data)
    setattr_from(organization, 'annual_revenue', data)
    setattr_from(organization, 'birth', data,
                 parse=parse_date)
    setattr_from(organization, 'legal_status', data,
                 parse=get_legal_status)
    setattr_from(organization, 'pref_email', data,
                 parse=get_contact)
    setattr_from(organization, 'pref_phone', data,
                 parse=get_contact)
    setattr_from(organization, 'testimony', data, '')
    setattr_from(organization, 'web', data)
    setattr_from(organization, 'workforce', data)


def deserialize_person(person, data):
    person.uuid = data['uuid']
    person.first_name = data['first_name']
    person.last_name = data['last_name']
    setattr_from(person, 'pref_email', data, parse=get_contact)

    person.username = shortuuid.uuid()


def deserialize_contact(content_object, contact, data):
    contact.uuid = data['uuid']
    contact.content = data['content']
    contact.content_object = content_object


def deserialize_role(role, data):
    role.uuid = data['uuid']
    role.label = data['label']
