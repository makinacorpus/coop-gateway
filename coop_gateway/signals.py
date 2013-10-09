import json
import os
import requests

from django.conf import settings

from .serializers import serialize_organization


def organization_saved(sender, instance, **kwargs):
    content = serialize_organization(instance)
    requests.put(os.path.join(settings.PES_HOST, 'api/'),
                 data=json.dumps(content))
