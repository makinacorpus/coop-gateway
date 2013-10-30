import json
import os
import requests

from django.conf import settings

from coop_gateway.serializers import (
    serialize_organization,
    serialize_person,
)


def endpoint_url(endpoint):
    url = os.path.join(settings.PES_HOST, 'api', endpoint)
    return '%s?api_key=%s' % (url, settings.PES_API_KEY)


def push_data(endpoint, data):
    requests.put(endpoint_url(endpoint), data=json.dumps(data))


def organization_saved(sender, instance, **kwargs):
    push_data('organizations/%s/' % instance.uuid,
              serialize_organization(instance))


def person_saved(sender, instance, **kwargs):
    push_data('persons/%s/' % instance.uuid,
              serialize_person(instance))
