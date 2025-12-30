from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import SupplierProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_supplier_profile(sender, instance, created, **kwargs):
    if created and instance.is_supplier:  # nếu bạn có trường này
        SupplierProfile.objects.create(user=instance)
