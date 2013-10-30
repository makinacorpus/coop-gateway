from django.db import models

from coop_local.models import (
    Organization,
    Person,
    Role,
)


class ForeignOrganization(models.Model):
    local_object = models.ForeignKey(Organization, unique=True)


class ForeignPerson(models.Model):
    local_object = models.ForeignKey(Person, unique=True)


class ForeignRole(models.Model):
    local_object = models.ForeignKey(Role, unique=True)
