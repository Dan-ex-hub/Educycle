from django.urls import path, include
from . import views
from . import payment_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('profile/', views.profile, name='profile'),
    path('items/', views.item_list, name='item_list'),
    path('items/<int:item_id>/', views.item_detail, name='item_detail'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:item_id>/delete/', views.item_delete, name='item_delete'),
    path('items/<int:item_id>/message/', views.send_message, name='send_message'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('remove-all-items/', views.remove_all_items, name='remove_all_items'),
    
    # Cart functionality
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:cart_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Payment endpoints
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('payment/create-intent/<int:order_id>/', payment_views.create_payment_intent, name='create_payment_intent'),
    path('payment/create-razorpay-order/<int:order_id>/', payment_views.create_razorpay_order, name='create_razorpay_order'),
    path('payment/process-cod/<int:order_id>/', payment_views.process_cod_payment, name='process_cod_payment'),
    path('payment/webhook/stripe/', payment_views.stripe_webhook, name='stripe_webhook'),
    path('payment/webhook/razorpay/', payment_views.razorpay_webhook, name='razorpay_webhook'),
    path('payment/history/', payment_views.payment_history, name='payment_history'),
    path('payment/refund/<int:payment_id>/', payment_views.refund_payment, name='refund_payment'),
    
    # API endpoints
    path('api/', include('hub.api_urls')),
    
    # Support pages
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('report-bug/', views.report_bug, name='report_bug'),
    path('help/', views.help_center, name='help_center'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('safety/', views.safety_guidelines, name='safety_guidelines'),
    
    # Review System
    path('item/<int:item_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Chatbot
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/history/<str:session_id>/', views.get_chat_history, name='get_chat_history'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # Newsletter subscription
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

    # Custom Admin Panel
    path('panel/', views.admin_panel, name='admin_panel'),
]