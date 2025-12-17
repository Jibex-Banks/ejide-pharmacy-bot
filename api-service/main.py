from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import sqlite3
import csv
import io
from ai_handler import MetaAIHandler
from database import Database

app = FastAPI(title="Ejide Pharmacy API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
db = Database()
ai_handler = MetaAIHandler()

class ChatMessage(BaseModel):
    phone_number: str
    message: str
    is_admin: bool
    timestamp: str

@app.on_event("startup")
async def startup():
    db.initialize()
    print("✅ Database initialized with medication tracking")

@app.post("/chat")
async def chat(msg: ChatMessage):
    """Main chat endpoint - handles all incoming messages"""
    
    # Log conversation
    db.log_conversation(msg.phone_number, msg.message, msg.is_admin)
    
    message_lower = msg.message.lower().strip()
    
    # Admin commands
    if msg.is_admin:
        # Inventory management
        if message_lower.startswith(("add drug", "update drug", "add inventory")):
            return handle_admin_inventory(msg.message, msg.phone_number)
        
        # Analytics commands
        elif message_lower in ["analytics", "show analytics", "predictive insights", "insights"]:
            return generate_analytics_report()
        
        # Inventory analysis
        elif message_lower in ["inventory report", "show inventory", "stock report", "inventory analysis"]:
            return generate_inventory_report()
        
        # Weekly report
        elif message_lower in ["weekly report", "week report", "weekly summary"]:
            return generate_weekly_report()
        
        # Help command
        elif message_lower == "help":
            return {"reply": get_admin_help()}
    
    # Check for cart/checkout commands
    if message_lower.startswith(("checkout", "check out")):
        return handle_checkout(msg.phone_number, msg.message)
    
    # Get context
    customer_history = db.get_customer_history(msg.phone_number)
    inventory = db.get_inventory()
    cart = db.get_cart(msg.phone_number)
    
    # Generate AI response
    ai_response = ai_handler.generate_response(
        message=msg.message,
        customer_history=customer_history,
        inventory=inventory,
        cart=cart,
        is_admin=msg.is_admin
    )
    
    # Check if customer wants to add to cart
    cart_action = parse_cart_action(msg.message, inventory)
    if cart_action:
        db.add_to_cart(msg.phone_number, cart_action['drug_name'], cart_action['quantity'])
        cart = db.get_cart(msg.phone_number)
        cart_summary = format_cart_summary(cart)
        ai_response += f"\n\n{cart_summary}"
    
    return {"reply": ai_response}

def parse_cart_action(message: str, inventory: List[dict]) -> Optional[dict]:
    """Parse if customer wants to add items to cart"""
    message_lower = message.lower()
    
    # Patterns: "add 2 paracetamol", "3 ibuprofen", "I want 5 chloroquine"
    words = message_lower.split()
    
    for i, word in enumerate(words):
        if word.isdigit() and i + 1 < len(words):
            quantity = int(word)
            potential_drug = words[i + 1]
            
            for item in inventory:
                if potential_drug in item['drug_name'].lower():
                    return {
                        'drug_name': item['drug_name'],
                        'quantity': quantity
                    }
    
    return None

def format_cart_summary(cart: List[dict]) -> str:
    """Format cart items with total"""
    if not cart:
        return "🛒 Your cart is empty."
    
    summary = "🛒 *YOUR CART:*\n"
    total = 0
    
    for item in cart:
        item_total = item['quantity'] * item['price']
        total += item_total
        summary += f"• {item['drug_name'].title()} x{item['quantity']} = ₦{item_total:,.2f}\n"
    
    summary += f"\n💰 *TOTAL: ₦{total:,.2f}*\n"
    summary += "\nReady to checkout? Reply 'checkout'"
    
    return summary

def handle_checkout(phone_number: str, message: str) -> dict:
    """Handle customer checkout"""
    cart = db.get_cart(phone_number)
    
    if not cart:
        return {"reply": "Your cart is empty. Add items first!\n\nExample: 'I want 2 paracetamol'"}
    
    # Calculate total
    total = sum(item['quantity'] * item['price'] for item in cart)
    
    # Generate order summary
    order_id = f"EJD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    receipt = "🧾 *ORDER SUMMARY*\n"
    receipt += f"Order ID: {order_id}\n"
    receipt += f"Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}\n"
    receipt += "="*35 + "\n\n"
    
    receipt += "📦 *ITEMS:*\n"
    for item in cart:
        item_total = item['quantity'] * item['price']
        receipt += f"• {item['drug_name'].title()}\n"
        receipt += f"  Qty: {item['quantity']} x ₦{item['price']:,.2f} = ₦{item_total:,.2f}\n"
        
        # Add dosage info if available
        if item.get('dosage_days') and item['dosage_days'] > 0:
            receipt += f"  📅 Treatment: {item['dosage_days']} days ({item.get('dosage_frequency', 'as prescribed')})\n"
        receipt += "\n"
    
    receipt += "="*35 + "\n"
    receipt += f"💰 *TOTAL: ₦{total:,.2f}*\n\n"
    
    receipt += "💳 *PAYMENT DETAILS:*\n"
    receipt += get_account_details() + "\n\n"
    
    receipt += "📍 *NEXT STEPS:*\n"
    receipt += "1. Transfer amount to account above\n"
    receipt += "2. Send screenshot of payment\n"
    receipt += "3. We'll confirm and prepare order\n"
    receipt += "4. Visit pharmacy or request delivery\n\n"
    
    # Add medication reminder notice
    has_medication = any(item.get('dosage_days', 0) > 0 for item in cart)
    if has_medication:
        receipt += "💊 *MEDICATION REMINDERS:*\n"
        receipt += "You'll receive daily reminders to take your medication and health checkups after treatment. Stay healthy! 😊\n\n"
    
    receipt += "⏰ Order valid for 24 hours\n"
    receipt += "📞 Reply 'help' for assistance\n\n"
    receipt += "Thank you for choosing Ejide Pharmacy! 🏥"
    
    # Record purchases
    for item in cart:
        db.record_purchase(
            phone_number, 
            item['drug_name'], 
            item['quantity'], 
            item['price'] * item['quantity']
        )
    
    # Clear cart
    db.clear_cart(phone_number)
    
    return {"reply": receipt}

def get_account_details() -> str:
    """Get pharmacy account details"""
    return """Bank: GTBank
Account Name: Ejide Pharmacy Ltd
Account Number: 0123456789

OR

Bank: Access Bank  
Account Name: Ejide Pharmacy
Account Number: 9876543210"""

def handle_admin_inventory(message: str, phone_number: str) -> dict:
    """Handle admin inventory commands"""
    try:
        parts = message.lower().split()
        
        if len(parts) >= 5:
            drug_name = parts[2]
            quantity = int(parts[3])
            price = float(parts[4])
            category = " ".join(parts[5:]) if len(parts) > 5 else "general"
            
            db.update_inventory(drug_name, quantity, price, category)
            
            return {
                "reply": f"✅ *Inventory Updated!*\n\n"
                        f"Drug: {drug_name.title()}\n"
                        f"Qty: {quantity}\n"
                        f"Price: ₦{price:,.2f}\n"
                        f"Category: {category.title()}"
            }
        else:
            return {
                "reply": "❌ Invalid format.\n\n"
                        "*Use:* add drug [name] [qty] [price] [category]\n"
                        "*Example:* add drug paracetamol 100 500 fever"
            }
    except Exception as e:
        return {"reply": f"❌ Error: {str(e)}"}

def generate_analytics_report() -> dict:
    """Generate predictive analytics report"""
    analytics = db.get_predictive_analytics()
    
    report = "📊 *PREDICTIVE ANALYTICS & INSIGHTS*\n"
    report += f"📅 Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}\n"
    report += "="*40 + "\n\n"
    
    # Revenue Trends
    report += "💰 *REVENUE TRENDS:*\n"
    rev = analytics['revenue_trend']
    report += f"This Week: ₦{rev['this_week']:,.2f}\n"
    report += f"Last Week: ₦{rev['last_week']:,.2f}\n"
    growth = rev.get('growth_percent', 0)
    emoji = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
    report += f"Growth: {growth:+.1f}% {emoji}\n\n"
    
    # Top Selling Drugs
    report += "🔥 *TOP SELLING (Last 30 Days):*\n"
    for i, drug in enumerate(analytics['top_drugs_30days'][:3], 1):
        report += f"{i}. {drug['drug_name'].title()}: {drug['total_qty']} units ({drug['purchase_count']} orders)\n"
    report += "\n"
    
    # Stock-Out Risk
    if analytics['stockout_risk']:
        report += "⚠️ *STOCK-OUT RISK ALERT:*\n"
        for item in analytics['stockout_risk'][:3]:
            report += f"• {item['drug_name'].title()}: {item['current_stock']} left "
            report += f"({item.get('days_until_stockout', 'N/A')} days until out)\n"
        report += "💡 *Action:* Restock these items soon!\n\n"
    
    # Customer Retention
    report += "👥 *CUSTOMER METRICS:*\n"
    ret = analytics['retention_metrics']
    report += f"Total Customers: {ret['total_customers']}\n"
    report += f"Returning: {ret['returning_customers']}\n"
    report += f"Retention Rate: {ret['retention_rate']}%\n\n"
    
    # Medication Adherence
    report += "💊 *MEDICATION ADHERENCE:*\n"
    adh = analytics['adherence_metrics']
    report += f"Active Treatments: {adh['total_prescriptions']}\n"
    report += f"Completed: {adh['completed_treatments']}\n"
    report += f"Adherence Rate: {adh['adherence_rate']}%\n\n"
    
    # Peak Hours
    if analytics['peak_hours']:
        report += "⏰ *BUSIEST HOURS:*\n"
        for peak in analytics['peak_hours']:
            hour = peak['hour']
            period = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            report += f"• {display_hour} {period}: {peak['message_count']} messages\n"
        report += "\n"
    
    report += "💡 *AI RECOMMENDATIONS:*\n"
    
    # Generate smart recommendations
    if analytics['stockout_risk']:
        report += "• Urgent: Restock low inventory items\n"
    
    if rev.get('growth_percent', 0) < 0:
        report += "• Consider promotional campaigns\n"
    
    if ret['retention_rate'] < 50:
        report += "• Improve customer retention programs\n"
    
    if adh['adherence_rate'] < 70:
        report += "• Enhance medication reminder system\n"
    
    report += "\n📈 Powered by Meta AI Analytics"
    
    return {"reply": report}

def generate_inventory_report() -> dict:
    """Generate comprehensive inventory analysis"""
    analysis = db.get_inventory_analysis()
    
    report = "📦 *INVENTORY ANALYSIS*\n"
    report += "="*35 + "\n\n"
    
    # Overview
    overview = analysis['overview']
    report += f"📊 *OVERVIEW:*\n"
    report += f"Total Items: {overview['total_items']}\n"
    report += f"Total Value: ₦{overview['total_value']:,.2f}\n"
    report += f"Avg Stock: {int(overview['avg_stock_level'])} units\n\n"
    
    # Low Stock
    if analysis['low_stock']:
        report += f"⚠️ *LOW STOCK ({len(analysis['low_stock'])} items):*\n"
        for item in analysis['low_stock'][:5]:
            report += f"• {item['drug_name'].title()}: {item['quantity']} left (₦{item['price']})\n"
        report += "\n"
    
    # High Value Items
    report += "💎 *TOP VALUE ITEMS:*\n"
    for item in analysis['high_value_items'][:3]:
        report += f"• {item['drug_name'].title()}: ₦{item['total_value']:,.2f}\n"
    report += "\n"
    
    # By Category
    report += "📁 *BY CATEGORY:*\n"
    for cat in analysis['by_category'][:5]:
        report += f"• {cat['category'].title()}: {cat['item_count']} items (₦{cat['category_value']:,.2f})\n"
    
    return {"reply": report}

def generate_weekly_report() -> dict:
    """Generate weekly summary report"""
    stats = db.get_weekly_stats()
    
    report = "📊 *WEEKLY SUMMARY REPORT*\n"
    report += f"📅 {datetime.now().strftime('%B %d, %Y')}\n"
    report += "="*35 + "\n\n"
    
    report += f"💰 *SALES:*\n"
    report += f"Total Revenue: ₦{stats['total_revenue']:,.2f}\n"
    report += f"Orders: {stats['total_purchases']}\n"
    report += f"Customers: {stats['unique_customers']}\n"
    report += f"Top Drug: {stats['top_drug']}\n\n"
    
    report += f"📨 *ENGAGEMENT:*\n"
    report += f"Messages: {stats['total_messages']}\n\n"
    
    # Get low stock items
    inventory = db.get_inventory()
    low_stock = [i for i in inventory if i['quantity'] < 20]
    
    if low_stock:
        report += f"⚠️ *LOW STOCK:* {len(low_stock)} items\n"
        for item in low_stock[:3]:
            report += f"  • {item['drug_name'].title()}: {item['quantity']}\n"
    
    return {"reply": report}

def get_admin_help() -> str:
    """Admin help message"""
    return """🔧 *ADMIN COMMANDS:*

📦 *Inventory:*
• add drug [name] [qty] [price] [category]
• inventory report / inventory analysis
• Upload CSV via WhatsApp

📊 *Analytics:*
• analytics / predictive insights
• weekly report / weekly summary

💡 *Examples:*
• "analytics" - Get AI-powered insights
• "inventory report" - Full stock analysis
• "weekly report" - Week summary
• "add drug paracetamol 100 500 fever"

📤 *CSV Upload:*
Send CSV file with columns:
drug_name,quantity,price,category,description,dosage_days,dosage_frequency"""

@app.post("/upload-inventory")
async def upload_inventory_csv(file: UploadFile = File(...)):
    """Upload inventory via CSV"""
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))
        
        added_count = 0
        errors = []
        
        for row in csv_reader:
            try:
                drug_name = row['drug_name'].strip().lower()
                quantity = int(row['quantity'])
                price = float(row['price'])
                category = row.get('category', 'general').strip()
                description = row.get('description', '').strip()
                dosage_days = int(row.get('dosage_days', 0))
                dosage_frequency = row.get('dosage_frequency', 'as prescribed').strip()
                
                db.update_inventory(drug_name, quantity, price, category, description, dosage_days, dosage_frequency)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Row {added_count + 1}: {str(e)}")
        
        response = f"✅ *CSV Upload Complete!*\n\n"
        response += f"✓ Added/Updated: {added_count} items\n"
        
        if errors:
            response += f"\n⚠️ Errors ({len(errors)}):\n"
            for error in errors[:5]:
                response += f"• {error}\n"
        
        return {"reply": response}
        
    except Exception as e:
        return {"reply": f"❌ CSV Upload Failed: {str(e)}"}

@app.get("/medication-reminders")
async def get_medication_reminders():
    """Get medication reminders for automated system"""
    reminders_list = db.get_medication_reminders()
    
    reminders = []
    for reminder in reminders_list:
        phone = reminder['phone_number']
        drug = reminder['drug_name']
        reminder_type = reminder['reminder_type']
        dosage = reminder.get('dosage_frequency', 'as prescribed')
        
        if reminder_type == 'daily':
            message = (
                f"💊 *MEDICATION REMINDER*\n\n"
                f"Time to take your {drug.title()}!\n"
                f"Dosage: {dosage}\n\n"
                f"✅ Reply 'took it' to confirm\n"
                f"❌ Reply 'missed' if you missed a dose\n\n"
                f"Stay consistent for best results! 💪"
            )
        elif reminder_type == 'completion':
            message = (
                f"🎉 *TREATMENT MILESTONE*\n\n"
                f"You've completed your {drug.title()} treatment course!\n\n"
                f"How are you feeling?\n"
                f"• Much better 😊\n"
                f"• Some improvement 🤔\n"
                f"• No change 😟\n\n"
                f"Your feedback helps us serve you better!"
            )
        else:  # checkup
            message = (
                f"🏥 *HEALTH CHECK-IN*\n\n"
                f"It's been 3 days since you completed {drug.title()}.\n\n"
                f"Quick checkup:\n"
                f"• Are your symptoms gone?\n"
                f"• Any side effects?\n"
                f"• Need any other medication?\n\n"
                f"We're here to help! 😊"
            )
        
        reminders.append({
            "phone_number": phone,
            "message": message,
            "purchase_id": reminder['purchase_id'],
            "reminder_type": reminder_type
        })
        
        # Mark reminder as sent
        db.mark_reminder_sent(reminder['purchase_id'])
        
        # Mark as completed if checkup
        if reminder_type == 'checkup':
            db.mark_treatment_completed(reminder['purchase_id'])
    
    return {"reminders": reminders}

@app.get("/generate-weekly-report")
async def api_generate_weekly_report():
    """API endpoint for weekly report generation"""
    result = generate_weekly_report()
    return {"report": result["reply"]}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Ejide Pharmacy API",
        "features": [
            "24/7 WhatsApp engagement",
            "AI-powered inventory",
            "Medication reminders",
            "Smart shopping cart",
            "Predictive analytics",
            "On-demand admin reports"
        ]
    }