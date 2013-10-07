import json
import os
from unittest import TestCase

from shortuuid import uuid

from coop_local.models import (
    Organization,
)

from coop_gateway.serializers import serialize_organization
from .mock_test_case import MockTestCase


class TestPushOrganization(MockTestCase, TestCase):

    def setUp(self):
        self.requests_mock = self.patch('coop_gateway.signals.requests')
        self.settings_mock = self.patch('coop_gateway.signals.settings')

    def test_organization_is_pushed_to_pes_when_saved(self):
        organization = Organization(title=uuid())
        self.settings_mock.PES_HOST = 'http://localhost'
        push_url = os.path.join(self.settings_mock.PES_HOST, 'api/')

        organization.save()

        serialized = serialize_organization(organization)
        self.requests_mock.put.assert_called_with(
            push_url,
            content=json.dumps(serialized))
