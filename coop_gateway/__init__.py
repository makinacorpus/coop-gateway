from django.db.models.signals import post_save
from coop_local.models import Organization
from .signals import organization_saved


post_save.connect(organization_saved, Organization)
