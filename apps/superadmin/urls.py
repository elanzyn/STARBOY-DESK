from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users, name='users'),
    path('users/<int:user_id>/toggle/', views.toggle_user, name='toggle_user'),
    path('users/<int:user_id>/promote-superadmin/', views.promote_user_superadmin, name='promote_superadmin'),
    path('users/<int:user_id>/request-password-reset/', views.request_user_password_reset, name='request_password_reset'),
    path('logs/', views.logs, name='logs'),
    path('password-resets/', views.password_resets, name='password_resets'),
]
