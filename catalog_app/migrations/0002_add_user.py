from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='productcatalog',
            name='owner',
            field=models.ForeignKey(
                null=True,   # 기존 레코드 호환용 (migrate 후 NOT NULL로 바꿔도 됨)
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='catalogs',
                to=settings.AUTH_USER_MODEL,
                verbose_name='소유자',
            ),
        ),
    ]
