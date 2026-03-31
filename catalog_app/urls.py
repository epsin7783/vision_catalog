from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # 인증 (페이지)
    path('login/',        views.login_view,   name='login'),
    path('signup/',       views.signup_view,  name='signup'),
    path('logout/',       views.logout_view,  name='logout'),
    # 인증 (AJAX — 폼 제출 가로채기용)
    path('auth/login/',   views.login_ajax,   name='login_ajax'),
    path('auth/signup/',  views.signup_ajax,  name='signup_ajax'),

    # 메인 대시보드 (로그인 필요)
    path('', views.index, name='index'),

    # 카탈로그 생성 (로그인 필요)
    path('create/', views.create_catalog, name='create'),

    # 카탈로그 결과 페이지 (공개 — 링크 공유용)
    path('catalog/<uuid:pk>/', views.catalog_view, name='view'),

    # 바이어 문의 (AJAX)
    path('catalog/<uuid:pk>/inquire/', views.submit_inquiry, name='inquire'),
]
