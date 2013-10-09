import json
import os
import requests

from django.conf import settings

from coop_gateway.serializers import (
    serialize_organization,
    serialize_person,
)


def push_data(endpoint, data):
    url = os.path.join(settings.PES_HOST, 'api', endpoint)
    requests.put(url, data=json.dumps(data))


def organization_saved(sender, instance, **kwargs):
    push_data('organizations/', serialize_organization(instance))


def person_saved(sender, instance, **kwargs):
    push_data('persons/', serialize_person(instance))
