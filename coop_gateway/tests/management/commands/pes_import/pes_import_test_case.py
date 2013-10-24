# encoding: utf-8

import os

from shortuuid import uuid
from mock import MagicMock

from django.core.exceptions import ObjectDoesNotExist

from coop_local.models import (
    Contact,
    Organization,
)

from coop_gateway.tests.mock_test_case import MockTestCase


class PesImportTestCase(MockTestCase):

    def setUp(self):
        self.requests_mock = self.patch(
            'coop_gateway.management.commands.pes_import.requests'
        )
        self.settings_mock = self.patch(
            'coop_gateway.management.commands.pes_import.settings'
        )

        self.patch('coop_gateway.signals.requests', self.requests_mock)
        self.patch('coop_gateway.signals.settings', self.settings_mock)

        self.response_mock = MagicMock()
        self.requests_mock.get.return_value = self.response_mock

        self.settings_mock.PES_HOST = 'http://localhost'
        self.settings_mock.PES_API_KEY = uuid()

        self.handler = self.handler_class()

    def create_contact(self):
        organization = Organization(uuid=uuid(), title=uuid())
        organization.save()

        contact = Contact(
            uuid=uuid(),
            content=uuid(),
            content_object=organization
        )
        contact.save()

        return contact

    def assertObjectDoesNotExist(self, model, **kwargs):
        with self.assertRaises(ObjectDoesNotExist):
            model.objects.get(**kwargs)

    def assertObjectDoesExist(self, model, **kwargs):
        model.objects.get(**kwargs)

    def test_endpoint_url(self):
        url = os.path.join(self.settings_mock.PES_HOST, self.endpoint)

        self.handler.handle()

        self.requests_mock.get.assert_called_with(url)
