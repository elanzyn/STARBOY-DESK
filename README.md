STARBOY DESK
=============

Tecnologias
----------
- Python 3.14
- Django 5.0.6
- SQLite (desenvolvimento)
- Tailwind CSS + Alpine.js (frontend)
- Chart.js (gráficos)
- Django REST Framework (APIs)

Instalação / Clonar em outra máquina
-----------------------------------
1. Clonar
   git clone <URL_DO_REPO>
   cd <repo>

2. Criar e ativar ambiente virtual
   python -m venv venv
   venv\Scripts\activate     # Windows
   source venv/bin/activate  # Linux / macOS

3. Instalar dependências
   pip install -r requirements.txt

4. Configurar variáveis de ambiente (opcionais/produção)
   - SECRET_KEY
   - DEBUG (True/False)
   - ALLOWED_HOSTS
   - DATABASE_* (se migrar para PostgreSQL)

5. Aplicar migrações e criar superuser
   python manage.py migrate
   python manage.py createsuperuser

6. Executar servidor de desenvolvimento
   python manage.py runserver

Observações rápidas
-------------------
- A flag de recurso TICKETS_ENABLE_REQUESTER_CLOSE está em core/settings.py (atualmente DESATIVADA). Altere se desejar reativar.
- Este repositório já contém scripts JS estáticos em /static/ — execute collectstatic em ambiente de produção.
- Para produção use PostgreSQL + Gunicorn/ASGI e Nginx para servir estáticos.

