from __future__ import annotations

import json
import logging
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import BuyerInquiry, ProductCatalog
from .services import remove_background

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
MAX_FILE_SIZE = 20 * 1024 * 1024


# ─────────────────────────────────────────────────────────────────────────────
# 인증 뷰
# ─────────────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        return render(request, 'catalog_app/login.html', {
            'error': '아이디 또는 비밀번호가 올바르지 않습니다.',
            'username': username,
        })

    return render(request, 'catalog_app/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:index')

    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not password1:
            return render(request, 'catalog_app/signup.html',
                          {'error': '아이디와 비밀번호를 입력해 주세요.', 'username': username, 'email': email})
        if password1 != password2:
            return render(request, 'catalog_app/signup.html',
                          {'error': '비밀번호가 일치하지 않습니다.', 'username': username, 'email': email})
        if len(password1) < 8:
            return render(request, 'catalog_app/signup.html',
                          {'error': '비밀번호는 8자 이상이어야 합니다.', 'username': username, 'email': email})
        if User.objects.filter(username=username).exists():
            return render(request, 'catalog_app/signup.html',
                          {'error': '이미 사용 중인 아이디입니다.', 'username': username, 'email': email})

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect('catalog:index')

    return render(request, 'catalog_app/signup.html')


def logout_view(request):
    logout(request)
    return redirect('catalog:login')


@csrf_exempt
@require_http_methods(['POST'])
def login_ajax(request):
    """폼 제출 가로채기용 AJAX 로그인 — 성공 시 세션 쿠키 세팅"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return JsonResponse({'success': True, 'username': user.username})
    return JsonResponse({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}, status=401)


@csrf_exempt
@require_http_methods(['POST'])
def signup_ajax(request):
    """폼 제출 가로채기용 AJAX 회원가입"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

    username  = data.get('username', '').strip()
    email     = data.get('email', '').strip()
    password1 = data.get('password1', '')
    password2 = data.get('password2', '')

    if not username or not password1:
        return JsonResponse({'error': '아이디와 비밀번호를 입력해 주세요.'}, status=400)
    if password1 != password2:
        return JsonResponse({'error': '비밀번호가 일치하지 않습니다.'}, status=400)
    if len(password1) < 8:
        return JsonResponse({'error': '비밀번호는 8자 이상이어야 합니다.'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': '이미 사용 중인 아이디입니다.'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password1)
    login(request, user)
    return JsonResponse({'success': True, 'username': user.username})


# ─────────────────────────────────────────────────────────────────────────────
# 대시보드 (내 카탈로그 목록)
# ─────────────────────────────────────────────────────────────────────────────

def index(request):
    my_catalogs = (
        ProductCatalog.objects.filter(owner=request.user)
        if request.user.is_authenticated else []
    )
    return render(request, 'catalog_app/index.html', {'my_catalogs': my_catalogs})


# ─────────────────────────────────────────────────────────────────────────────
# 카탈로그 생성
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(['POST'])
def create_catalog(request):
    required_fields = ('product_name', 'company_name', 'short_intro')
    missing = [f for f in required_fields if not request.POST.get(f, '').strip()]
    if missing:
        my_catalogs = ProductCatalog.objects.filter(owner=request.user)
        return render(request, 'catalog_app/index.html', {
            'error': f"필수 항목을 입력해 주세요: {', '.join(missing)}",
            'form_data': request.POST,
            'my_catalogs': my_catalogs,
        })

    if 'image' not in request.FILES:
        my_catalogs = ProductCatalog.objects.filter(owner=request.user)
        return render(request, 'catalog_app/index.html', {
            'error': '제품 이미지를 첨부해 주세요.',
            'form_data': request.POST,
            'my_catalogs': my_catalogs,
        })

    uploaded = request.FILES['image']
    ext = Path(uploaded.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        my_catalogs = ProductCatalog.objects.filter(owner=request.user)
        return render(request, 'catalog_app/index.html', {
            'error': f'지원하지 않는 이미지 형식입니다. ({", ".join(ALLOWED_EXTENSIONS)})',
            'form_data': request.POST,
            'my_catalogs': my_catalogs,
        })
    if uploaded.size > MAX_FILE_SIZE:
        my_catalogs = ProductCatalog.objects.filter(owner=request.user)
        return render(request, 'catalog_app/index.html', {
            'error': '파일 크기가 20MB를 초과합니다.',
            'form_data': request.POST,
            'my_catalogs': my_catalogs,
        })

    catalog = ProductCatalog(
        owner         = request.user,
        product_name  = request.POST['product_name'].strip(),
        short_intro   = request.POST['short_intro'].strip(),
        specs         = request.POST.get('specs', '').strip(),
        company_name  = request.POST['company_name'].strip(),
        contact_email = request.POST.get('contact_email', '').strip(),
        contact_phone = request.POST.get('contact_phone', '').strip(),
        original_image = uploaded,
    )
    catalog.save()

    original_abs = Path(settings.MEDIA_ROOT) / catalog.original_image.name
    try:
        processed_bytes = remove_background(original_abs)
        processed_rel = f"processed/{catalog.id}.png"
        processed_abs = Path(settings.MEDIA_ROOT) / processed_rel
        processed_abs.parent.mkdir(parents=True, exist_ok=True)
        processed_abs.write_bytes(processed_bytes)
        catalog.processed_image = processed_rel
        catalog.save(update_fields=['processed_image'])
    except Exception as exc:
        logger.warning(f"[BG Remove] 실패 (원본 사용): {exc}")

    return redirect('catalog:view', pk=catalog.id)


# ─────────────────────────────────────────────────────────────────────────────
# 카탈로그 결과 페이지 (공개)
# ─────────────────────────────────────────────────────────────────────────────

def catalog_view(request, pk):
    catalog = get_object_or_404(ProductCatalog, pk=pk)
    spec_rows = catalog.get_spec_rows()
    catalog_url = request.build_absolute_uri()
    inquiry_count = catalog.inquiries.count()
    is_owner = request.user.is_authenticated and catalog.owner == request.user

    return render(request, 'catalog_app/catalog_view.html', {
        'catalog': catalog,
        'spec_rows': spec_rows,
        'catalog_url': catalog_url,
        'inquiry_count': inquiry_count,
        'is_owner': is_owner,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 바이어 문의 (AJAX)
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def submit_inquiry(request, pk):
    catalog = get_object_or_404(ProductCatalog, pk=pk)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)

    buyer_name  = data.get('buyer_name', '').strip()
    buyer_email = data.get('buyer_email', '').strip()
    message     = data.get('message', '').strip()

    if not all([buyer_name, buyer_email, message]):
        return JsonResponse({'error': '이름, 이메일, 문의 내용은 필수입니다.'}, status=400)

    BuyerInquiry.objects.create(
        catalog=catalog, buyer_name=buyer_name,
        buyer_email=buyer_email,
        buyer_phone=data.get('buyer_phone', '').strip(),
        message=message,
    )

    return JsonResponse({
        'success': True,
        'message': f"문의가 접수되었습니다. {catalog.contact_email or '담당자'}가 곧 연락드립니다.",
    })
