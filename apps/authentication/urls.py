from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.ResetPasswordConfirmTokenView.as_view(), name='reset_password'),
    path('plans/', views.plan_selection_view, name='plan_selection'),
    path('plans/activate/', views.plan_activate_view, name='plan_activate'),
    path('plans/confirm/', views.plan_confirm_view, name='plan_confirm'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
