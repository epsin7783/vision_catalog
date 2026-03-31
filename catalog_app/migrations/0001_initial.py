from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ProductCatalog',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product_name',    models.CharField(max_length=200, verbose_name='제품명')),
                ('short_intro',     models.CharField(max_length=300, verbose_name='한 줄 소개')),
                ('specs',           models.TextField(blank=True, verbose_name='제품 스펙')),
                ('company_name',    models.CharField(max_length=200, verbose_name='회사명')),
                ('contact_email',   models.EmailField(blank=True, verbose_name='문의 이메일')),
                ('contact_phone',   models.CharField(blank=True, max_length=30, verbose_name='문의 전화')),
                ('original_image',  models.ImageField(upload_to='uploads/', verbose_name='원본 이미지')),
                ('processed_image', models.ImageField(blank=True, null=True, upload_to='processed/', verbose_name='배경제거 이미지')),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'B2B 제품 카탈로그', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='BuyerInquiry',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buyer_name',  models.CharField(max_length=100, verbose_name='문의자 이름')),
                ('buyer_email', models.EmailField(verbose_name='이메일')),
                ('buyer_phone', models.CharField(blank=True, max_length=30, verbose_name='연락처')),
                ('message',     models.TextField(verbose_name='문의 내용')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('catalog',     models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                  related_name='inquiries',
                                                  to='catalog_app.productcatalog',
                                                  verbose_name='카탈로그')),
            ],
            options={'verbose_name': '바이어 문의', 'ordering': ['-created_at']},
        ),
    ]
