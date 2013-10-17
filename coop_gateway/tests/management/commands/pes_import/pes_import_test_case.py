# encoding: utf-8

from shortuuid import uuid
from mock import MagicMock

from coop_local.models import (
    Contact,
    Organization,
)

from coop_gateway.management.commands import PesImportCommand

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

        self.command = PesImportCommand()

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
