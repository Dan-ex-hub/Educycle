import re
import random
from datetime import datetime
from .models import ChatMessage

class EduCycleChatbot:
    def __init__(self):
        self.greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        self.farewells = ['bye', 'goodbye', 'see you', 'thanks', 'thank you']
        self.help_keywords = ['help', 'guide', 'how', 'what', 'where', 'when', 'why']
        
        # Define conversation flows
        self.conversation_flows = {
            'greeting': {
                'patterns': self.greetings,
                'responses': [
                    "Hello! Welcome to EduCycle! I'm here to help you navigate our student marketplace. How can I assist you today?",
                    "Hi there! I'm your EduCycle assistant. I can help you with buying, selling, and using our platform. What would you like to know?",
                    "Hey! Welcome to EduCycle! I'm here to guide you through our student marketplace. What can I help you with?"
                ]
            },
            'farewell': {
                'patterns': self.farewells,
                'responses': [
                    "You're welcome! Feel free to come back if you need more help. Happy trading on EduCycle!",
                    "Goodbye! Have a great day and happy shopping/selling on EduCycle!",
                    "Thanks for chatting! Don't hesitate to ask if you need help later. See you around!"
                ]
            },
            'buying': {
                'patterns': ['buy', 'purchase', 'shop', 'buying', 'how to buy', 'buy item'],
                'responses': [
                    "To buy items on EduCycle:\n1. Browse items on the homepage\n2. Click on an item to view details\n3. Add to cart or contact seller\n4. Complete checkout process\n5. Arrange pickup/delivery with seller",
                    "Buying is easy! Just browse items, add to cart, and checkout. You can also message sellers directly to ask questions before buying.",
                    "Here's how to buy:\n- Browse the item listings\n- Click on items you're interested in\n- Add to cart or message the seller\n- Complete your purchase\n- Meet up for pickup/delivery"
                ]
            },
            'selling': {
                'patterns': ['sell', 'selling', 'list', 'add item', 'post item', 'how to sell'],
                'responses': [
                    "To sell items on EduCycle:\n1. Log in to your account\n2. Click 'Add Item' in the navigation\n3. Fill in item details (name, description, price)\n4. Upload photos\n5. Submit your listing\n6. Respond to buyer inquiries",
                    "Selling is simple! Just click 'Add Item', fill in the details, add photos, and submit. You'll be notified when someone is interested.",
                    "To sell:\n- Log in and click 'Add Item'\n- Describe your item with photos\n- Set your price\n- Submit and wait for buyers\n- Respond to messages from interested buyers"
                ]
            },
            'account': {
                'patterns': ['account', 'profile', 'register', 'sign up', 'login', 'sign in'],
                'responses': [
                    "To create an account:\n1. Click 'Sign Up' in the navigation\n2. Fill in your details (name, email, password)\n3. Add your student information\n4. Verify your email\n5. Start buying and selling!",
                    "Creating an account is easy! Just click 'Sign Up', fill in your student details, verify your email, and you're ready to go.",
                    "For account help:\n- Click 'Sign Up' to create an account\n- Use your student email\n- Add your department and year\n- Verify your email to activate"
                ]
            },
            'safety': {
                'patterns': ['safe', 'safety', 'secure', 'trust', 'meet', 'pickup', 'delivery'],
                'responses': [
                    "Safety is our priority! Always:\n- Meet in public places (campus libraries, cafes)\n- Verify items before paying\n- Use cash or secure payment methods\n- Trust your instincts\n- Report any suspicious activity",
                    "Stay safe by meeting in public places, verifying items before purchase, and using secure payment methods. We have safety guidelines on our website.",
                    "Safety tips:\n- Meet in campus public areas\n- Check items before paying\n- Use secure payment methods\n- Report any issues immediately\n- Trust your gut feeling"
                ]
            },
            'payment': {
                'patterns': ['payment', 'pay', 'money', 'price', 'cost', 'payment method'],
                'responses': [
                    "Payment methods include:\n- Cash (recommended for local meetups)\n- Digital wallets (PayTM, Google Pay)\n- Online payments through our secure system\n- Payment details are arranged between buyers and sellers",
                    "We support various payment methods including cash, digital wallets, and online payments. Payment is typically arranged between buyers and sellers.",
                    "Payment options:\n- Cash for local meetups\n- Digital wallets\n- Online secure payments\n- Discuss payment method with seller before meeting"
                ]
            },
            'categories': {
                'patterns': ['category', 'categories', 'what can I sell', 'what can I buy', 'types of items'],
                'responses': [
                    "EduCycle categories include:\n- Textbooks and study materials\n- Lab equipment and supplies\n- Room decor and furniture\n- Mini-fridges and appliances\n- Electronics and gadgets\n- Sports equipment\n- And much more!",
                    "You can buy and sell various student items:\n- Textbooks and academic materials\n- Lab equipment and supplies\n- Room decor and furniture\n- Appliances and electronics\n- Sports and fitness equipment",
                    "Our categories include textbooks, lab equipment, room decor, appliances, electronics, sports gear, and many other student essentials."
                ]
            },
            'contact': {
                'patterns': ['contact', 'support', 'help desk', 'customer service', 'report'],
                'responses': [
                    "Need help? You can:\n- Visit our Help Center\n- Contact us through the Contact Us page\n- Report bugs through the Report a Bug page\n- Email us at support@educycle.com\n- Use the chat feature for immediate assistance",
                    "For support:\n- Check our Help Center first\n- Use the Contact Us page\n- Report issues through Report a Bug\n- Email support@educycle.com",
                    "Get help through:\n- Help Center for common questions\n- Contact Us page for general inquiries\n- Report a Bug for technical issues\n- Email support for urgent matters"
                ]
            },
            'reviews': {
                'patterns': ['review', 'rating', 'feedback', 'star', 'rate'],
                'responses': [
                    "Reviews help our community! You can:\n- Leave reviews for items you've purchased\n- Read reviews before buying\n- Rate sellers and buyers\n- Help others make informed decisions\n- Build trust in our community",
                    "Reviews are important for our community trust. You can leave reviews after purchases and read reviews before buying to make informed decisions.",
                    "Our review system:\n- Leave reviews after purchases\n- Read reviews before buying\n- Rate sellers and buyers\n- Help build community trust\n- Make informed decisions"
                ]
            }
        }

    def get_response(self, user_message, session_id):
        """Get chatbot response based on user message"""
        # Save user message
        ChatMessage.objects.create(
            session_id=session_id,
            message_type='user',
            content=user_message
        )
        
        # Process message and get response
        response = self._process_message(user_message.lower())
        
        # Save bot response
        ChatMessage.objects.create(
            session_id=session_id,
            message_type='bot',
            content=response
        )
        
        return response

    def _process_message(self, message):
        """Process user message and return appropriate response"""
        # Check for greetings
        if any(greeting in message for greeting in self.greetings):
            return random.choice(self.conversation_flows['greeting']['responses'])
        
        # Check for farewells
        if any(farewell in message for farewell in self.farewells):
            return random.choice(self.conversation_flows['farewell']['responses'])
        
        # Check for help keywords
        if any(help_word in message for help_word in self.help_keywords):
            return self._get_help_response()
        
        # Check for specific topics
        for topic, flow in self.conversation_flows.items():
            if topic not in ['greeting', 'farewell']:
                if any(pattern in message for pattern in flow['patterns']):
                    return random.choice(flow['responses'])
        
        # Default response for unrecognized messages
        return self._get_default_response()

    def _get_help_response(self):
        """Get help response with available topics"""
        return """I can help you with:

🛒 **Buying & Selling**
- How to buy items
- How to sell items
- Payment methods
- Safety guidelines

👤 **Account Management**
- Creating an account
- Profile settings
- Login/logout

📚 **Categories & Items**
- What you can buy/sell
- Item categories
- Listing items

🛡️ **Safety & Support**
- Safety guidelines
- Contact support
- Report issues

💬 **Reviews & Feedback**
- Leaving reviews
- Reading reviews
- Building trust

Just ask me about any of these topics!"""

    def _get_default_response(self):
        """Get default response for unrecognized messages — escalate to admin"""
        return "__ESCALATE_TO_ADMIN__"

    def get_conversation_history(self, session_id):
        """Get conversation history for a session"""
        return ChatMessage.objects.filter(session_id=session_id).order_by('timestamp')

    def get_suggested_questions(self):
        """Get suggested questions for users"""
        return [
            "How do I buy items?",
            "How do I sell items?",
            "How do I create an account?",
            "Is it safe to meet sellers?",
            "What payment methods are accepted?",
            "What can I buy and sell?",
            "How do I contact support?",
            "How do reviews work?"
        ]

    def get_welcome_message(self):
        """Get welcome message for new chat sessions"""
        return """👋 Welcome to EduCycle! I'm your personal assistant here to help you navigate our student marketplace.

I can help you with:
• Buying and selling items
• Account setup and management
• Safety guidelines
• Payment methods
• Platform features

Just ask me anything, or try one of these common questions:
• "How do I buy items?"
• "How do I sell items?"
• "Is it safe to meet sellers?"
• "What payment methods are accepted?"

What would you like to know about EduCycle?""" 