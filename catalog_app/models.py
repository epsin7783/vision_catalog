from django.db import models
from django.contrib.auth.models import User
import uuid


class BuyerInquiry(models.Model):
    """바이어가 카탈로그에서 남기는 문의"""

    catalog      = models.ForeignKey('ProductCatalog', on_delete=models.CASCADE,
                                     related_name='inquiries', verbose_name='카탈로그')
    buyer_name   = models.CharField(max_length=100, verbose_name='문의자 이름')
    buyer_email  = models.EmailField(verbose_name='이메일')
    buyer_phone  = models.CharField(max_length=30, blank=True, verbose_name='연락처')
    message      = models.TextField(verbose_name='문의 내용')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '바이어 문의'

    def __str__(self):
        return f"{self.buyer_name} → {self.catalog.product_name}"


class ProductCatalog(models.Model):
    """B2B 제품 카탈로그 — 입력 폼 한 건당 한 레코드"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── 제품 정보 (폼 입력) ────────────────────────────────────────
    product_name  = models.CharField(max_length=200, verbose_name='제품명')
    short_intro   = models.CharField(max_length=300, verbose_name='한 줄 소개')
    specs         = models.TextField(blank=True, verbose_name='제품 스펙')

    # ── 회사/연락처 정보 ───────────────────────────────────────────
    company_name  = models.CharField(max_length=200, verbose_name='회사명')
    contact_email = models.EmailField(blank=True, verbose_name='문의 이메일')
    contact_phone = models.CharField(max_length=30, blank=True, verbose_name='문의 전화')

    # ── 소유자 ────────────────────────────────────────────────────
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='catalogs', verbose_name='소유자')

    # ── 이미지 ────────────────────────────────────────────────────
    original_image  = models.ImageField(upload_to='uploads/',   verbose_name='원본 이미지')
    processed_image = models.ImageField(upload_to='processed/', blank=True, null=True,
                                        verbose_name='배경제거 이미지')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'B2B 제품 카탈로그'

    def __str__(self):
        return f"[{self.company_name}] {self.product_name}"

    def get_spec_rows(self):
        """
        스펙 텍스트(키: 값 형식)를 파싱해 (key, value) 튜플 리스트로 반환.
        템플릿의 스펙 테이블 렌더링에 사용.
        예시 입력:
            크기: 100 x 50 x 30 mm
            무게: 250g
        """
        rows = []
        for line in self.specs.splitlines():
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                key, _, val = line.partition(':')
                rows.append((key.strip(), val.strip()))
            else:
                rows.append(('', line))
        return rows
