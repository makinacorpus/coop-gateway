import json
import os
import requests

from django.conf import settings

from coop_local.models import (
    Person,
    Calendar,
    Organization,
)

from coop_gateway.serializers import (
    serialize_organization,
    serialize_person,
    serialize_product,
    serialize_exchange,
    serialize_calendar,
    serialize_event,
)


def endpoint_url(endpoint):
    url = os.path.join(settings.PES_HOST, 'api', endpoint)
    return '%s?api_key=%s' % (url, settings.PES_API_KEY)


def push_data(endpoint, data):
    print('PUT %s\n%s' % (endpoint_url(endpoint), data))
    requests.put(endpoint_url(endpoint), data=json.dumps(data))


def delete_data(endpoint):
    requests.delete(endpoint_url(endpoint))


def organization_saved(sender, instance, **kwargs):
    data = serialize_organization(instance)

    #Ensure person exists on the pes
    for member in data['members']:
        person = Person.objects.get(uuid=member['person'])
        person_saved(None, person)

    push_data('organizations/%s/' % instance.uuid, data)


def organization_deleted(sender, instance, **kwargs):
    delete_data('organizations/%s/' % instance.uuid)


def person_saved(sender, instance, **kwargs):
    push_data('persons/%s/' % instance.uuid,
              serialize_person(instance))


def person_deleted(sender, instance, **kwargs):
    delete_data('persons/%s/' % instance.uuid)


def product_saved(sender, instance, **kwargs):
    push_data('products/%s/' % instance.uuid,
              serialize_product(instance))


def product_deleted(sender, instance, **kwargs):
    delete_data('products/%s/' % instance.uuid)


def exchange_saved(sender, instance, **kwargs):

    #Ensure organization exist on the pes
    if instance.organization:
        organization_saved(None, instance.organization)

    #Ensure person exist on the pes
    if instance.person:
        person_saved(None, instance.person)

    #Ensure products exist on the pes
    for product in instance.products:
        product_saved(None, product)

    push_data('exchanges/%s/' % instance.uuid,
              serialize_exchange(instance))


def exchange_deleted(sender, instance, **kwargs):
    delete_data('exchanges/%s/' % instance.uuid)


def calendar_saved(sender, instance, **kwargs):
    push_data('calendars/%s/' % instance.uuid, serialize_calendar(instance))


def calendar_deleted(sender, instance, **kwargs):
    delete_data('calendars/%s/' % instance.uuid)


def event_saved(sender, instance, **kwargs):
    data = serialize_event(instance)

    #Ensure calendar exists on the pes
    calendar = Calendar.objects.get(uuid=data['calendar'])
    calendar_saved(None, calendar)

    #Ensure organizations exists on the pes
    organization = Organization.objects.get(uuid=data['organization'])
    organization_saved(None, organization)

    for organization_uuid in data['organizations']:
        organization = Organization.objects.get(uuid=organization_uuid)
        organization_saved(None, organization)

    push_data('events/%s/' % instance.uuid, data)


def event_deleted(sender, instance, **kwargs):
    delete_data('events/%s/' % instance.uuid)
