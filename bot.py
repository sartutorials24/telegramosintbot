import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration - Using your provided token directly
BOT_TOKEN = "5833556052:AAGSnVI5gmwfB4sByMk_7fCIAUYWVzzxgjw"
API_URL = "https://decryptkarnrwalebkl.wasmer.app/"

class PhoneInfoBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_phone_number))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when command /start is issued."""
        welcome_text = """
👋 Welcome to Phone Number Info Bot!

📱 Simply send me a phone number and I'll fetch its details for you.

Examples:
- +1234567890
- 1234567890
- +1 (234) 567-890
- 234567890

🔍 I'll provide information like:
• Carrier/Operator
• Number type
• Location
• And other available details

Type /help for more information.
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message when command /help is issued."""
        help_text = """
📖 How to use this bot:

1. Send any phone number in international format or local format
2. The bot will query the API for details
3. You'll receive information about the number

📋 Supported formats:
• International: +1234567890
• Local: 1234567890
• With formatting: +1 (234) 567-890

⚡ Commands:
/start - Start the bot
/help - Show this help message

🔧 Examples to try:
+14155552671
+919876543210
+442072193000

⚠️ Note: The accuracy of information depends on the API database.
        """
        await update.message.reply_text(help_text)
    
    def clean_phone_number(self, phone_number: str) -> str:
        """Clean and validate phone number"""
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # If number doesn't start with +, assume it's a local number
        if not cleaned.startswith('+'):
            # For demo purposes, we'll keep it as is and let API handle it
            pass
        
        return cleaned
    
    def fetch_phone_info(self, phone_number: str) -> dict:
        """Fetch phone number information from API"""
        try:
            # Clean the phone number
            clean_number = self.clean_phone_number(phone_number)
            
            logger.info(f"Fetching info for number: {clean_number}")
            
            # Prepare API parameters
            params = {
                'key': 'lodalelobaby',
                'term': clean_number
            }
            
            # Make API request
            response = requests.get(API_URL, params=params, timeout=15)
            
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API Response Data: {data}")
                return data
            else:
                logger.error(f"API returned status code: {response.status_code}")
                return {"error": f"API returned status code: {response.status_code}", "success": False}
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return {"error": "Request timeout - API is taking too long to respond", "success": False}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}
    
    def format_phone_info(self, data: dict, original_number: str) -> str:
        """Format the phone information into a readable message"""
        
        # Check if there's an error
        if "error" in data:
            return f"❌ Error fetching information for {original_number}:\n{data['error']}"
        
        # Check if API returned empty data or no results
        if not data or (isinstance(data, list) and len(data) == 0):
            return f"❌ No information found for {original_number}\n\n💡 Try with a different number format or check if the number is valid."
        
        # Handle both list and dictionary responses
        if isinstance(data, list):
            if len(data) == 0:
                return f"❌ No information found for {original_number}"
            # Take the first result if it's a list
            data = data[0]
        
        # Start building the response
        response_lines = [f"📱 **Phone Number Information**\n"]
        response_lines.append(f"🔢 **Original:** `{original_number}`")
        
        # Add number if available
        if data.get("number"):
            response_lines.append(f"🔧 **Number:** `{data['number']}`")
        
        # Add carrier information
        if data.get("carrier"):
            response_lines.append(f"📡 **Carrier:** {data['carrier']}")
        elif data.get("operator"):
            response_lines.append(f"📡 **Operator:** {data['operator']}")
        
        # Add number type
        if data.get("type"):
            number_type = data["type"].title()
            response_lines.append(f"📊 **Type:** {number_type}")
        elif data.get("lineType"):
            response_lines.append(f"📊 **Line Type:** {data['lineType']}")
        
        # Add location information
        if data.get("location"):
            response_lines.append(f"📍 **Location:** {data['location']}")
        elif data.get("region"):
            response_lines.append(f"📍 **Region:** {data['region']}")
        
        # Add country information
        if data.get("country"):
            response_lines.append(f"🌍 **Country:** {data['country']}")
        elif data.get("countryCode"):
            response_lines.append(f"🌍 **Country Code:** {data['countryCode']}")
        
        # Add validity information
        if "valid" in data:
            validity = "✅ Valid" if data["valid"] else "❌ Invalid"
            response_lines.append(f"✓ **Validity:** {validity}")
        
        # Add ported information if available
        if "ported" in data:
            ported_status = "✅ Yes" if data["ported"] else "❌ No"
            response_lines.append(f"🔄 **Ported:** {ported_status}")
        
        # Add any other available fields
        interesting_fields = ['name', 'status', 'timezone', 'cnam', 'spamScore']
        for field in interesting_fields:
            if data.get(field):
                field_name = field.title()
                response_lines.append(f"ℹ️ **{field_name}:** {data[field]}")
        
        # If no specific information found
        if len(response_lines) <= 2:
            response_lines.append("\nℹ️ **No detailed information available for this number.**")
            response_lines.append("The number might be invalid, not in database, or in private registry.")
            
            # Show available fields for debugging
            available_fields = [key for key in data.keys() if key not in ['success', 'error']]
            if available_fields:
                response_lines.append(f"\n🔍 **Available fields:** {', '.join(available_fields)}")
        
        response_lines.append("\n---")
        response_lines.append("⚠️ *Information provided by Phone Lookup API*")
        
        return "\n".join(response_lines)
    
    async def handle_phone_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming phone number messages"""
        user_message = update.message.text.strip()
        user = update.message.from_user
        
        logger.info(f"Received message from {user.first_name}: {user_message}")
        
        # Show typing action
        await update.message.chat.send_action(action="typing")
        
        # Check if message looks like a phone number (contains digits)
        if not any(char.isdigit() for char in user_message) or len(user_message) < 5:
            await update.message.reply_text(
                "❌ **Please send a valid phone number containing digits.**\n\n"
                "**Examples:**\n"
                "• `+1234567890`\n"
                "• `1234567890`\n"
                "• `+1 (234) 567-890`\n\n"
                "Type /help for more information."
            )
            return
        
        # Send initial processing message
        processing_msg = await update.message.reply_text(
            f"🔍 **Searching for information...**\n"
            f"**Number:** `{user_message}`\n"
            f"⏳ Please wait..."
        )
        
        try:
            # Fetch phone information
            phone_info = self.fetch_phone_info(user_message)
            
            # Format and send the response
            formatted_info = self.format_phone_info(phone_info, user_message)
            
            # Edit the original processing message with the results
            await processing_msg.edit_text(formatted_info, parse_mode='Markdown')
            
            logger.info(f"Successfully processed number for {user.first_name}")
            
        except Exception as e:
            logger.error(f"Error processing phone number: {e}")
            error_message = (
                f"❌ **Sorry, I encountered an error while processing** `{user_message}`\n\n"
                f"**Error:** {str(e)}\n\n"
                "**Please try:**\n"
                "• Using a different number format\n"
                "• Checking if the number is valid\n"
                "• Trying again later\n\n"
                "Type /help for assistance."
            )
            await processing_msg.edit_text(error_message, parse_mode='Markdown')
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Phone Info Bot...")
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        print("🤖 Phone Info Bot Started!")
        print("📍 Bot Token: 5833556052:AAGSnVI5gmwfB4sByMk_7fCIAUYWVzzxgjw")
        print("🌐 API: https://decryptkarnrwalebkl.wasmer.app/")
        print("🔑 API Key: lodalelobaby")
        print("🚀 Send a message to your bot on Telegram to test it!")
        
        self.application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

def main():
    """Main function to run the bot"""
    try:
        # Create and run the bot with your token
        bot = PhoneInfoBot(BOT_TOKEN)
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Error starting bot: {e}")
        print("Please check your bot token and internet connection.")

if __name__ == '__main__':
    main()
