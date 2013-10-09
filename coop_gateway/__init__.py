from django.db.models.signals import post_save
from coop_local.models import (
    Organization,
    Person,
)
from .signals import (
    organization_saved,
    person_saved,
)


post_save.connect(organization_saved, Organization)
post_save.connect(person_saved, Person)
