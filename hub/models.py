from django.db import models
from django.contrib.auth.models import User

# UserProfile to extend User with student_id
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=50, choices=[
        ('computer_science', 'Computer Science'),
        ('engineering', 'Engineering'),
        ('arts', 'Arts & Design'),
        ('business', 'Business'),
        ('science', 'Science'),
        ('medicine', 'Medicine'),
        ('law', 'Law'),
        ('education', 'Education'),
        ('other', 'Other')
    ], default='other', blank=True)
    year_of_study = models.CharField(max_length=20, choices=[
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4', '4th Year'),
        ('5', '5th Year'),
        ('graduate', 'Graduate'),
        ('phd', 'PhD')
    ], default='1', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.student_id})"

# Item model for listings
class Item(models.Model):
    CATEGORY_CHOICES = [
        ('textbook', 'Textbook'),
        ('equipment', 'Lab Equipment'),
        ('decor', 'Room Decor'),
        ('appliance', 'Mini-Fridge/Appliance'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    desired_swap_item = models.CharField(max_length=100, null=True, blank=True)
    image1 = models.ImageField(upload_to='item_images/', null=True, blank=True)
    image2 = models.ImageField(upload_to='item_images/', null=True, blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

# Message model for internal messaging
class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} about {self.item.name}"

# Cart model for shopping cart functionality
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.cartitem_set.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())

# CartItem model for individual items in cart
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.item.name} in {self.cart.user.username}'s cart"

    def get_total_price(self):
        return self.item.price * self.quantity if self.item.price else 0

# Order model for completed purchases
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='sold_orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.username}"

# OrderItem model for individual items in orders
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.item.name} in Order {self.order.id}"

    def get_total_price(self):
        return self.price_at_time * self.quantity

# Payment model for Stripe integration
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.order.id} - {self.status}"
    
    def get_amount_display(self):
        return f"{self.currency} {self.amount}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('item_added', 'Item Added'),
        ('item_sold', 'Item Sold'),
        ('item_purchased', 'Item Purchased'),
        ('review_received', 'Review Received'),
        ('message_received', 'Message Received'),
        ('order_status', 'Order Status Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    related_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=255)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['item', 'user']  # One review per user per item
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.item.name} - {self.rating} stars"
    
    def get_star_display(self):
        """Return HTML for star display"""
        stars = '★' * self.rating + '☆' * (5 - self.rating)
        return stars

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('bot', 'Bot Response'),
    ]
    
    session_id = models.CharField(max_length=100)  # To group conversation
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.session_id} - {self.message_type} - {self.timestamp}"


class ContactMessage(models.Model):
    """Stores contact form submissions"""
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('bug', 'Report a Bug'),
        ('feature', 'Feature Request'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} — {self.get_subject_display()} ({self.submitted_at.strftime('%d %b %Y')})"


class BugReport(models.Model):
    """Stores bug report submissions"""
    BUG_TYPE_CHOICES = [
        ('ui', 'UI Issue'),
        ('functionality', 'Functionality Problem'),
        ('performance', 'Performance Issue'),
        ('security', 'Security Concern'),
        ('payment', 'Payment Bug'),
        ('search', 'Search Issue'),
        ('mobile', 'Mobile Responsiveness'),
        ('other', 'Other'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bug_type = models.CharField(max_length=20, choices=BUG_TYPE_CHOICES, default='other')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField()
    steps = models.TextField(blank=True)
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.get_bug_type_display()} — {self.name}"


class NewsletterSubscription(models.Model):
    """Stores newsletter / notification subscription emails"""
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return f"{self.email} ({'active' if self.is_active else 'inactive'})"
