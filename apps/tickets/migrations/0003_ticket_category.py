from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_ticketstatuslog'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='category',
            field=models.CharField(choices=[('SUPPORT', 'Suporte técnico'), ('ACCESS', 'Acesso e contas'), ('SOFTWARE', 'Software'), ('HARDWARE', 'Hardware'), ('NETWORK', 'Rede'), ('INFRA', 'Infraestrutura'), ('ADMIN', 'Administrativo'), ('FINANCE', 'Financeiro'), ('MAINTENANCE', 'Manutenção'), ('OTHER', 'Outros')], default='SUPPORT', max_length=20),
        ),
    ]
