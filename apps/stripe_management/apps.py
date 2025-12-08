from django.apps import AppConfig


class StripeManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stripe_management"
    verbose_name = "Stripe Management"
