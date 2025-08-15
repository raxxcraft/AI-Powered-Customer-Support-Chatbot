import nltk
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class CustomerSupportChatbot:
    def __init__(self):
        # Sample order database
        self.orders = {
            'ORD123': {'status': 'Shipped', 'tracking': 'TRK789456', 'delivery': 'Expected Dec 28, 2024'},
            'ORD456': {'status': 'Processing', 'tracking': None, 'delivery': 'Expected Dec 30, 2024'},
            'ORD789': {'status': 'Delivered', 'tracking': 'TRK123789', 'delivery': 'Delivered Dec 25, 2024'}
        }
        
        self.waiting_for_order_id = False
        self.waiting_for_cancel_id = False
        self.last_order_id = None
        
        self.intents = {
            'greeting': {
                'patterns': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
                'responses': ['Hello! I can help with order tracking, returns, payments, order cancellation, and general questions. What would you like to know?', 'Hi there! I can help with order tracking, returns, payments, order cancellation, and general questions. What would you like to know?', 'Hey! I can help with order tracking, returns, payments, order cancellation, and general questions. What would you like to know?']
            },
            'order_status': {
                'patterns': ['order status', 'track order', 'where is my order', 'order tracking'],
                'responses': ['Please provide your order number:']
            },
            'return_policy': {
                'patterns': ['return policy', 'return item', 'refund', 'exchange'],
                'responses': ['Our return policy allows returns within 30 days. Items must be unused and in original packaging.', 'You can return items within 30 days for a full refund.']
            },
            'payment': {
                'patterns': ['payment', 'credit card', 'billing', 'charge', 'payment methods'],
                'responses': ['We accept all major credit cards, PayPal, and Apple Pay.', 'Your payment information is secure and encrypted.']
            },
            'cancel_order': {
                'patterns': ['cancel order', 'cancel my order', 'stop delivery', 'cancel'],
                'responses': ['I can help you cancel your order. Please provide your order number:']
            },
            'goodbye': {
                'patterns': ['bye', 'goodbye', 'see you', 'thanks', 'thank you'],
                'responses': ['Goodbye! Have a great day!', 'Thank you for contacting us!', 'See you later!']
            }
        }
        
        self.small_talk = {
            'how are you': 'I\'m doing great, thank you for asking! How can I help you?',
            'what is your name': 'I\'m your customer support assistant. How may I help you today?',
            'what can you do': 'I can help with order tracking, returns, payments, order cancellation, and general questions!',
            'help': 'I can assist with: order tracking, returns, payments, order cancellation, and more!'
        }
        
        # Prepare training data for ML component
        self.prepare_training_data()
    
    def prepare_training_data(self):
        self.training_sentences = []
        self.training_labels = []
        
        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                self.training_sentences.append(pattern.lower())
                self.training_labels.append(intent)
        
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.training_sentences)
    
    def preprocess_text(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def get_intent(self, user_input):
        processed_input = self.preprocess_text(user_input)
        
        # Rule-based matching first
        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                if pattern in processed_input:
                    return intent
        
        # ML-based matching using cosine similarity
        input_vector = self.vectorizer.transform([processed_input])
        similarities = cosine_similarity(input_vector, self.tfidf_matrix)
        best_match_idx = similarities.argmax()
        
        if similarities[0][best_match_idx] > 0.3:  # Threshold for similarity
            return self.training_labels[best_match_idx]
        
        return 'unknown'
    
    def extract_order_id(self, text):
        # Look for order ID pattern (ORD followed by numbers)
        order_pattern = r'ORD\d+'
        match = re.search(order_pattern, text.upper())
        return match.group() if match else None
    
    def get_response(self, user_input):
        processed_input = self.preprocess_text(user_input)
        
        # Check if waiting for order ID
        if self.waiting_for_order_id:
            self.waiting_for_order_id = False
            return self.check_order_status(user_input)
        
        # Check if waiting for cancel order ID
        if self.waiting_for_cancel_id:
            self.waiting_for_cancel_id = False
            return self.cancel_order(user_input)
        
        # Check small talk first
        for question, answer in self.small_talk.items():
            if question in processed_input:
                return answer
        
        # Get intent and respond
        intent = self.get_intent(user_input)
        
        if intent == 'order_status':
            # Check if order ID is already in the message
            order_id = self.extract_order_id(user_input)
            if order_id:
                return self.check_order_status(order_id)
            else:
                self.waiting_for_order_id = True
                return "Please provide your order number:"
        elif intent == 'cancel_order':
            # Check if order ID is already in the message
            order_id = self.extract_order_id(user_input)
            if order_id:
                return self.cancel_order(order_id)
            elif self.last_order_id:
                return self.cancel_order(self.last_order_id)
            else:
                self.waiting_for_cancel_id = True
                return "Please provide your order number to cancel:"
        elif intent != 'unknown':
            return random.choice(self.intents[intent]['responses'])
        else:
            return "I can help with order tracking, returns, payments, order cancellation, and general questions. What would you like to know?"
    
    def check_order_status(self, order_id):
        order_id = order_id.upper().strip()
        self.last_order_id = order_id  # Store for future use
        
        if order_id in self.orders:
            order = self.orders[order_id]
            if order['status'] == 'Shipped':
                return f"Order {order_id}: {order['status']} - Tracking: {order['tracking']} - {order['delivery']}"
            elif order['status'] == 'Processing':
                return f"Order {order_id}: {order['status']} - {order['delivery']}"
            elif order['status'] == 'Delivered':
                return f"Order {order_id}: {order['status']} - {order['delivery']}"
        else:
            return f"Order {order_id} not found. Please check your order number or contact support."
    
    def cancel_order(self, order_id):
        order_id = order_id.upper().strip()
        
        if order_id in self.orders:
            order = self.orders[order_id]
            if order['status'] == 'Processing':
                return f"Order {order_id} has been successfully cancelled. You will receive a confirmation email shortly."
            elif order['status'] == 'Shipped':
                return f"Order {order_id} has already shipped and cannot be cancelled. Please contact support for return options."
            elif order['status'] == 'Delivered':
                return f"Order {order_id} has been delivered and cannot be cancelled. Please see our return policy for options."
        else:
            return f"Order {order_id} not found. Please check your order number or contact support."

def chat():
    bot = CustomerSupportChatbot()
    print("Customer Support Chatbot")
    print("Type 'quit' to exit")
    print("-" * 30)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Bot: Goodbye! Have a great day!")
            break
        
        response = bot.get_response(user_input)
        print(f"Bot: {response}")

if __name__ == "__main__":
    chat()
