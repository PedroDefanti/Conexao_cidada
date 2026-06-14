# 🤝 Conexão Cidadã

> Site de conexão entre **voluntários** e **ONGs**, desenvolvido em Django com design dark moderno e segurança de front-end e back-end.

---

## 📋 Pré-requisitos

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **pip** — já vem com o Python
- *(opcional)* **Git** — para clonar o repositório

Verifique se está tudo certo:
```bash
python --version
pip --version
```

---

## 🚀 Instalação e execução

### 1. Clone ou extraia o projeto
```bash
# Se tiver Git:
git clone https://github.com/seu-usuario/conexao-cidada.git
cd conexao-cidada

# Ou descompacte o .zip e entre na pasta:
cd conexao_cidada
```

### 2. Crie e ative o ambiente virtual
```bash
# Criar o ambiente
python -m venv venv

# Ativar — Windows:
venv\Scripts\activate

# Ativar — Linux / macOS:
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Aplique as migrações (cria o banco de dados)
```bash
python manage.py migrate
```

### 5. Crie um superusuário (admin)
```bash
python manage.py createsuperuser
```
> Informe e-mail e senha quando solicitado. Esse usuário acessa `/admin/`.

### 6. (Opcional) Popule o banco com dados de exemplo
```bash
python manage.py shell -c "
from core.models import Categoria, ONG
Categoria.objects.get_or_create(nome='Educação', slug='educacao')
Categoria.objects.get_or_create(nome='Meio Ambiente', slug='meio-ambiente')
print('Categorias criadas!')
"
```

### 7. Inicie o servidor de desenvolvimento
```bash
python manage.py runserver
```

Acesse no navegador: **http://127.0.0.1:8000**

---

## 🗂️ Páginas do site

| URL | Descrição |
|-----|-----------|
| `/` | Home — grid de ONGs, busca e filtros por categoria |
| `/login/` | Login com e-mail e senha |
| `/cadastro/` | Cadastro (abas: Voluntário ou ONG) |
| `/perfil/` | Painel do usuário — inscrições e status |
| `/inscricao/<id>/` | Formulário de inscrição em uma ONG |
| `/admin/` | Painel administrativo do Django |

---

## 🛠️ Comandos úteis do dia a dia

```bash
# Iniciar o servidor
python manage.py runserver

# Criar migrações após alterar models.py
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Abrir o shell interativo do Django
python manage.py shell

# Coletar arquivos estáticos (necessário em produção)
python manage.py collectstatic

# Rodar os testes
python manage.py test

# Ver todas as URLs do projeto
python manage.py show_urls 2>/dev/null || python manage.py shell -c "
from django.urls import get_resolver
for key in get_resolver().url_patterns: print(key)
"
```

---

## 🔒 Segurança implementada

### Back-end
| Proteção | Detalhe |
|----------|---------|
| **CSRF** | Token obrigatório em todos os formulários POST |
| **Rate Limiting** | Login: 10 tentativas/min · Cadastro: 5/5 min |
| **Sanitização XSS** | Entradas limpas com `bleach` antes de salvar |
| **Senhas seguras** | Mínimo 8 chars, não comuns, não similares ao nome |
| **`@login_required`** | Rotas `/perfil/` e `/inscricao/` protegidas |
| **`require_http_methods`** | Cada view aceita apenas os métodos HTTP corretos |
| **`never_cache`** | Páginas autenticadas não ficam em cache |
| **Logging** | Tentativas de login suspeitas registradas em `logs/django.log` |

### Headers HTTP
| Header | Valor |
|--------|-------|
| `Content-Security-Policy` | Bloqueia scripts/estilos externos não autorizados |
| `X-Frame-Options` | `DENY` — impede clickjacking |
| `X-Content-Type-Options` | `nosniff` — impede MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Bloqueia câmera, microfone e geolocalização |

### Sessão e Cookies
| Configuração | Valor |
|--------------|-------|
| `SESSION_COOKIE_HTTPONLY` | `True` — cookie inacessível via JavaScript |
| `SESSION_COOKIE_SAMESITE` | `Lax` — proteção contra CSRF cross-site |
| `SESSION_COOKIE_AGE` | `3600` — sessão expira em 1 hora |
| `CSRF_COOKIE_HTTPONLY` | `True` |

---

## 🗃️ Estrutura do projeto

```
conexao_cidada/
├── conexao_cidada/        # Configurações do projeto
│   ├── settings.py        # Todas as configs + segurança
│   └── urls.py            # Roteamento principal
├── core/                  # App principal
│   ├── models.py          # Usuario, ONG, Categoria, Inscricao
│   ├── views.py           # Lógica das páginas
│   ├── forms.py           # Formulários com validação
│   ├── middleware.py      # Rate limiting + headers de segurança
│   └── admin.py           # Painel administrativo
├── templates/core/        # Templates HTML
│   ├── base.html          # Layout base (nav + footer)
│   ├── index.html         # Home
│   ├── login.html         # Login
│   ├── cadastro.html      # Cadastro
│   ├── inscricao.html     # Inscrição em ONG
│   └── perfil.html        # Perfil do usuário
├── static/css/
│   └── style.css          # Estilos globais (design dark)
├── requirements.txt       # Dependências Python
├── .env.example           # Variáveis de ambiente de exemplo
└── manage.py              # CLI do Django
```

---

## ⚙️ Variáveis de ambiente (produção)

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

```env
DJANGO_SECRET_KEY=sua-chave-secreta-forte-aqui
DJANGO_DEBUG=False
ALLOWED_HOSTS=seudominio.com www.seudominio.com
```

> ⚠️ **Nunca** suba o arquivo `.env` para o repositório. Adicione-o ao `.gitignore`.

---

## 📦 Dependências (`requirements.txt`)

| Pacote | Finalidade |
|--------|------------|
| `Django` | Framework web principal |
| `bleach` | Sanitização de inputs — remove HTML/JS malicioso |
| `Pillow` | Suporte a imagens (uploads futuros) |

---

*Projeto acadêmico — Práticas Extensionistas*
