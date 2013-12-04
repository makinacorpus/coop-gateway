from django.db import models
from django.db.models.loading import get_model


class ForeignOrganization(models.Model):
    local_object = models.OneToOneField(get_model('coop_local',
                                                  'Organization'))


class ForeignPerson(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Person'))


class ForeignRole(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Role'))


class ForeignCalendar(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Calendar'))


class ForeignEvent(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Event'))


class ForeignProduct(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Product'))


class ForeignExchange(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Exchange'))
