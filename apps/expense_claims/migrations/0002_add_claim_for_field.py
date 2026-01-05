# Generated migration for adding claim_for field

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('expense_claims', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE claims_expenseclaim
                ADD COLUMN claim_for_id INTEGER NULL
                REFERENCES accounts_user(id) DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="ALTER TABLE claims_expenseclaim DROP COLUMN claim_for_id;",
        ),
    ]
