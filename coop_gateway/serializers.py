import json

from django.core import serializers
from coop_local.models import Engagement

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
