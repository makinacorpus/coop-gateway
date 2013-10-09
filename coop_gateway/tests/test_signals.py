import json
import os
from unittest import TestCase

from shortuuid import uuid

from coop_local.models import (
    Organization,
    Person,
)

from coop_gateway.serializers import (
    serialize_organization,
    serialize_person,
)
from .mock_test_case import MockTestCase


class TestSignals(MockTestCase, TestCase):

    def setUp(self):
        self.requests_mock = self.patch('coop_gateway.signals.requests')
        self.settings_mock = self.patch('coop_gateway.signals.settings')
        self.settings_mock.PES_HOST = 'http://localhost'

    def assertPushed(self, endpoint, data):
        url = os.path.join(self.settings_mock.PES_HOST, 'api', endpoint)
        self.requests_mock.put.assert_called_with(url,
                                                  data=json.dumps(data))

    def test_organization_is_pushed_to_pes_when_saved(self):
        organization = Organization(title=uuid())

        organization.save()

        self.assertPushed('organizations/',
                          serialize_organization(organization))

    def test_person_is_pushed_to_pes_when_saved(self):
        person = Person(first_name=uuid(), last_name=uuid())

        person.save()

        self.assertPushed('persons/',
                          serialize_person(person))
