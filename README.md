# EduCycle — Campus Marketplace

A full-stack student marketplace platform built with **Django 5.2** and **Tailwind CSS**. EduCycle enables students to buy, sell, and swap second-hand textbooks, lab equipment, appliances, and room décor within their campus community.

**🌐 Live Demo:** [https://educycle-six.vercel.app/](https://educycle-six.vercel.app/)

---

## Overview

EduCycle provides a secure, intuitive marketplace designed specifically for student communities. The platform streamlines the process of buying and selling used items through integrated payment processing, real-time messaging, and comprehensive order management.

---

## Features

| Category | Details |
|---|---|
| **Authentication** | Student ID registration, secure login/logout, session management, password recovery |
| **Item Listings** | Create, edit, and delete listings with image uploads, category organization, pricing, and swap options |
| **Search & Discovery** | Full-text search, category filtering, and live autocomplete suggestions |
| **Shopping Cart** | Add items to cart, streamlined checkout, and order history tracking |
| **Payment Processing** | Stripe (card payments), Razorpay (UPI/wallets), and Cash on Delivery |
| **Messaging System** | Direct messaging between buyers and sellers for negotiations and inquiries |
| **Reviews & Ratings** | Star-based rating system with detailed comments on purchased items |
| **Notifications** | Real-time in-app alerts for sales, messages, reviews, and order status updates |
| **AI Assistant** | Intelligent keyword-based chatbot with admin escalation for unresolved queries |
| **Personalization** | Dark/light/system theme support, notification preferences, privacy controls |
| **Support** | Contact form, bug reporting, comprehensive safety guidelines and policies |
| **Administration** | Django admin panel with contact message and bug report management |

---

## Technology Stack

- **Backend:** Django 5.2, Django REST Framework 3.14
- **Database:** SQLite 3 (development), PostgreSQL (production-ready)
- **Frontend:** Tailwind CSS, Font Awesome Icons, Inter Typography
- **Payment Gateways:** Stripe, Razorpay
- **Image Processing:** Pillow
- **Authentication:** Django Sessions, Django REST Framework SimpleJWT

---

## Local Development

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Installation & Setup

```bash
# Clone the repository
git clone https://github.com/Dan-ex-hub/Educycle.git
cd Educycle

# Install dependencies
pip install -r requirements.txt
pip install Pillow stripe

# Apply database migrations
python manage.py migrate

# Create superuser account for admin access
python manage.py createsuperuser

# (Optional) Load sample product data
python manage.py add_sample_items

# Start development server
python manage.py runserver
```

Access the application at **http://127.0.0.1:8000**

Admin panel available at **http://127.0.0.1:8000/admin/**

---

## Project Structure

```
Educycle/
├── EduCycle/                  # Django project configuration
│   ├── settings.py            # Project settings and configuration
│   └── urls.py                # URL routing
├── hub/                        # Main application module
│   ├── models.py               # Database models (Item, Order, Payment, Review, etc.)
│   ├── views.py                # View functions and logic
│   ├── urls.py                 # App-level URL routing
│   ├── forms.py                # Django forms (registration, login, listings)
│   ├── chatbot.py              # AI assistant implementation
│   ├── services.py             # Business logic (notifications, etc.)
│   ├── payment_views.py        # Stripe & Razorpay payment handlers
│   ├── api_views.py            # REST API endpoints
│   └── templates/hub/          # HTML templates with Tailwind CSS
├── media/                      # User-uploaded item images
├── db.sqlite3                  # SQLite database
├── requirements.txt            # Python dependencies
└── manage.py                   # Django management script
```

---

## Environment Configuration

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key (keep secure) | `your-secret-key-here` |
| `DEBUG` | Debug mode (disable in production) | `False` |
| `ALLOWED_HOSTS` | Permitted domain names | `educycle-six.vercel.app` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | `pk_test_...` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` |
| `RAZORPAY_KEY_ID` | Razorpay key ID | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key | `...` |

---

## Application Routes

| Route | Purpose |
|---|---|
| `/` | Home page and item listings |
| `/register/` | Student registration |
| `/login/` | User authentication |
| `/items/create/` | Create new listing |
| `/items/<id>/` | Item detail page |
| `/cart/` | Shopping cart |
| `/checkout/` | Purchase checkout |
| `/orders/` | Order history and tracking |
| `/profile/` | User profile and seller dashboard |
| `/settings/` | Account settings and preferences |
| `/chatbot/` | AI assistant interface |
| `/notifications/` | Notification center |
| `/contact/` | Contact support form |
| `/report-bug/` | Bug report submission |
| `/privacy/` | Privacy Policy |
| `/terms/` | Terms of Service |
| `/how-it-works/` | Platform guide |
| `/safety/` | Safety guidelines |
| `/admin/` | Administrative dashboard |
| `/api/` | REST API endpoints |

---

## Testing

Run the test suite to validate functionality:

```bash
python manage.py test hub
```

---

## License

MIT License — This project is open source and available for modification and distribution.

---

**EduCycle — Connecting Students, Reducing Waste**
