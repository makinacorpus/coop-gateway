import json

import dateutil

from django.core import serializers

from coop_local.models import Engagement
from coop_local.models import (
    Contact,
    LegalStatus,
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
                'role': engagement.role.uuid,
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


def deserialize_contact(content_object, contact, data):
    contact.uuid = data['uuid']
    contact.content = data['content']
    contact.content_object = content_object
