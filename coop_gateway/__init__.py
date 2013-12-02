from django.db.models.signals import (
    post_save,
    post_delete,
)
from coop_local.models import (
    Calendar,
    Event,
    Exchange,
    Organization,
    Person,
    Product,
)
from .signals import (
    calendar_deleted,
    calendar_saved,
    event_deleted,
    event_saved,
    exchange_deleted,
    exchange_saved,
    organization_deleted,
    organization_saved,
    person_deleted,
    person_saved,
    product_deleted,
    product_saved,
)


post_save.connect(organization_saved, Organization)
post_delete.connect(organization_deleted, Organization)

post_save.connect(person_saved, Person)
post_delete.connect(person_deleted, Person)

post_save.connect(calendar_saved, Calendar)
post_delete.connect(calendar_deleted, Calendar)

post_save.connect(event_saved, Event)
post_delete.connect(event_deleted, Event)

post_save.connect(product_saved, Product)
post_delete.connect(product_deleted, Product)

post_save.connect(exchange_saved, Exchange)
post_delete.connect(exchange_deleted, Exchange)
