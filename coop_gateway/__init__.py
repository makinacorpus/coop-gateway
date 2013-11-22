from django.db.models.signals import (
    post_save,
    post_delete,
)
from coop_local.models import (
    Organization,
    Person,
    Calendar,
    Event,
)
from .signals import (
    organization_saved,
    organization_deleted,
    person_saved,
    person_deleted,
    calendar_saved,
    calendar_deleted,
    event_saved,
    event_deleted,
)


post_save.connect(organization_saved, Organization)
post_delete.connect(organization_deleted, Organization)

post_save.connect(person_saved, Person)
post_delete.connect(person_deleted, Person)

post_save.connect(calendar_saved, Calendar)
post_delete.connect(calendar_deleted, Calendar)

post_save.connect(event_saved, Event)
post_delete.connect(event_deleted, Event)
