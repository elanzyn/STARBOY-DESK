from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetRequest
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informações Pessoais'), {'fields': ('nome_completo', 'username', 'bio', 'telefone', 'cargo')}),
        (_('Permissões'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Datas'), {'fields': ('criado_em', 'atualizado_em')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'nome_completo', 'password1', 'password2', 'cargo', 'is_staff', 'is_superuser', 'is_active'),
        }),
    )
    
    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Ativo</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Inativo</span>')
    status_display.short_description = 'Status'
    
    def activate_users(modeladmin, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Ativar usuários selecionados"
    
    def deactivate_users(modeladmin, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Desativar usuários selecionados"
    
    list_display = ('email', 'nome_completo', 'cargo', 'status_display', 'is_staff', 'criado_em')
    list_filter = ('cargo', 'is_active', 'is_staff', 'is_superuser', 'criado_em')
    search_fields = ('email', 'nome_completo', 'username')
    ordering = ('-criado_em',)
    readonly_fields = ('criado_em', 'atualizado_em')
    actions = [activate_users, deactivate_users]

@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'solicitado_em', 'aprovado_por', 'aprovado_em', 'expira_em')
    list_filter = ('status',)
    search_fields = ('user__email',)

# Register your models here.
