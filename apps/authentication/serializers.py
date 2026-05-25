from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nome_completo', 'username', 'email', 'avatar', 'cargo', 'bio', 'telefone', 'is_active', 'is_staff', 'is_superuser', 'criado_em', 'atualizado_em')

class LoginJWTSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Credenciais inválidas.')
