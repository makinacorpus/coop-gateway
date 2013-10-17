from django.db import models


class ForeignOrganization(models.Model):
    uuid = models.CharField(max_length=255, unique=True)


class ForeignPerson(models.Model):
    uuid = models.CharField(max_length=255, unique=True)
