import stripe
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib import messages
from .models import Order, Payment
from .services import NotificationService
import requests

logger = logging.getLogger(__name__)

# Initialize payment gateways
stripe.api_key = settings.STRIPE_SECRET_KEY

# Try to import razorpay (optional)
try:
    import razorpay
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    RAZORPAY_AVAILABLE = True
except ImportError:
    logger.warning("Razorpay not available - using mock implementation")
    RAZORPAY_AVAILABLE = False
    razorpay_client = None

class PaymentGateway:
    """Payment gateway handler for multiple payment methods"""
    
    @staticmethod
    def create_stripe_payment_intent(order, amount):
        """Create Stripe payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='inr',
                metadata={
                    'order_id': order.id,
                    'user_id': order.buyer.id,
                    'seller_id': order.seller.id
                }
            )
            return intent
        except Exception as e:
            logger.error(f"Stripe payment intent creation failed: {str(e)}")
            return None

    @staticmethod
    def create_razorpay_order(order, amount):
        """Create Razorpay order"""
        if not RAZORPAY_AVAILABLE:
            # Mock implementation for testing
            return {
                'id': f'rzp_test_order_{order.id}',
                'amount': int(amount * 100),
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'status': 'created'
            }
        
        try:
            data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'notes': {
                    'order_id': str(order.id),
                    'user_id': str(order.buyer.id),
                    'seller_id': str(order.seller.id)
                }
            }
            razorpay_order = razorpay_client.order.create(data=data)
            return razorpay_order
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            return None

    @staticmethod
    def create_paypal_order(order, amount):
        """Create PayPal order (placeholder for PayPal integration)"""
        try:
            # PayPal integration would go here
            # For now, return a mock response
            return {
                'id': f'paypal_order_{order.id}',
                'status': 'created',
                'links': [
                    {
                        'href': f'/payment/paypal/approve/{order.id}/',
                        'rel': 'approve',
                        'method': 'GET'
                    }
                ]
            }
        except Exception as e:
            logger.error(f"PayPal order creation failed: {str(e)}")
            return None

@login_required
def payment_page(request, order_id):
    """Payment page with multiple payment options"""
    try:
        order = get_object_or_404(Order, id=order_id, buyer=request.user)
        total_amount = sum(item.get_total_price() for item in order.orderitem_set.all())
        
        # Create payment options
        payment_options = {
            'stripe': {
                'enabled': True,
                'name': 'Credit/Debit Card',
                'icon': 'fas fa-credit-card',
                'description': 'Pay securely with your card'
            },
            'razorpay': {
                'enabled': True,
                'name': 'UPI & Digital Wallets',
                'icon': 'fas fa-mobile-alt',
                'description': 'Pay with UPI, PayTM, Google Pay'
            },
            'paypal': {
                'enabled': False,  # Disabled for now
                'name': 'PayPal',
                'icon': 'fab fa-paypal',
                'description': 'Pay with PayPal account'
            },
            'cod': {
                'enabled': True,
                'name': 'Cash on Delivery',
                'icon': 'fas fa-money-bill-wave',
                'description': 'Pay when you receive the item'
            }
        }
        
        return render(request, 'hub/payment.html', {
            'order': order,
            'total_amount': total_amount,
            'payment_options': payment_options,
            'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        })
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('orders')

@login_required
def create_payment_intent(request, order_id):
    """Create Stripe payment intent"""
    try:
        order = get_object_or_404(Order, id=order_id, buyer=request.user)
        total_amount = sum(item.get_total_price() for item in order.orderitem_set.all())
        
        intent = PaymentGateway.create_stripe_payment_intent(order, total_amount)
        
        if intent:
            return JsonResponse({
                'client_secret': intent.client_secret,
                'success': True
            })
        else:
            return JsonResponse({
                'error': 'Failed to create payment intent',
                'success': False
            })
    except Exception as e:
        logger.error(f"Payment intent creation failed: {str(e)}")
        return JsonResponse({
            'error': 'Payment processing failed',
            'success': False
        })

@login_required
def create_razorpay_order(request, order_id):
    """Create Razorpay order"""
    try:
        order = get_object_or_404(Order, id=order_id, buyer=request.user)
        total_amount = sum(item.get_total_price() for item in order.orderitem_set.all())
        
        razorpay_order = PaymentGateway.create_razorpay_order(order, total_amount)
        
        if razorpay_order:
            return JsonResponse({
                'order_id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency'],
                'success': True
            })
        else:
            return JsonResponse({
                'error': 'Failed to create Razorpay order',
                'success': False
            })
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {str(e)}")
        return JsonResponse({
            'error': 'Payment processing failed',
            'success': False
        })

@login_required
def process_cod_payment(request, order_id):
    """Process Cash on Delivery payment"""
    try:
        order = get_object_or_404(Order, id=order_id, buyer=request.user)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            currency='INR',
            status='pending',
        )
        
        # Update order status
        order.status = 'confirmed'
        order.save()
        
        # Send notifications
        for order_item in order.orderitem_set.all():
            NotificationService.notify_item_sold(
                seller=order_item.item.seller,
                buyer=request.user,
                item=order_item.item,
                order=order
            )
            
            NotificationService.notify_item_purchased(
                buyer=request.user,
                seller=order_item.item.seller,
                item=order_item.item,
                order=order
            )
        
        messages.success(request, 'Order confirmed! Pay when you receive the item.')
        return redirect('order_detail', order_id=order.id)
        
    except Exception as e:
        logger.error(f"COD payment processing failed: {str(e)}")
        messages.error(request, 'Payment processing failed. Please try again.')
        return redirect('payment_page', order_id=order_id)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_stripe_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_stripe_payment_failure(payment_intent)
    
    return HttpResponse(status=200)

def handle_stripe_payment_success(payment_intent):
    """Handle successful Stripe payment"""
    try:
        order_id = payment_intent['metadata']['order_id']
        order = Order.objects.get(id=order_id)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=payment_intent['amount'] / 100,  # Convert from cents
            currency=payment_intent['currency'],
            status='completed',
            stripe_payment_intent_id=payment_intent['id'],
            stripe_charge_id=payment_intent.get('latest_charge')
        )
        
        # Update order status
        order.status = 'confirmed'
        order.save()
        
        # Send notifications
        for order_item in order.orderitem_set.all():
            NotificationService.notify_item_sold(
                seller=order_item.item.seller,
                buyer=order.buyer,
                item=order_item.item,
                order=order
            )
            
            NotificationService.notify_item_purchased(
                buyer=order.buyer,
                seller=order_item.item.seller,
                item=order_item.item,
                order=order
            )
        
        logger.info(f"Stripe payment successful for order {order_id}")
        
    except Exception as e:
        logger.error(f"Stripe payment success handling failed: {str(e)}")

def handle_stripe_payment_failure(payment_intent):
    """Handle failed Stripe payment"""
    try:
        order_id = payment_intent['metadata']['order_id']
        order = Order.objects.get(id=order_id)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=payment_intent['amount'] / 100,
            currency=payment_intent['currency'],
            status='failed',
            stripe_payment_intent_id=payment_intent['id']
        )
        
        logger.info(f"Stripe payment failed for order {order_id}")
        
    except Exception as e:
        logger.error(f"Stripe payment failure handling failed: {str(e)}")

@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Handle Razorpay webhooks"""
    try:
        # Verify webhook signature
        webhook_signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        
        # Verify signature (simplified for now)
        if webhook_signature:
            payload = request.body.decode('utf-8')
            # Add proper signature verification here
            
            data = json.loads(payload)
            
            if data['event'] == 'payment.captured':
                handle_razorpay_payment_success(data['payload']['payment']['entity'])
            elif data['event'] == 'payment.failed':
                handle_razorpay_payment_failure(data['payload']['payment']['entity'])
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Razorpay webhook handling failed: {str(e)}")
        return HttpResponse(status=400)

def handle_razorpay_payment_success(payment_data):
    """Handle successful Razorpay payment"""
    try:
        order_id = payment_data['notes']['order_id']
        order = Order.objects.get(id=order_id)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=payment_data['amount'] / 100,  # Convert from paise
            currency=payment_data['currency'],
            status='completed',
            stripe_charge_id=payment_data['id']  # Using this field for Razorpay payment ID
        )
        
        # Update order status
        order.status = 'confirmed'
        order.save()
        
        # Send notifications
        for order_item in order.orderitem_set.all():
            NotificationService.notify_item_sold(
                seller=order_item.item.seller,
                buyer=order.buyer,
                item=order_item.item,
                order=order
            )
            
            NotificationService.notify_item_purchased(
                buyer=order.buyer,
                seller=order_item.item.seller,
                item=order_item.item,
                order=order
            )
        
        logger.info(f"Razorpay payment successful for order {order_id}")
        
    except Exception as e:
        logger.error(f"Razorpay payment success handling failed: {str(e)}")

def handle_razorpay_payment_failure(payment_data):
    """Handle failed Razorpay payment"""
    try:
        order_id = payment_data['notes']['order_id']
        order = Order.objects.get(id=order_id)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=payment_data['amount'] / 100,
            currency=payment_data['currency'],
            status='failed',
            stripe_charge_id=payment_data['id']
        )
        
        logger.info(f"Razorpay payment failed for order {order_id}")
        
    except Exception as e:
        logger.error(f"Razorpay payment failure handling failed: {str(e)}")

@login_required
def payment_history(request):
    """View payment history"""
    payments = Payment.objects.filter(order__buyer=request.user).order_by('-created_at')
    return render(request, 'hub/payment_history.html', {'payments': payments})

@login_required
def refund_payment(request, payment_id):
    """Refund a payment"""
    try:
        payment = get_object_or_404(Payment, id=payment_id, order__buyer=request.user)
        
        if payment.status == 'completed':
            # Process refund based on payment method
            if payment.stripe_payment_intent_id:
                # Stripe refund
                refund = stripe.Refund.create(
                    payment_intent=payment.stripe_payment_intent_id
                )
                payment.status = 'refunded'
                payment.save()
                messages.success(request, 'Payment refunded successfully!')
            else:
                # Manual refund process
                payment.status = 'refunded'
                payment.save()
                messages.success(request, 'Refund request submitted!')
        else:
            messages.error(request, 'Payment cannot be refunded.')
            
        return redirect('payment_history')
        
    except Exception as e:
        logger.error(f"Payment refund failed: {str(e)}")
        messages.error(request, 'Refund processing failed.')
        return redirect('payment_history') 