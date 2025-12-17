"""
Quick test script to verify AI handler is working
Run this to test all three options: LM Studio, HuggingFace, and Fallback
"""

from ai_handler import MetaAIHandler

def test_ai():
    print("🧪 Testing Ejide Pharmacy AI Handler")
    print("=" * 50)
    
    # Initialize handler
    handler = MetaAIHandler()
    
    # Sample inventory
    inventory = [
        {"drug_name": "paracetamol", "quantity": 150, "price": 500, "category": "fever/pain"},
        {"drug_name": "chloroquine", "quantity": 60, "price": 800, "category": "malaria"},
        {"drug_name": "ibuprofen", "quantity": 120, "price": 600, "category": "pain"},
    ]
    
    # Sample customer history
    customer_history = {
        "conversations": [],
        "purchases": []
    }
    
    # Test messages
    test_messages = [
        "Hello",
        "Do you have paracetamol?",
        "I need something for malaria",
        "How much is ibuprofen?",
    ]
    
    print("\n🔍 Current Configuration:")
    print(f"   LM Studio: {'✅ Enabled' if handler.use_groq else '❌ Disabled'}")
    print(f"   HuggingFace: {'✅ Enabled' if handler.use_huggingface else '❌ Disabled'}")
    print(f"   HF Token: {'✅ Set' if handler.hf_token else '❌ Not Set'}")
    print(f"   Fallback: ✅ Always Available")
    
    print("\n" + "=" * 50)
    print("Testing responses...")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 Test {i}: '{message}'")
        print("-" * 50)
        
        try:
            response = handler.generate_response(
                message=message,
                customer_history=customer_history,
                inventory=inventory,
                is_admin=False
            )
            
            print(f"✅ Response received:")
            print(f"{response}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n" + "=" * 50)
    print("✅ Testing complete!")
    print("=" * 50)
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not handler.use_groq and not (handler.use_huggingface and handler.hf_token):
        print("   ⚠️  Currently using ONLY fallback responses")
        print("   📝 To enable AI:")
        print("      Option 1: Start LM Studio → Set use_groq = True")
        print("      Option 2: Add HF_TOKEN to .env file")
    elif handler.use_groq:
        print("   🚀 LM Studio enabled - should be fastest!")
        print("   💡 Make sure LM Studio server is running on port 1234")
    elif handler.use_huggingface:
        print("   🌐 HuggingFace enabled")
        print("   ⏱️  First request may take 20-60 seconds (model loading)")
        print("   💡 Subsequent requests will be faster")

if __name__ == "__main__":
    test_ai()