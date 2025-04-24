import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
from core.assistant import PersonalAssistant
from tools.email import get_email_tools
from tools.transcribe import get_transcribe_tools
from tools.knowledge import get_knowledge_tools
from tools.calendar import get_calendar_tools

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "noori-whatsapp-verify-token")

class WhatsAppBot:
    def __init__(self):
        self.app = Flask(__name__)
        self._setup_assistant()
        self._setup_routes()

    def _setup_assistant(self):
        tools = []
        tools.extend(get_email_tools())
        tools.extend(get_transcribe_tools())
        tools.extend(get_knowledge_tools())
        tools.extend(get_calendar_tools())
        self.assistant = PersonalAssistant(
            model="google-gla:gemini-2.0-flash",
            system_prompt="""
              You are Noori my super smart personal assistant.
              you have access to the following tools:
              - email_send: Send an email to the specified recipient
              - email_read: Read emails from the inbox
              - email_mark_read: Mark an email as read
              - transcribe: Transcribe audio from file path or bytes
              - knowledge_upsert: Add or update knowledge in the knowledge base even tho they are subjective opinions
              - knowledge_search: Search for similar knowledge in the knowledge base
              - calendar_get_today: Get today's date in YYYY-MM-DD format
              - calendar_create_event: Create event with time conflict checking. Returns either created event details or conflict information
              - calendar_update_event: Update an existing calendar event. Args: calendar_id, event_id, summary, start, end, description
              Responses:
              - Be concise but helpful
              - handle errors gracefully    
              - Only ask questions if absolutely necessary
              - output should always be organized and formatted
           """,
            tools=tools
        )

    def _setup_routes(self):
        @self.app.route("/webhook", methods=["GET"])
        def verify():
            # Verification for WhatsApp webhook
            mode = request.args.get("hub.mode")
            token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return challenge, 200
            return "Verification failed", 403

        @self.app.route("/webhook", methods=["POST"])
        def webhook():
            data = request.get_json()
            # Only process messages
            if data and data.get("entry"):
                for entry in data["entry"]:
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        messages = value.get("messages", [])
                        for message in messages:
                            self.handle_message(message, value)
            return "OK", 200

    def handle_message(self, message, value):
        # Extract text and sender
        text = message.get("text", {}).get("body")
        sender = message.get("from")
        if not text or not sender:
            return
        # Run assistant
        response = self.assistant.run(text)
        if hasattr(response, "__await__"):
            import asyncio
            response = asyncio.get_event_loop().run_until_complete(response)
        self.send_message(sender, response)

    def send_message(self, to, message):
        url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        requests.post(url, headers=headers, json=data)

    def run(self, host="0.0.0.0", port=5000):
        self.app.run(host=host, port=port)
