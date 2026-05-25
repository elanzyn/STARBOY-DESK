from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.home, name='home'),
    path('export/csv/', views.export_dashboard_csv, name='export_csv'),
]
