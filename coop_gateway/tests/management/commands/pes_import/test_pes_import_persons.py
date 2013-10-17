# encoding: utf-8

import os

from unittest import TestCase

from shortuuid import uuid

from coop_local.models import Person

from coop_gateway.models import ForeignPerson
from coop_gateway.serializers import serialize_person

from .pes_import_test_case import PesImportTestCase


class TestPesImportPerson(PesImportTestCase, TestCase):

    def test_endpoint_url(self):
        url = os.path.join(self.settings_mock.PES_HOST, 'api/persons/')

        self.command.import_persons()

        self.requests_mock.get.assert_called_with(url)

    def serialized_person(self, **data):
        result = {
            'uuid': uuid(),
            'first_name': uuid(),
            'last_name': uuid(),
            'contacts': [],
            'pref_email': None,
        }
        result.update(data)
        return result

    def test_new_person_is_inserted(self):
        json_person = {
            'uuid': uuid(),
            'first_name': uuid(),
            'last_name': uuid(),
        }
        self.response_mock.json.return_value = [json_person]

        self.command.import_persons()

        Person.objects.get(uuid=json_person['uuid'])

    def test_new_person_is_marked_has_foreign(self):
        json_person = {
            'uuid': uuid(),
            'first_name': uuid(),
            'last_name': uuid(),
        }
        self.response_mock.json.return_value = [json_person]

        self.command.import_persons()

        ForeignPerson.objects.get(uuid=json_person['uuid'])

    def test_new_person_is_not_pushed_back(self):
        json_person = {
            'uuid': uuid(),
            'first_name': uuid(),
            'last_name': uuid(),
        }
        self.response_mock.json.return_value = [json_person]

        self.command.import_persons()

        self.assertEquals(len(self.requests_mock.put.mock_calls), 0)

    def test_already_present_person_is_updated(self):
        person_uuid = uuid()
        json_person = {
            'uuid': person_uuid,
            'first_name': uuid(),
            'last_name': uuid(),
        }
        self.response_mock.json.return_value = [json_person]
        self.command.import_persons()
        self.response_mock.json.return_value[0]['first_name'] = uuid()

        self.command.import_persons()

        person = Person.objects.get(
            uuid=person_uuid
        )

        self.assertEquals(
            person.first_name,
            json_person['first_name']
        )

    def test_owned_person_is_not_modified(self):
        uuid_ = uuid()
        first_name = uuid()
        person = Person(uuid=uuid_, first_name=first_name)
        person.save()
        self.response_mock.json.return_value = [{
            'uuid': uuid_,
            'first_name': uuid(),
            'last_name': uuid(),
        }]

        self.command.import_persons()

        person = Person.objects.get(uuid=uuid_)
        self.assertEquals(
            person.first_name,
            first_name
        )

    def assertImported(self, **data):
        serialized = self.serialized_person(**data)
        self.response_mock.json.return_value = [serialized]

        self.command.import_persons()

        person = Person.objects.get(
            uuid=serialized['uuid']
        )

        self.assertEquals(
            serialize_person(person),
            serialized
        )

    def test_person_first_namehandle(self):
        self.assertImported(
            first_name=uuid()
        )

    def test_person_last_namehandle(self):
        self.assertImported(
            last_name=uuid()
        )

    def test_person_pref_emailhandle(self):
        self.assertImported(
            pref_email=self.create_contact().uuid,
        )

    def test_new_owned_person_contacts_are_created(self):
        self.assertImported(
            contacts=[
                {
                    'uuid': uuid(),
                    'content': uuid()
                },
            ],
        )
