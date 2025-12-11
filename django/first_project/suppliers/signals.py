from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import SupplierProfile

User = settings.AUTH_USER_MODEL

# post_save signal for User: if user belongs to group 'supplier', auto-create SupplierProfile
from django.contrib.auth import get_user_model
UserModel = get_user_model()

@receiver(post_save, sender=UserModel)
def create_supplier_profile_for_group(sender, instance, created, **kwargs):
    """
    If a user is in group 'supplier' and does not yet have a SupplierProfile,
    create a default SupplierProfile automatically.
    This allows admin to just add a user to the supplier group and the profile appears.
    """
    try:
        supplier_group = Group.objects.get(name='supplier')
    except Group.DoesNotExist:
        return

    if supplier_group in instance.groups.all():
        # create profile if missing
        if not hasattr(instance, 'supplier_profile'):
            SupplierProfile.objects.create(
                user=instance,
                company_name=instance.get_full_name() or instance.username,
                contact_email=instance.email or '',
            )