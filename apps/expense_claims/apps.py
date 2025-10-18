from django.apps import AppConfig


class ExpenseClaimsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.expense_claims"
    label = "expense_claims"  # App label without dots
    verbose_name = "Expense Claims Management"
