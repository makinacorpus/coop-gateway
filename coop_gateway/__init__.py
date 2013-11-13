from django.db.models.signals import (
    post_save,
    post_delete,
)
from coop_local.models import (
    Organization,
    Person,
)
from .signals import (
    organization_saved,
    organization_deleted,
    person_saved,
    person_deleted,
)


post_save.connect(organization_saved, Organization)
post_delete.connect(organization_deleted, Organization)

post_save.connect(person_saved, Person)
post_delete.connect(person_deleted, Person)
