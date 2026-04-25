from django.contrib import admin
from .models import (
    UserProfile, Item, Message, ContactMessage, BugReport,
    NewsletterSubscription, Order, OrderItem, Review, Notification,
    Cart, CartItem, Payment, ChatMessage
)

admin.site.register(UserProfile)
admin.site.register(Item)
admin.site.register(Message)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(ChatMessage)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'is_resolved')
    list_filter = ('subject', 'is_resolved')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('submitted_at',)

@admin.register(BugReport)
class BugReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'bug_type', 'severity', 'submitted_at', 'is_resolved')
    list_filter = ('bug_type', 'severity', 'is_resolved')
    search_fields = ('name', 'email', 'description')
    readonly_fields = ('submitted_at',)

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)

