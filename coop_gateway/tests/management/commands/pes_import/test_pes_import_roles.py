# encoding: utf-8

from unittest import TestCase

from shortuuid import uuid

from coop_gateway.management.commands.pes_import import PesImportRoles

from coop_local.models import Role

from coop_gateway.models import ForeignRole

from .pes_import_test_case import PesImportTestCase


class TestPesImportRole(PesImportTestCase, TestCase):
    endpoint = 'api/roles/'
    handler_class = PesImportRoles

    def test_not_imported_if_matching_slug(self):
        role = Role(
            uuid=uuid(),
            label=uuid(),
        )
        role.save()
        serialized = {
            'uuid': uuid(),
            'label': role.label,
            'slug': role.slug,
        }
        self.response_mock.json.return_value = [serialized]

        self.handler.handle()

        self.assertObjectDoesNotExist(Role, uuid=serialized['uuid'])

    def test_imported_if_missing(self):
        serialized = {
            'uuid': uuid(),
            'label': uuid(),
            'slug': uuid(),
        }
        serialized['slug'] = serialized['label']
        self.response_mock.json.return_value = [serialized]

        self.handler.handle()

        self.assertObjectDoesExist(Role, uuid=serialized['uuid'])

    def test_marked_has_foreign_if_imported(self):
        serialized = {
            'uuid': uuid(),
            'label': uuid(),
            'slug': uuid(),
        }
        self.response_mock.json.return_value = [serialized]

        self.handler.handle()

        self.assertObjectDoesExist(ForeignRole, slug=serialized['slug'])
