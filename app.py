from flask import Flask, render_template, request, jsonify
import webbrowser
import threading
import time
from chatbot import CustomerSupportChatbot

app = Flask(__name__)
app.secret_key = 'chatbot_session'

# Global bot instance to maintain state
bot = CustomerSupportChatbot()

def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global bot
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'})
    
    bot_response = bot.get_response(user_message)
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    print("Starting Customer Support Chatbot...")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, use_reloader=False, port=8080)
