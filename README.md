# 🎓 EduCycle — Campus Marketplace

A full-stack student marketplace built with **Django 5.2** and **Tailwind CSS**. Students can buy, sell, and swap second-hand textbooks, lab equipment, appliances, and room decor within their campus community.

---

## ✨ Features

| Area | What's included |
|---|---|
| **Auth** | Register with student ID, login/logout, session management, password change |
| **Listings** | Create, edit, delete items with photos, category, price, swap option |
| **Search** | Full-text search, category filter, live autocomplete suggestions |
| **Cart & Orders** | Add to cart, checkout, order tracking for buyers and sellers |
| **Payments** | Stripe (card), Razorpay (UPI/wallets), Cash on Delivery |
| **Messaging** | Direct messages between buyers and sellers |
| **Reviews** | Star ratings and comments on items |
| **Notifications** | In-app alerts for sales, messages, reviews, order updates |
| **AI Assistant** | Keyword-based chatbot with typewriter effect and admin escalation |
| **Settings** | Profile, password, notification prefs, privacy, dark/light/system theme |
| **Dark Mode** | Full dark mode across every page, persisted in localStorage |
| **Support Pages** | Contact Us, Report a Bug (saved to DB), Privacy Policy, Terms, Safety, How It Works |
| **Admin** | Django admin with ContactMessage and BugReport management |

---

## 🛠 Tech Stack

- **Backend:** Django 5.2, Django REST Framework 3.14
- **Database:** SQLite 3 (development) — see deployment section for production
- **Frontend:** Tailwind CSS (CDN), Font Awesome, Inter font
- **Payments:** Stripe, Razorpay (mock fallback if not installed)
- **Images:** Pillow, real product photos from Unsplash
- **Auth:** Django sessions + `djangorestframework-simplejwt` for API

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- pip

### Steps

```bash
# 1. Clone
git clone <your-repo-url>
cd Educycle

# 2. Install dependencies
pip install -r requirements.txt
pip install Pillow stripe

# 3. Apply migrations
python manage.py migrate

# 4. Create a superuser (for admin panel)
python manage.py createsuperuser

# 5. (Optional) Load sample products
python manage.py add_sample_items

# 6. Start the dev server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

Admin panel: **http://127.0.0.1:8000/admin/**

---

## 📁 Project Structure

```
Educycle/
├── EduCycle/               # Django project settings
│   ├── settings.py
│   └── urls.py
├── hub/                    # Main app
│   ├── models.py           # Item, Order, Payment, Review, Notification, ContactMessage, BugReport …
│   ├── views.py            # All view functions
│   ├── urls.py             # URL routing
│   ├── forms.py            # Registration, login, item forms
│   ├── chatbot.py          # Keyword-based AI assistant
│   ├── services.py         # NotificationService
│   ├── payment_views.py    # Stripe + Razorpay handlers
│   ├── api_views.py        # DRF API endpoints
│   └── templates/hub/      # All HTML templates (Tailwind CSS)
├── media/                  # Uploaded item images
├── db.sqlite3              # SQLite database
├── requirements.txt
└── manage.py
```

---

## 🌐 Deployment Guide

### Option 1 — Railway (Recommended, free tier available)

Railway supports SQLite for small projects and is the easiest zero-config deployment.

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set these environment variables in Railway dashboard:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
```

---

### Option 2 — Render (Free tier, SQLite supported)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set:
   - **Build command:** `pip install -r requirements.txt && python manage.py migrate`
   - **Start command:** `gunicorn EduCycle.wsgi:application`
5. Add environment variables:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app.onrender.com
   ```

> **Note on SQLite on Render:** Render's free tier uses an ephemeral filesystem — the SQLite file resets on each deploy. For persistent data, use Render's free PostgreSQL add-on (see Option 4).

---

### Option 3 — VPS / DigitalOcean Droplet

```bash
# On your server (Ubuntu 22.04)
sudo apt update && sudo apt install python3-pip python3-venv nginx

# Clone and set up
git clone <your-repo> /var/www/educycle
cd /var/www/educycle
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# Configure settings for production
export SECRET_KEY="your-secret-key"
export DEBUG=False
export ALLOWED_HOSTS="your-domain.com"

python manage.py migrate
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn EduCycle.wsgi:application --bind 0.0.0.0:8000 --workers 3 --daemon

# Nginx config: /etc/nginx/sites-available/educycle
server {
    listen 80;
    server_name your-domain.com;

    location /static/ { alias /var/www/educycle/staticfiles/; }
    location /media/  { alias /var/www/educycle/media/; }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### Option 4 — Switching from SQLite to PostgreSQL (Production)

SQLite is fine for development and low-traffic deployments. For production with multiple users, switch to PostgreSQL:

```bash
pip install psycopg2-binary
```

In `settings.py`, replace the `DATABASES` block:

```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:password@localhost:5432/educycle'
    )
}
```

Then:
```bash
python manage.py migrate
python manage.py createsuperuser
```

Free PostgreSQL options:
- **Render** — free 90-day PostgreSQL instance
- **Supabase** — free tier with 500MB
- **Railway** — free tier with PostgreSQL plugin
- **Neon** — serverless PostgreSQL, generous free tier

---

### Production Checklist

Before going live, update `settings.py`:

```python
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')   # Never hardcode in production
ALLOWED_HOSTS = ['your-domain.com']

# Serve static files with WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # Add this
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# HTTPS settings (once you have SSL)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Run:
```bash
python manage.py collectstatic
```

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | Hardcoded (change for production!) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `[]` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | Test placeholder |
| `STRIPE_SECRET_KEY` | Stripe secret key | Test placeholder |
| `RAZORPAY_KEY_ID` | Razorpay key ID | Test placeholder |
| `RAZORPAY_KEY_SECRET` | Razorpay secret | Test placeholder |

---

## 📋 Key URLs

| URL | Description |
|---|---|
| `/` | Homepage / item listing |
| `/register/` | Student registration |
| `/login/` | Login |
| `/items/create/` | List an item for sale |
| `/items/<id>/` | Item detail page |
| `/cart/` | Shopping cart |
| `/checkout/` | Checkout |
| `/orders/` | Order history |
| `/profile/` | User profile & listings |
| `/settings/` | Account settings + dark mode |
| `/chatbot/` | AI assistant |
| `/notifications/` | Notification centre |
| `/contact/` | Contact Us |
| `/report-bug/` | Report a Bug |
| `/privacy/` | Privacy Policy |
| `/terms/` | Terms of Service |
| `/how-it-works/` | How It Works |
| `/safety/` | Safety Guidelines |
| `/admin/` | Django admin panel |
| `/api/` | REST API endpoints |

---

## 🧪 Running Tests

```bash
python manage.py test hub
```

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

**Built with ❤️ for students, by students.**
