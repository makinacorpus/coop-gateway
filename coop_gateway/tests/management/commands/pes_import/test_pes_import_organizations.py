# encoding: utf-8

from unittest import TestCase
from datetime import datetime

from shortuuid import uuid

from coop_local.models import (
    LegalStatus,
    Organization,
    Role,
    Person,
)

from coop_gateway.management.commands.pes_import import PesImportOrganisations
from coop_gateway.models import ForeignOrganization
from coop_gateway.serializers import serialize_organization

from .pes_import_test_case import PesImportTestCase


class TestPesImportOrganization(PesImportTestCase, TestCase):
    endpoint = 'api/organizations/'
    handler_class = PesImportOrganisations

    def serialized_organization(self, **data):
        result = {
            'uuid': uuid(),
            'title': uuid(),
            'acronym': None,
            'annual_revenue': None,
            'birth': None,
            'contacts': [],
            'legal_status': None,
            'members': [],
            'pref_email': None,
            'pref_phone': None,
            'testimony': '',
            'transverse_themes': [],
            'web': None,
            'workforce': None
        }
        result.update(data)
        return result

    def test_new_organization_is_inserted(self):
        json_organization = {
            'uuid': uuid(),
            'title': uuid()
        }
        self.response_mock.json.return_value = [json_organization]

        self.handler.handle()

        Organization.objects.get(uuid=json_organization['uuid'])

    def test_new_organization_is_marked_has_foreign(self):
        json_organization = {
            'uuid': uuid(),
            'title': uuid()
        }
        self.response_mock.json.return_value = [json_organization]

        self.handler.handle()

        ForeignOrganization.objects.get(uuid=json_organization['uuid'])

    def test_new_organization_is_not_pushed_back(self):
        json_organization = {
            'uuid': uuid(),
            'title': uuid()
        }
        self.response_mock.json.return_value = [json_organization]

        self.handler.handle()

        self.assertEquals(len(self.requests_mock.put.mock_calls), 0)

    def test_already_present_organization_is_updated(self):
        organization_uuid = uuid()
        json_organization = {
            'uuid': organization_uuid,
            'title': uuid()
        }
        self.response_mock.json.return_value = [json_organization]
        self.handler.handle()
        self.response_mock.json.return_value[0]['title'] = uuid()

        self.handler.handle()

        organization = Organization.objects.get(
            uuid=organization_uuid
        )

        self.assertEquals(
            organization.title,
            json_organization['title']
        )

    def test_owned_organization_is_not_modified(self):
        uuid_ = uuid()
        title = uuid()
        organization = Organization(uuid=uuid_, title=title)
        organization.save()
        self.response_mock.json.return_value = [{
            'uuid': uuid_,
            'title': uuid()
        }]

        self.handler.handle()

        organization = Organization.objects.get(uuid=uuid_)
        self.assertEquals(
            organization.title,
            title
        )

    def assertImported(self, **data):
        serialized = self.serialized_organization(**data)
        self.response_mock.json.return_value = [serialized]

        self.handler.handle()

        organization = Organization.objects.get(
            uuid=serialized['uuid']
        )

        self.assertEquals(
            serialize_organization(organization),
            serialized
        )

    def test_organization_acronymhandle(self):
        self.assertImported(
            acronym=uuid()
        )

    def test_organization_annual_revenuehandle(self):
        self.assertImported(
            annual_revenue=42
        )

    def test_organization_annual_birthhandle(self):
        self.assertImported(
            birth=datetime.now().date().isoformat(),
        )

    def test_organization_legal_statushandle(self):
        legal_status = LegalStatus(label=uuid())
        legal_status.save()
        self.assertImported(
            legal_status=legal_status.slug,
        )

    def test_organization_pref_email_and_phonehandle(self):
        self.assertImported(
            pref_email=self.create_contact().uuid,
            pref_phone=self.create_contact().uuid,
        )

    def test_organization_testimonyhandle(self):
        self.assertImported(
            testimony=uuid()
        )

    def test_organization_webhandle(self):
        self.assertImported(
            web=uuid()
        )

    def test_organization_workforcehandle(self):
        self.assertImported(
            workforce='4.2'
        )

    def test_new_owned_organization_contacts_are_created(self):
        self.assertImported(
            contacts=[
                {
                    'uuid': uuid(),
                    'content': uuid()
                },
            ],
        )

    def test_member_with_translated_roles_import(self):
        person = Person(uuid=uuid(), first_name=uuid())
        person.save()
        json_role = {
            'uuid': uuid(),
            'lablel': uuid(),
        }
        json_organization = {
            'uuid': uuid(),
            'title': uuid(),
            'members': [
                {
                    'role': json_role['uuid'],
                    'person': person.uuid,
                }
            ]
        }
        self.response_mock.json.return_value = [json_organization]
        role = Role(uuid=uuid(), label=uuid())
        role.save()

        self.handler.role_translations = {
            json_role['uuid']: role.uuid
        }

        self.handler.handle()
