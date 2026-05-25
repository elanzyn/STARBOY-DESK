from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, username, nome_completo, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        if not username:
            raise ValueError('O username é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, nome_completo=nome_completo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, nome_completo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('cargo', User.Cargo.SUPER_ADMIN)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa de is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa de is_superuser=True.')
        return self.create_user(email, username, nome_completo, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class Cargo(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
        ADMIN = 'ADMIN', _('Admin')
        USER = 'USER', _('Usuário')

    id = models.BigAutoField(primary_key=True)
    nome_completo = models.CharField(max_length=150)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cargo = models.CharField(max_length=20, choices=Cargo.choices, default=Cargo.USER)
    bio = models.TextField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nome_completo']

    def __str__(self):
        return self.email

    @property
    def first_name(self):
        return self.nome_completo.split(' ')[0] if self.nome_completo else ''

    @property
    def last_name(self):
        return ' '.join(self.nome_completo.split(' ')[1:]) if self.nome_completo and len(self.nome_completo.split(' ')) > 1 else ''

class PasswordResetRequest(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', _('Pendente')
        APROVADO = 'APROVADO', _('Aprovado')
        RECUSADO = 'RECUSADO', _('Recusado')

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='reset_requests')
    token = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    solicitado_em = models.DateTimeField(default=timezone.now)
    aprovado_por = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reset_approved')
    aprovado_em = models.DateTimeField(null=True, blank=True)
    expira_em = models.DateTimeField()

    def __str__(self):
        return f"Reset {self.user.email} - {self.status}"

# Create your models here.
