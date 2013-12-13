# encoding: utf-8

import sys

from django.core.management.base import BaseCommand

from coop_local.models import (
    Calendar,
    Event,
    Exchange,
    Location,
    Organization,
    Person,
    Product,
)

from ...signals import (
    calendar_saved,
    event_saved,
    exchange_saved,
    location_saved,
    organization_saved,
    person_saved,
    product_saved,
)


class Command(BaseCommand):
    help = 'Exports data to the PES'
    handlers = (
        (Location, location_saved),
        (Person, person_saved),
        (Organization, organization_saved),
        (Calendar, calendar_saved),
        (Event, event_saved),
        (Product, product_saved),
        (Exchange, exchange_saved),
    )

    def handle(self, *args, **options):

        for model, instance_saved in self.handlers:
            for instance in model.objects.filter(foreign_model=None).all():
                try:
                    instance_saved(None, instance)
                except Exception as e:
                    sys.stderr.write('%s\n%s\n' % (type(e).__name__, e))
