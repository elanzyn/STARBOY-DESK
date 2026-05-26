from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'category', 'priority', 'requester', 'assignee', 'created_at')
    list_filter = ('status', 'category', 'priority')
    search_fields = ('title', 'description', 'requester__email', 'assignee__email')
