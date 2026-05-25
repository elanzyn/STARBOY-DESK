from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.ticket_list, name='list'),
    path('create/', views.ticket_create, name='create'),
    path('<int:pk>/', views.ticket_detail, name='detail'),
    path('<int:pk>/status/', views.ticket_change_status, name='change_status'),
    path('<int:pk>/assign_self/', views.ticket_assign_self, name='assign_self'),
    path('<int:pk>/confirm_resolution/', views.ticket_confirm_resolution, name='confirm_resolution'),
    path('<int:pk>/logs/', views.ticket_logs, name='logs'),
]
