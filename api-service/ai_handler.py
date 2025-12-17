from dotenv import load_dotenv
from typing import List, Dict, Optional
import requests
import os

load_dotenv()

class MetaAIHandler:
    """
    AI Handler optimized for Groq API with Meta Llama 3.1
    Fast, friendly, and concise responses
    """
    
    def __init__(self):
        # Groq API (Primary - Fast & Reliable)
        self.GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.use_groq = True
        
        # HuggingFace (Backup)
        self.use_huggingface = False
        self.hf_api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
        self.hf_token = os.getenv("HF_TOKEN")
        
        # System prompt - Concise and friendly
        self.system_prompt = """You are Ejide Pharmacy's AI assistant. Be friendly, helpful, and concise.

CORE RULES:
- Check inventory before confirming availability
- Mention price and stock when available
- Be conversational but brief
- Use emojis sparingly (💊 🏥 😊 🛒)
- NEVER diagnose medical conditions
- NEVER prescribe medications or dosages
- Always refer medical questions to a pharmacist/doctor

FEATURES YOU HELP WITH:
1. Drug inquiries - Check stock and prices
2. Shopping cart - Help add items: "I want [qty] [drug]"
3. Checkout - Guide to payment when ready
4. General pharmacy info

PAYMENT INFO (share only when customer checks out):
Bank: GTBank
Account Name: Ejide Pharmacy Ltd
Account Number: 0123456789

OR

Bank: Access Bank
Account Name: Ejide Pharmacy
Account Number: 9876543210

Remember: Be helpful, friendly, and professional. Keep responses natural and conversational."""
    
    def generate_response(self, message: str, customer_history: Dict, 
                         inventory: List[Dict], cart: List[Dict] = None,
                         is_admin: bool = False) -> str:
        """Generate AI response"""
        
        # Build context
        context = self._build_context(message, customer_history, inventory, cart, is_admin)
        
        # Try Groq first (primary)
        if self.use_groq and self.GROQ_API_KEY:
            response = self._generate_groq_response(context)
            if response:
                return response
        
        # Fallback to HuggingFace if enabled
        if self.use_huggingface and self.hf_token:
            response = self._generate_huggingface(context)
            if response:
                return response
        
        # Final fallback to rule-based
        return self._fallback_response(context)
    
    def _build_context(self, message: str, customer_history: Dict, 
                      inventory: List[Dict], cart: List[Dict] = None,
                      is_admin: bool = False) -> str:
        """Build optimized context for AI"""
        
        context_parts = []
        
        # Add inventory (top 12 items for quick reference)
        if inventory:
            inv_text = "INVENTORY:\n"
            for item in inventory[:12]:
                inv_text += f"- {item['drug_name'].title()}: {item['quantity']} units @ ₦{item['price']:,.0f}\n"
            context_parts.append(inv_text)
        
        # Add cart if exists
        if cart:
            cart_text = "CUSTOMER'S CART:\n"
            cart_total = 0
            for item in cart:
                item_total = item['quantity'] * item['price']
                cart_total += item_total
                cart_text += f"- {item['drug_name'].title()} x{item['quantity']} = ₦{item_total:,.0f}\n"
            cart_text += f"Total: ₦{cart_total:,.0f}\n"
            context_parts.append(cart_text)
        
        # Add recent purchases (brief)
        if customer_history.get('purchases'):
            recent = customer_history['purchases'][:2]
            if recent:
                purchase_text = "PREVIOUS PURCHASES:\n"
                for p in recent:
                    purchase_text += f"- {p['drug_name'].title()}\n"
                context_parts.append(purchase_text)
        
        # Add customer message
        context_parts.append(f"CUSTOMER: {message}")
        
        return "\n\n".join(context_parts)
    
    def _generate_groq_response(self, context: str) -> Optional[str]:
        """Generate response using Groq API (Fast!)"""
        
        if not self.GROQ_API_KEY:
            print("⚠️ Groq API key not set")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ],
            "temperature": 0.7,
            "max_tokens": 400,  # Increased for natural responses
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.GROQ_API_URL, 
                headers=headers, 
                json=payload, 
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    ai_response = data["choices"][0]["message"]["content"].strip()
                    cleaned = self._clean_response(ai_response)
                    print(f"✅ Groq AI response generated")
                    return cleaned
                else:
                    print("⚠️ Groq returned empty response")
                    return None
            
            elif response.status_code == 401:
                print("❌ Groq API: Invalid API key")
                return None
            
            elif response.status_code == 429:
                print("⚠️ Groq API: Rate limit exceeded")
                return None
            
            else:
                print(f"⚠️ Groq API error {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Details: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return None
        
        except requests.exceptions.Timeout:
            print("⚠️ Groq API timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("⚠️ Groq API connection error - check internet")
            return None
        except Exception as e:
            print(f"⚠️ Groq API error: {e}")
            return None
    
    def _generate_huggingface(self, context: str) -> Optional[str]:
        """HuggingFace backup (slower but free)"""
        
        if not self.hf_token:
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.hf_token}"
        }
        
        full_prompt = f"{self.system_prompt}\n\n{context}"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                self.hf_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    if generated_text:
                        cleaned = self._clean_response(generated_text)
                        print(f"✅ HuggingFace response generated")
                        return cleaned
                elif isinstance(result, dict) and 'generated_text' in result:
                    cleaned = self._clean_response(result['generated_text'])
                    print(f"✅ HuggingFace response generated")
                    return cleaned
                
                return None
            
            elif response.status_code == 503:
                print("⚠️ HuggingFace model loading (20-60s wait)")
                return None
            
            else:
                print(f"⚠️ HuggingFace error: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"⚠️ HuggingFace error: {e}")
            return None
    
    def _fallback_response(self, context: str) -> str:
        """Smart rule-based fallback (always works!)"""
        
        # Extract customer message
        try:
            if "CUSTOMER:" in context:
                message = context.split("CUSTOMER:")[-1].strip().lower()
            else:
                message = context.lower()
        except:
            message = context.lower()
        
        # Extract inventory
        inventory_section = ""
        if "INVENTORY:" in context:
            try:
                inventory_section = context.split("INVENTORY:")[1].split("\n\n")[0]
            except:
                pass
        
        print(f"💡 Fallback response: '{message[:40]}...'")
        
        # Greetings
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings", "hola"]
        if any(word in message for word in greetings):
            return ("Hello! Welcome to Ejide Pharmacy! 😊\n\n"
                   "I can help you:\n"
                   "• Find medications and check prices\n"
                   "• Add items to cart: 'I want [qty] [drug]'\n"
                   "• Answer general pharmacy questions\n\n"
                   "What are you looking for today?")
        
        # Specific drug queries
        common_drugs = {
            "paracetamol": "fever and pain",
            "ibuprofen": "pain and inflammation",
            "amoxicillin": "bacterial infections",
            "chloroquine": "malaria",
            "artemether": "malaria",
            "coartem": "malaria",
            "vitamin": "health supplements",
            "cough": "cough and cold"
        }
        
        for drug, purpose in common_drugs.items():
            if drug in message:
                # Search inventory
                for line in inventory_section.split("\n"):
                    if drug in line.lower() and line.strip():
                        drug_info = line.strip('- ')
                        return (f"Yes! We have {drug.title()} 💊\n\n"
                               f"{drug_info}\n\n"
                               f"Used for {purpose}. To order:\n"
                               f"Reply: 'I want [quantity] {drug}'")
                
                # Not in stock
                return (f"Sorry, {drug.title()} is currently out of stock. 😔\n\n"
                       f"We have other options for {purpose}. "
                       f"Would you like recommendations?")
        
        # Condition-based queries
        conditions = {
            "malaria": ["chloroquine", "artemether", "coartem"],
            "fever": ["paracetamol", "ibuprofen"],
            "pain": ["paracetamol", "ibuprofen"],
            "headache": ["paracetamol", "ibuprofen"],
            "cold": ["cough syrup", "vitamin c"],
            "cough": ["cough syrup"]
        }
        
        for condition, suggested_drugs in conditions.items():
            if condition in message:
                available = []
                for drug in suggested_drugs:
                    for line in inventory_section.split("\n"):
                        if drug in line.lower() and line.strip():
                            available.append(line.strip('- '))
                
                if available:
                    response = f"For {condition}, we have:\n\n"
                    for i, drug_info in enumerate(available, 1):
                        response += f"{i}. {drug_info}\n"
                    response += f"\nTo order, say: 'I want [qty] [drug name]' 🛒"
                    return response
        
        # Price queries
        if any(word in message for word in ["price", "cost", "how much", "expensive"]):
            return ("I can check prices for you! 💰\n\n"
                   "Which medication? Just ask:\n"
                   "'How much is paracetamol?'")
        
        # Stock/availability queries
        if any(word in message for word in ["available", "in stock", "have", "sell", "stock"]):
            return ("Let me check our inventory! 📦\n\n"
                   "What medication do you need?\n"
                   "You can ask about specific drugs or conditions.")
        
        # Cart queries
        if any(word in message for word in ["cart", "basket", "added", "items"]):
            if "CUSTOMER'S CART:" in context:
                return ("Your cart is ready! 🛒\n\n"
                       "To add more: 'I want [qty] [drug]'\n"
                       "To checkout: Reply 'checkout'")
            else:
                return ("Your cart is empty. 🛒\n\n"
                       "To add items, say:\n"
                       "'I want 2 paracetamol'\n"
                       "'Add 3 ibuprofen'")
        
        # Checkout queries
        if any(word in message for word in ["checkout", "pay", "payment", "order", "buy now"]):
            if "CUSTOMER'S CART:" in context:
                return ("Great! To complete your order:\n"
                       "Reply 'checkout' and I'll send payment details.")
            else:
                return ("Your cart is empty. Add items first! 🛒\n\n"
                       "Example: 'I want 2 paracetamol'")
        
        # Medical advice (redirect)
        if any(word in message for word in ["sick", "ill", "symptom", "diagnose", "what should i take", "treatment"]):
            return ("I understand you're not feeling well. 🏥\n\n"
                   "I can show you available medications, but for medical advice, "
                   "please consult our pharmacist or a doctor.\n\n"
                   "Visit us or call to speak with a professional. Your health matters! 😊")
        
        # Default helpful response
        return ("I'm here to help! 🏥\n\n"
               "You can:\n"
               "• Ask about medications: 'Do you have paracetamol?'\n"
               "• Check prices: 'How much is ibuprofen?'\n"
               "• Add to cart: 'I want 2 paracetamol'\n"
               "• Ask about conditions: 'What do you have for malaria?'\n\n"
               "What would you like to know?")
    
    def _clean_response(self, response: str) -> str:
        """Clean AI response"""
        
        # Remove common AI artifacts
        artifacts = [
            "YOUR RESPONSE (be helpful, check inventory, and be conversational):",
            "CUSTOMER'S CURRENT MESSAGE:",
            "CUSTOMER:",
            "Assistant:",
            "Response:",
            "AI:"
        ]
        
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        # Trim whitespace
        response = response.strip()
        
        # Remove excessive newlines
        while "\n\n\n" in response:
            response = response.replace("\n\n\n", "\n\n")
        
        # Ensure not empty
        if not response or len(response) < 5:
            return "I'm here to help! Could you rephrase your question? 😊"
        
        return response