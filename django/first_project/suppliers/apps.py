from django.apps import AppConfig

class SuppliersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'suppliers'

    def ready(self):
        # import signals so they are registered
        try:
            import suppliers.signals  # noqa: F401
        except Exception:
            # avoid breaking if signals import fails during migrations
            pass