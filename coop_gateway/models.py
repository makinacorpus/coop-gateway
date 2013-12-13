from django.db import models
from django.db.models.loading import get_model


class ForeignOrganization(models.Model):
    local_object = models.OneToOneField(
        get_model('coop_local', 'Organization'),
        related_name='foreign_model'
    )


class ForeignPerson(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Person'),
                                        related_name='foreign_model')


class ForeignRole(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Role'),
                                        related_name='foreign_model')


class ForeignCalendar(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Calendar'),
                                        related_name='foreign_model')


class ForeignEvent(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Event'),
                                        related_name='foreign_model')


class ForeignProduct(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Product'),
                                        related_name='foreign_model')


class ForeignExchange(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Exchange'),
                                        related_name='foreign_model')


class ForeignLocation(models.Model):
    local_object = models.OneToOneField(get_model('coop_local', 'Location'),
                                        related_name='foreign_model')
