# STARBOY DESK - Instalação e Setup

## 1. Crie o ambiente virtual

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

## 2. Instale as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure o .env

Copie `.env.example` para `.env` e ajuste as variáveis:

```
SECRET_KEY=uma-chave-secreta
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

## 4. Migre o banco de dados

```bash
python manage.py migrate
```

## 5. Crie um superusuário (opcional)

```bash
python manage.py createsuperuser
```

## 6. Instale TailwindCSS (Frontend)

Você pode usar o CDN já incluso, ou instalar localmente para customização:

```bash
# Instale Node.js se não tiver
npm install -g npm
npm install -D tailwindcss
npx tailwindcss init
# Edite tailwind.config.js conforme sua estrutura
# Gere o CSS:
npx tailwindcss -i ./static/css/input.css -o ./static/css/custom.css --watch
```

> O template já funciona com o CDN, mas para produção use build local.

## 7. Rode o servidor

```bash
python manage.py runserver
```

Acesse: http://127.0.0.1:8000/

---

- Estrutura modular pronta para SaaS
- JWT, DRF, segurança, templates premium
- Pronto para evoluir
