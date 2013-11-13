from django.db import models

from coop_local.models import (
    Organization,
    Person,
    Role,
)


class ForeignOrganization(models.Model):
    local_object = models.OneToOneField(Organization)


class ForeignPerson(models.Model):
    local_object = models.OneToOneField(Person)


class ForeignRole(models.Model):
    local_object = models.OneToOneField(Role)
