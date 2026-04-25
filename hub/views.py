from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, ItemForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Item, Message, Cart, CartItem, Order, OrderItem, Notification, Review, ChatMessage, ContactMessage, BugReport, NewsletterSubscription
from django.contrib.auth.models import User
from django.db.models import Q
from django.conf import settings
from .services import NotificationService
from .chatbot import EduCycleChatbot
import uuid

# Create your views here.

def home(request):
    items = Item.objects.filter(is_active=True).order_by('-created_at')
    query = request.GET.get('q')
    category = request.GET.get('category')
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )
    if category:
        items = items.filter(category=category)
    return render(request, 'hub/item_list.html', {'items': items})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, 'Registration successful! Please log in with your credentials.')
                return redirect('user_login')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'hub/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            # Try to authenticate with username or email
            user = authenticate(request, username=username, password=password)
            if user is None:
                # Try with email if username didn't work
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                
                # Admin redirect: admin@gmail.com with password admin123
                if user.email == 'admin@gmail.com':
                    messages.success(request, f'Welcome back, Admin!')
                    return redirect('admin_panel')
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username/email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()
    return render(request, 'hub/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('user_login')

def item_list(request):
    items = Item.objects.filter(is_active=True)
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Handle category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Order by creation date
    items = items.order_by('-created_at')
    
    return render(request, 'hub/item_list.html', {
        'items': items,
        'search_query': search_query,
        'category_filter': category_filter
    })

def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get suggestions from item names and categories
    suggestions = []
    
    # Search in item names
    items = Item.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(category__icontains=query)
    ).values('name', 'category').distinct()[:10]
    
    for item in items:
        suggestions.append({
            'text': item['name'],
            'category': item['category']
        })
    
    # Add category suggestions
    categories = Item.objects.filter(
        category__icontains=query
    ).values_list('category', flat=True).distinct()[:5]
    
    for category in categories:
        suggestions.append({
            'text': f"Category: {category}",
            'category': category
        })
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def item_create(request):
    if request.method == 'POST':
        # ── Idempotency guard: reject duplicate rapid submissions ──
        form_token = request.POST.get('form_token', '')
        last_token = request.session.get('last_item_form_token', '')
        if form_token and form_token == last_token:
            # Same token submitted twice — redirect without saving
            messages.warning(request, 'Your item was already submitted.')
            return redirect('item_list')
        if form_token:
            request.session['last_item_form_token'] = form_token

        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                item = form.save(commit=False)
                item.seller = request.user
                item.save()
                NotificationService.notify_item_added(request.user, item)
                messages.success(request, 'Item listed successfully!')
                return redirect('item_list')
            except Exception as e:
                messages.error(request, f'Failed to create item: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ItemForm()
    return render(request, 'hub/item_form.html', {'form': form})

def item_detail(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
        # Get related items from the same category
        related_items = Item.objects.filter(
            category=item.category,
            is_active=True
        ).exclude(id=item.id).order_by('-created_at')[:3]
        return render(request, 'hub/item_detail.html', {
            'item': item,
            'items': related_items
        })
    except Item.DoesNotExist:
        messages.error(request, 'Item not found.')
        return redirect('item_list')

@login_required
def send_message(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
        if request.method == 'POST':
            content = request.POST.get('content')
            if content and len(content.strip()) > 0:
                message_obj = Message.objects.create(
                    sender=request.user,
                    receiver=item.seller,
                    item=item,
                    content=content.strip()
                )
                
                # Send notification to seller
                NotificationService.notify_message_received(
                    receiver=item.seller,
                    sender=request.user,
                    item=item,
                    message_content=content.strip()
                )
                
                messages.success(request, 'Message sent to the seller!')
                return redirect('item_detail', item_id=item.id)
            else:
                messages.error(request, 'Message content cannot be empty.')
        return render(request, 'hub/send_message.html', {'item': item})
    except Item.DoesNotExist:
        messages.error(request, 'Item not found.')
        return redirect('item_list')

@login_required
def profile(request):
    if request.user.email == 'admin@gmail.com':
        return redirect('admin_panel')
    user_items = Item.objects.filter(seller=request.user).order_by('-created_at')
    received_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    return render(request, 'hub/profile.html', {'user_items': user_items, 'received_messages': received_messages})

@login_required
def item_edit(request, item_id):
    try:
        item = Item.objects.get(id=item_id, seller=request.user)
        if request.method == 'POST':
            form = ItemForm(request.POST, request.FILES, instance=item)
            if form.is_valid():
                form.save()
                messages.success(request, 'Item updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = ItemForm(instance=item)
        return render(request, 'hub/item_form.html', {'form': form, 'edit_mode': True})
    except Item.DoesNotExist:
        messages.error(request, 'Item not found or you do not have permission to edit it.')
        return redirect('profile')

@login_required
def item_delete(request, item_id):
    try:
        item = Item.objects.get(id=item_id, seller=request.user)
        if request.method == 'POST':
            item.delete()
            messages.success(request, 'Item deleted successfully!')
            return redirect('profile')
        return render(request, 'hub/item_confirm_delete.html', {'item': item})
    except Item.DoesNotExist:
        messages.error(request, 'Item not found or you do not have permission to delete it.')
        return redirect('profile')

# Cart functionality
@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    return render(request, 'hub/cart.html', {
        'cart': cart,
        'cart_items': cart_items
    })

@login_required
def add_to_cart(request, item_id):
    try:
        item = Item.objects.get(id=item_id, is_active=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Check if item is already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            item=item,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, f'{item.name} added to cart!')
        return redirect('cart')
    except Item.DoesNotExist:
        messages.error(request, 'Item not found.')
        return redirect('item_list')

@login_required
def remove_from_cart(request, cart_id):
    try:
        cart_item = CartItem.objects.get(id=cart_id, cart__user=request.user)
        item_name = cart_item.item.name
        cart_item.delete()
        messages.success(request, f'{item_name} removed from cart!')
    except CartItem.DoesNotExist:
        messages.error(request, 'Cart item not found.')
    
    return redirect('cart')

@login_required
def update_cart_quantity(request, cart_id):
    try:
        cart_item = CartItem.objects.get(id=cart_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
    except (CartItem.DoesNotExist, ValueError):
        messages.error(request, 'Invalid request.')
    
    return redirect('cart')

# Checkout and Order functionality
@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method')
        
        if not shipping_address:
            messages.error(request, 'Please provide a shipping address.')
            total = sum(cart_item.get_total_price() for cart_item in cart_items)
            return render(request, 'hub/checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total': total
            })
        
        try:
            # Create orders for each seller
            seller_orders = {}
            
            for cart_item in cart_items:
                seller = cart_item.item.seller
                if seller not in seller_orders:
                    seller_orders[seller] = {
                        'order': Order.objects.create(
                            buyer=request.user,
                            seller=seller,
                            total_amount=0,
                            shipping_address=shipping_address,
                            payment_method=payment_method
                        ),
                        'items': []
                    }
                
                # Create order item
                order_item = OrderItem.objects.create(
                    order=seller_orders[seller]['order'],
                    item=cart_item.item,
                    quantity=cart_item.quantity,
                    price_at_time=cart_item.item.price or 0
                )
                
                seller_orders[seller]['items'].append(order_item)
                seller_orders[seller]['order'].total_amount += order_item.get_total_price()
                seller_orders[seller]['order'].save()
            
                            # Clear the cart
                cart.cartitem_set.all().delete()
                
                # Send notifications for each order
                for order_data in seller_orders.values():
                    order = order_data['order']
                    for order_item in order.orderitem_set.all():
                        # Notify seller
                        NotificationService.notify_item_sold(
                            seller=order_item.item.seller,
                            buyer=request.user,
                            item=order_item.item,
                            order=order
                        )
                        
                        # Notify buyer
                        NotificationService.notify_item_purchased(
                            buyer=request.user,
                            seller=order_item.item.seller,
                            item=order_item.item,
                            order=order
                        )
                
                # Redirect to payment for the first order
                if seller_orders:
                    first_order = list(seller_orders.values())[0]['order']
                    return redirect('payment_page', order_id=first_order.id)
                else:
                    messages.success(request, 'Order placed successfully! You will receive confirmation emails.')
                    return redirect('orders')
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
    
    total = sum(cart_item.get_total_price() for cart_item in cart_items)
    return render(request, 'hub/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total': total
    })

@login_required
def orders(request):
    # Get orders where user is buyer
    buyer_orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    # Get orders where user is seller
    seller_orders = Order.objects.filter(seller=request.user).order_by('-created_at')
    
    # Debug: Print order counts
    print(f"Debug: User {request.user.username} has {buyer_orders.count()} buyer orders and {seller_orders.count()} seller orders")
    
    return render(request, 'hub/orders.html', {
        'bought_orders': buyer_orders,
        'sold_orders': seller_orders
    })

@login_required
def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        # Check if user is buyer or seller
        if order.buyer != request.user and order.seller != request.user:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('orders')
        
        order_items = order.orderitem_set.all()
        
        return render(request, 'hub/order_detail.html', {
            'order': order,
            'order_items': order_items
        })
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('orders')

@login_required
def remove_all_items(request):
    """Remove all items from the database. Only accessible by superusers."""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Get count before deletion for confirmation message
            item_count = Item.objects.count()
            
            # Delete all items
            Item.objects.all().delete()
            
            # Also clear all cart items since they reference items
            CartItem.objects.all().delete()
            
            # Clear all messages since they reference items
            Message.objects.all().delete()
            
            # Clear all order items since they reference items
            OrderItem.objects.all().delete()
            
            # Clear all orders since they reference items
            Order.objects.all().delete()
            
            messages.success(request, f'Successfully removed all {item_count} items and related data.')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Error removing items: {str(e)}')
            return redirect('home')
    
    # GET request - show confirmation page
    item_count = Item.objects.count()
    return render(request, 'hub/remove_all_items.html', {'item_count': item_count})

@login_required
def payment_page(request, order_id):
    """Display payment page for an order"""
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        total_amount = sum(item.get_total_price() for item in order.orderitem_set.all())
        
        return render(request, 'hub/payment.html', {
            'order': order,
            'total_amount': total_amount,
            'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        })
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('orders')

def about_us(request):
    """About Us page"""
    return render(request, 'hub/about_us.html')

def contact_us(request):
    """Contact Us page — saves submission to DB and shows inline success"""
    from .models import ContactMessage
    submitted = False
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'general').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            submitted = True
        else:
            messages.error(request, 'Please fill in all required fields.')
    return render(request, 'hub/contact_us.html', {'submitted': submitted})


def report_bug(request):
    """Report a Bug page — saves submission to DB and shows inline success"""
    from .models import BugReport
    submitted = False
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        email       = request.POST.get('email', '').strip()
        bug_type    = request.POST.get('bug_type', 'other').strip()
        severity    = request.POST.get('severity', 'medium').strip()
        description = request.POST.get('description', '').strip()
        steps       = request.POST.get('steps', '').strip()
        browser     = request.POST.get('browser', '').strip()
        device      = request.POST.get('device', '').strip()
        if name and email and description:
            BugReport.objects.create(
                name=name, email=email, bug_type=bug_type,
                severity=severity, description=description,
                steps=steps, browser=browser, device=device
            )
            submitted = True
        else:
            messages.error(request, 'Please fill in all required fields.')
    return render(request, 'hub/report_bug.html', {'submitted': submitted})

def help_center(request):
    """Help Center page"""
    return render(request, 'hub/help_center.html')


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'hub/privacy_policy.html')


def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'hub/terms_of_service.html')


def how_it_works(request):
    """How It Works page"""
    return render(request, 'hub/how_it_works.html')


def safety_guidelines(request):
    """Safety Guidelines page"""
    return render(request, 'hub/safety_guidelines.html')

# Review System Views
@login_required
def add_review(request, item_id):
    """Add a review for an item"""
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user has already reviewed this item
    existing_review = Review.objects.filter(item=item, user=request.user).first()
    if existing_review:
        messages.error(request, 'You have already reviewed this item.')
        return redirect('item_detail', item_id=item_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        if rating and title and comment:
            try:
                review = Review.objects.create(
                    item=item,
                    user=request.user,
                    rating=int(rating),
                    title=title,
                    comment=comment,
                    is_verified_purchase=True  # Assuming they can only review if they bought it
                )
                
                # Send notification to item owner
                NotificationService.notify_review_received(item.seller, request.user, item, review)
                
                messages.success(request, 'Review added successfully!')
                return redirect('item_detail', item_id=item_id)
            except Exception as e:
                messages.error(request, f'Failed to add review: {str(e)}')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'hub/add_review.html', {'item': item})

@login_required
def edit_review(request, review_id):
    """Edit a review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        if rating and title and comment:
            try:
                review.rating = int(rating)
                review.title = title
                review.comment = comment
                review.save()
                messages.success(request, 'Review updated successfully!')
                return redirect('item_detail', item_id=review.item.id)
            except Exception as e:
                messages.error(request, f'Failed to update review: {str(e)}')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'hub/edit_review.html', {'review': review})

@login_required
def delete_review(request, review_id):
    """Delete a review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        item_id = review.item.id
        review.delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('item_detail', item_id=item_id)
    
    return render(request, 'hub/delete_review.html', {'review': review})

# Notification Views
@login_required
def notifications(request):
    """View user notifications"""
    notifications = NotificationService.get_user_notifications(request.user)
    return render(request, 'hub/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if NotificationService.mark_notification_read(notification_id, request.user):
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    NotificationService.mark_all_notifications_read(request.user)
    return JsonResponse({'success': True})

# Chatbot Views
def chatbot(request):
    """Chatbot interface"""
    if request.method == 'POST':
        message = request.POST.get('message')
        session_id = request.POST.get('session_id', str(uuid.uuid4()))

        if message:
            bot = EduCycleChatbot()
            response = bot.get_response(message, session_id)
            escalate = response == '__ESCALATE_TO_ADMIN__'
            if escalate:
                response = (
                    "I'm not quite sure how to help with that one. "
                    "Let me connect you with a real person from our support team — "
                    "they'll be able to assist you much better! 🙋"
                )
            return JsonResponse({
                'response': response,
                'session_id': session_id,
                'escalate': escalate,
            })
    
    # For GET request, return the chatbot page
    chatbot = EduCycleChatbot()
    suggested_questions = chatbot.get_suggested_questions()
    welcome_message = chatbot.get_welcome_message()
    
    return render(request, 'hub/chatbot.html', {
        'suggested_questions': suggested_questions,
        'welcome_message': welcome_message
    })

def get_chat_history(request, session_id):
    """Get chat history for a session"""
    chatbot = EduCycleChatbot()
    history = chatbot.get_conversation_history(session_id)
    
    messages = []
    for msg in history:
        messages.append({
            'type': msg.message_type,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    
    return JsonResponse({'messages': messages})


@login_required
def settings_view(request):
    """User settings page — handles all settings actions"""
    from .models import UserProfile
    from django.contrib.auth import update_session_auth_hash

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    active_section = 'profile'  # default

    if request.method == 'POST':
        action = request.POST.get('action')
        active_section = request.POST.get('active_section', 'profile')

        # ── Update Profile ──────────────────────────────────────────
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name  = request.POST.get('last_name', '').strip()
            new_email = request.POST.get('email', '').strip()
            if new_email and new_email != request.user.email:
                if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                    messages.error(request, 'That email address is already in use.')
                else:
                    request.user.email = new_email
            request.user.save()
            profile.phone_number  = request.POST.get('phone_number', '').strip()
            profile.department    = request.POST.get('department', profile.department)
            profile.year_of_study = request.POST.get('year_of_study', profile.year_of_study)
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            active_section = 'profile'

        # ── Change Password ─────────────────────────────────────────
        elif action == 'change_password':
            current = request.POST.get('current_password', '')
            new_pw  = request.POST.get('new_password', '')
            confirm = request.POST.get('confirm_password', '')
            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif new_pw != confirm:
                messages.error(request, 'New passwords do not match.')
            elif len(new_pw) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new_pw)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully. You are still logged in.')
            active_section = 'security'

        # ── Save Notification Prefs ─────────────────────────────────
        elif action == 'save_notifications':
            # Store toggle states in session (no DB model for this yet)
            prefs = {
                'notif_messages':      'notif_messages'      in request.POST,
                'notif_sold':          'notif_sold'          in request.POST,
                'notif_reviews':       'notif_reviews'       in request.POST,
                'notif_orders':        'notif_orders'        in request.POST,
                'notif_announcements': 'notif_announcements' in request.POST,
            }
            request.session['notification_prefs'] = prefs
            messages.success(request, 'Notification preferences saved.')
            active_section = 'notifications'

        # ── Save Privacy Prefs ──────────────────────────────────────
        elif action == 'save_privacy':
            privacy = {
                'show_profile':  'show_profile'  in request.POST,
                'show_email':    'show_email'    in request.POST,
                'allow_messages':'allow_messages' in request.POST,
            }
            request.session['privacy_prefs'] = privacy
            messages.success(request, 'Privacy settings saved.')
            active_section = 'privacy'

        # ── Save Appearance ─────────────────────────────────────────
        elif action == 'save_appearance':
            request.session['theme']    = request.POST.get('theme', 'light')
            request.session['language'] = request.POST.get('language', 'en')
            messages.success(request, 'Appearance preferences saved.')
            active_section = 'appearance'

        # ── Delete Own Listings ─────────────────────────────────────
        elif action == 'delete_my_listings':
            confirm_text = request.POST.get('confirm_listings', '')
            if confirm_text == 'DELETE':
                count = Item.objects.filter(seller=request.user).count()
                # Remove related data first
                my_items = Item.objects.filter(seller=request.user)
                CartItem.objects.filter(item__in=my_items).delete()
                Message.objects.filter(item__in=my_items).delete()
                my_items.delete()
                messages.success(request, f'Deleted {count} listing(s) successfully.')
            else:
                messages.error(request, 'Please type DELETE to confirm.')
            active_section = 'danger'

        # ── Delete Account ──────────────────────────────────────────
        elif action == 'delete_account':
            confirm_text = request.POST.get('confirm_text', '')
            if confirm_text == 'DELETE':
                logout(request)
                request.user.delete()
                messages.success(request, 'Your account has been permanently deleted.')
                return redirect('home')
            else:
                messages.error(request, 'Please type DELETE exactly to confirm.')
            active_section = 'danger'

        return redirect(f'/settings/?section={active_section}')

    # ── GET ─────────────────────────────────────────────────────────
    active_section = request.GET.get('section', 'profile')
    notif_prefs = request.session.get('notification_prefs', {
        'notif_messages': True, 'notif_sold': True,
        'notif_reviews': True, 'notif_orders': True, 'notif_announcements': True,
    })
    privacy_prefs = request.session.get('privacy_prefs', {
        'show_profile': True, 'show_email': False, 'allow_messages': True,
    })
    theme    = request.session.get('theme', 'light')
    language = request.session.get('language', 'en')

    return render(request, 'hub/settings.html', {
        'profile':        profile,
        'user':           request.user,
        'active_section': active_section,
        'notif_prefs':    notif_prefs,
        'privacy_prefs':  privacy_prefs,
        'theme':          theme,
        'language':       language,
        'my_listing_count': Item.objects.filter(seller=request.user).count(),
    })


def newsletter_subscribe(request):
    """Handle newsletter subscription from the footer form"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            obj, created = NewsletterSubscription.objects.get_or_create(
                email=email, defaults={'is_active': True}
            )
            if created:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Subscribed successfully!'})
                messages.success(request, 'You have been subscribed to our newsletter!')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'You are already subscribed.'})
                messages.info(request, 'You are already subscribed.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please provide a valid email.'})
            messages.error(request, 'Please provide a valid email.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def admin_panel(request):
    """Custom admin panel — only accessible to admin@gmail.com"""
    if request.user.email != 'admin@gmail.com':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')

    # Handle POST actions (update order status, resolve bugs/contacts, etc.)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_order_status':
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('status')
            try:
                order = Order.objects.get(id=order_id)
                order.status = new_status
                order.save()
                messages.success(request, f'Order #{order_id} status updated to {new_status}.')
            except Order.DoesNotExist:
                messages.error(request, 'Order not found.')

        elif action == 'resolve_bug':
            bug_id = request.POST.get('bug_id')
            try:
                bug = BugReport.objects.get(id=bug_id)
                bug.is_resolved = not bug.is_resolved
                bug.save()
                status = 'resolved' if bug.is_resolved else 'reopened'
                messages.success(request, f'Bug #{bug_id} has been {status}.')
            except BugReport.DoesNotExist:
                messages.error(request, 'Bug report not found.')

        elif action == 'resolve_contact':
            contact_id = request.POST.get('contact_id')
            try:
                contact = ContactMessage.objects.get(id=contact_id)
                contact.is_resolved = not contact.is_resolved
                contact.save()
                status = 'resolved' if contact.is_resolved else 'reopened'
                messages.success(request, f'Contact #{contact_id} has been {status}.')
            except ContactMessage.DoesNotExist:
                messages.error(request, 'Contact message not found.')

        elif action == 'delete_review':
            review_id = request.POST.get('review_id')
            try:
                review = Review.objects.get(id=review_id)
                review.delete()
                messages.success(request, f'Review #{review_id} has been deleted.')
            except Review.DoesNotExist:
                messages.error(request, 'Review not found.')

        elif action == 'toggle_item':
            item_id = request.POST.get('item_id')
            try:
                item = Item.objects.get(id=item_id)
                item.is_active = not item.is_active
                item.save()
                status = 'activated' if item.is_active else 'deactivated'
                messages.success(request, f'Item "{item.name}" has been {status}.')
            except Item.DoesNotExist:
                messages.error(request, 'Item not found.')

        elif action == 'remove_subscriber':
            sub_id = request.POST.get('sub_id')
            try:
                sub = NewsletterSubscription.objects.get(id=sub_id)
                sub.is_active = not sub.is_active
                sub.save()
                status = 'activated' if sub.is_active else 'deactivated'
                messages.success(request, f'Subscriber {sub.email} has been {status}.')
            except NewsletterSubscription.DoesNotExist:
                messages.error(request, 'Subscriber not found.')

        return redirect('admin_panel')

    # ── Dashboard statistics ─────────────────────────────────────
    from django.db.models import Count, Sum, Avg

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0

    total_items = Item.objects.count()
    active_items = Item.objects.filter(is_active=True).count()
    total_users = User.objects.count()

    total_reviews = Review.objects.count()
    avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0

    total_bugs = BugReport.objects.count()
    open_bugs = BugReport.objects.filter(is_resolved=False).count()
    critical_bugs = BugReport.objects.filter(severity='critical', is_resolved=False).count()

    total_contacts = ContactMessage.objects.count()
    open_contacts = ContactMessage.objects.filter(is_resolved=False).count()

    total_subscribers = NewsletterSubscription.objects.filter(is_active=True).count()

    # ── Data for tabs ────────────────────────────────────────────
    orders = Order.objects.select_related('buyer', 'seller').order_by('-created_at')[:50]
    reviews = Review.objects.select_related('item', 'user').order_by('-created_at')[:50]
    bugs = BugReport.objects.order_by('-submitted_at')[:50]
    contacts = ContactMessage.objects.order_by('-submitted_at')[:50]
    subscribers = NewsletterSubscription.objects.order_by('-subscribed_at')[:50]
    items = Item.objects.select_related('seller').order_by('-created_at')[:50]
    users = User.objects.order_by('-date_joined')[:50]

    context = {
        # Stats
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'active_items': active_items,
        'total_users': total_users,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'total_bugs': total_bugs,
        'open_bugs': open_bugs,
        'critical_bugs': critical_bugs,
        'total_contacts': total_contacts,
        'open_contacts': open_contacts,
        'total_subscribers': total_subscribers,
        # Tab data
        'orders': orders,
        'reviews': reviews,
        'bugs': bugs,
        'contacts': contacts,
        'subscribers': subscribers,
        'items': items,
        'users': users,
    }
    return render(request, 'hub/admin_panel.html', context)
