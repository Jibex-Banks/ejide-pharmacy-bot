# 🏥 Ejide Pharmacy Chatbot - Setup Guide
## Complete Setup in 30 Minutes

---

## 🎯 What This System Does

1. **WhatsApp Chatbot** - Customers chat with pharmacy via WhatsApp
2. **Inventory Management** - Real-time drug stock tracking
3. **Customer Retention** - Automated medication reminders
4. **Weekly Reports** - Automated sales & inventory reports to admin
5. **Meta AI Powered** - Uses Meta Llama for intelligent responses

---

## 📋 Prerequisites

- Node.js (v16+) - [Download](https://nodejs.org/)
- Python (3.8+) - [Download](https://python.org/)
- A phone number for Ejide Pharmacy WhatsApp
- Code editor (VS Code recommended)

---

## 🚀 Quick Start (30 Minutes)

### Step 1: Project Setup (5 mins)

```bash
# Create project folder
mkdir ejide-pharmacy-bot
cd ejide-pharmacy-bot

# Create folder structure
mkdir whatsapp-service api-service database

# Clone or copy the code files into respective folders
```

### Step 2: WhatsApp Service Setup (10 mins)

```bash
cd whatsapp-service

# Create package.json (copy from artifact)
# Create index.js (copy from artifact)

# Install dependencies
npm install

# IMPORTANT: Edit index.js and add admin phone numbers
# Line 7-8: Replace with actual admin numbers (remove 234 from beginning)
# Example: ['8012345678', '8087654321']
```

### Step 3: Python API Setup (10 mins)

```bash
cd ../api-service

# Create files
# - main.py (copy from artifact)
# - database.py (copy from artifact)  
# - ai_handler.py (copy from artifact)
# - requirements.txt (copy from artifact)

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database folder
cd ..
mkdir database
```

### Step 4: Start the System (5 mins)

**Terminal 1 - Start Python API:**
```bash
cd api-service
# Make sure venv is activated
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ Database initialized
```

**Terminal 2 - Start WhatsApp Service:**
```bash
cd whatsapp-service
npm start
```

You should see a **QR CODE** in terminal!

### Step 5: Connect WhatsApp (2 mins)

1. **Scan QR Code:**
   - Open WhatsApp on Ejide Pharmacy phone
   - Go to Settings → Linked Devices → Link a Device
   - Scan the QR code in the terminal

2. **Wait for confirmation:**
   ```
   ✅ Ejide Pharmacy Bot is ready!
   📱 Customers can now chat with the pharmacy
   ```

3. **Test it:**
   - Send a message to the pharmacy number from ANY phone
   - Bot should respond immediately!

---

## 🔧 Configuration

### Admin Phone Numbers

Edit `whatsapp-service/index.js`:

```javascript
const ADMIN_NUMBERS = [
  '2348012345678',  // Add country code (234 for Nigeria)
  '2348087654321'   // Add all admin numbers
];
```

### Initial Inventory

The system comes with sample drugs. To customize:

Edit `api-service/database.py` line 50-57:

```python
initial_drugs = [
    ("paracetamol", 150, 500, "fever/pain", "For fever and pain relief"),
    ("your_drug", quantity, price, "category", "description"),
    # Add more drugs here
]
```

---

## 📱 How to Use

### For Customers (via WhatsApp)

Just send a message to Ejide Pharmacy WhatsApp number:

**Examples:**
- "Hello" → Get welcome message
- "Do you have paracetamol?" → Check availability & price
- "I need malaria drugs" → Get recommendations
- "How much is ibuprofen?" → Get price
- "I want to buy paracetamol" → Bot confirms and records purchase

### For Admins (via WhatsApp)

**Add/Update Drugs:**
```
add drug paracetamol 200 500 fever
```
Format: `add drug [name] [quantity] [price] [category]`

**Check Inventory:**
```
inventory report
```
or
```
show inventory
```

**Weekly Report:**
- Automated every Sunday 8 PM
- Manual: Just message "weekly report"

### Customer Retention (Automated)

- **Day 1 after purchase:** Reminder to take medication
- **Day 3 after purchase:** Another reminder
- **Day 7 after purchase:** "How are you feeling?" follow-up

All automatic! No action needed.

---

## 🎓 Testing Scenarios

### Test 1: Customer Inquiry
```
Customer: "Hello, do you have drugs for malaria?"
Bot: [Checks inventory, responds with available options and prices]
```

### Test 2: Admin Inventory Update
```
Admin: "add drug artemether 50 1500 malaria"
Bot: "✅ Inventory Updated! [Details]"
```

### Test 3: Purchase Recording
```
Customer: "I want to buy paracetamol"
Bot: [Confirms availability, records purchase for retention system]
```

---

## 🤖 Meta AI Integration

The system uses **Meta Llama 3** via Hugging Face (FREE):

- **No API key needed** for basic use
- **Optional:** Get HuggingFace token for better performance
  1. Go to [huggingface.co](https://huggingface.co)
  2. Create free account
  3. Get token from Settings → Access Tokens
  4. Add to environment: `export HF_TOKEN=your_token_here`

### Fallback System

If AI fails (internet issues, etc.), the system has rule-based fallback responses. **Your bot never goes down!**

---

## 📊 Features Checklist

- ✅ WhatsApp chatbot (whatsapp-web.js)
- ✅ Meta Llama AI (via Hugging Face)
- ✅ Inventory management
- ✅ Customer purchase tracking
- ✅ Automated medication reminders (Days 1, 3, 7)
- ✅ Weekly reports (Every Sunday 8 PM)
- ✅ Admin commands
- ✅ No verification needed (QR code only)
- ✅ FREE to run (no message costs)
- ✅ Admin/customer recognition

---

## 🎯 Hackathon Submission Points

### Meta Resources Used ✅
1. **Meta Llama 3 AI Model** - Core chatbot intelligence
2. **WhatsApp Platform** - Via whatsapp-web.js (Meta's WhatsApp)
3. **AI-Powered Customer Service** - Meta AI for natural conversations

### Key Features ✅
- ✅ Medical chatbot for pharmacy
- ✅ Drug inquiry system
- ✅ Inventory management  
- ✅ Customer retention (automated reminders)
- ✅ Weekly reports (automated)
- ✅ Admin/user recognition
- ✅ WhatsApp integration

---

## 🐛 Troubleshooting

### Issue: QR Code not showing
```bash
# Make sure whatsapp-web.js installed correctly
npm install --force
# Try again
npm start
```

### Issue: Bot not responding
```bash
# Check Python API is running
# Should see: Uvicorn running on http://127.0.0.1:8000

# Check logs in both terminals for errors
```

### Issue: "Authentication failed"
```bash
# Delete session folder and rescan
cd whatsapp-service
rm -rf .wwebjs_auth
npm start
# Scan new QR code
```

### Issue: Database error
```bash
# Delete and reinitialize
cd database
rm pharmacy.db
# Restart Python API (will recreate database)
```

---

## 📱 Production Deployment (Optional)

For real deployment after hackathon:

1. **Deploy Python API:**
   - Use Heroku, Railway, or DigitalOcean
   - Update `API_URL` in whatsapp-service/index.js

2. **Keep WhatsApp Service Running:**
   - Use VPS (DigitalOcean, Linode)
   - Or dedicated computer (Raspberry Pi)
   - Install PM2: `npm install -g pm2`
   - Run: `pm2 start index.js --name ejide-bot`

3. **Backups:**
   - Schedule database backups (pharmacy.db)
   - Keep .wwebjs_auth folder backed up (session)

---

## 🎉 You're Ready!

Your Ejide Pharmacy Bot is now:
- ✅ Answering customer questions 24/7
- ✅ Managing inventory in real-time
- ✅ Sending medication reminders automatically
- ✅ Generating weekly business reports
- ✅ Powered by Meta AI technology
