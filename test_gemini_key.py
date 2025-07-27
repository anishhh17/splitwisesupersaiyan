#!/usr/bin/env python3
"""
Test script to verify Gemini can actually process images
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json

def create_sample_receipt():
    """Create a simple sample receipt image for testing"""
    # Create a simple receipt image
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        try:
            font_large = ImageFont.truetype("arial.ttf", 20)
            font_medium = ImageFont.truetype("arial.ttf", 16) 
            font_small = ImageFont.truetype("arial.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Draw receipt content
    y = 20
    draw.text((50, y), "MARIO'S PIZZA", fill='black', font=font_large)
    y += 40
    draw.text((50, y), "123 Main Street", fill='black', font=font_small)
    y += 20
    draw.text((50, y), "Date: 2025-01-27", fill='black', font=font_small)
    y += 40
    
    # Items
    draw.text((50, y), "Margherita Pizza    $18.99", fill='black', font=font_medium)
    y += 25
    draw.text((50, y), "Garlic Bread        $6.50", fill='black', font=font_medium)
    y += 25
    draw.text((50, y), "Coca Cola           $3.99", fill='black', font=font_medium)
    y += 40
    
    # Totals
    draw.text((50, y), "Subtotal:          $29.48", fill='black', font=font_medium)
    y += 25
    draw.text((50, y), "Tax (8.5%):        $2.51", fill='black', font=font_medium)
    y += 25
    draw.text((50, y), "Tip (18%):         $5.76", fill='black', font=font_medium)
    y += 30
    draw.text((50, y), "TOTAL:            $37.75", fill='black', font=font_large)
    
    return img

def test_image_processing():
    """Test Gemini's image processing capabilities with a sample receipt"""
    
    print("🧪 Testing Gemini Image Processing")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ No GEMINI_API_KEY found in .env file")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create a sample receipt
        print("📄 Creating sample receipt image...")
        receipt_img = create_sample_receipt()
        
        # Save for reference
        receipt_img.save("test_receipt.png")
        print("💾 Saved test receipt as 'test_receipt.png'")
        
        # Strict JSON prompt
        prompt = """
        Analyze this receipt image and extract the following information in JSON format:
        
        {
          "restaurant_name": "string",
          "items": [
            {"name": "string", "price": 0.00, "is_tax_or_tip": false}
          ],
          "tax_amount": 0.00,
          "tip_amount": 0.00,
          "total_amount": 0.00
        }
        
        RULES:
        - Return ONLY valid JSON.
        - Do not include code fences, explanations, or text outside the JSON.
        - Use proper numbers for price fields (e.g., 18.99).
        """
        
        print("🔍 Analyzing receipt with Gemini...")
        response = model.generate_content([prompt, receipt_img])
        raw_output = response.text.strip()
        
        # Remove code fences (```json ... ```)
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1].replace("json", "", 1).strip()
        
        print("📥 Gemini Response:")
        print("-" * 30)
        print(raw_output)
        print("-" * 30)
        
       
        try:
            parsed = json.loads(raw_output)
            print("✅ Response is valid JSON!")
            print(f"   Restaurant: {parsed.get('restaurant_name', 'N/A')}")
            print(f"   Items found: {len(parsed.get('items', []))}")
            print(f"   Total: ${parsed.get('total_amount', 0)}")
        except json.JSONDecodeError as e:
            print(f"⚠️  Response is not valid JSON: {e}")
            return False
        
        print("\n🎉 SUCCESS: Gemini can process images and return valid JSON!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

# def test_with_uploaded_image(image_path):
#     """Test with a user-provided image"""
    
#     if not os.path.exists(image_path):
#         print(f"❌ Image file not found: {image_path}")
#         return False
    
#     print(f"🖼️  Testing with uploaded image: {image_path}")
#     print("=" * 50)
    
#     load_dotenv()
#     api_key = os.getenv("GEMINI_API_KEY")
    
#     if not api_key:
#         print("❌ No GEMINI_API_KEY found")
#         return False
    
#     try:
#         genai.configure(api_key=api_key)
#         model = genai.GenerativeModel('gemini-1.5-flash')
        
#         # Load image
#         img = Image.open(image_path)
        
#         prompt = "What do you see in this image? Describe it in detail."
        
#         response = model.generate_content([prompt, img])
        
#         print("📤 Sent image for analysis")
#         print("📥 Gemini Response:")
#         print("-" * 30)
#         print(response.text)
#         print("-" * 30)
        
#         return True
        
#     except Exception as e:
#         print(f"❌ ERROR: {str(e)}")
#         return False

if __name__ == "__main__":
    print("🚀 Gemini Image Processing Tester")
    print("=" * 50)
    
    # Test with generated sample receipt
    success = test_image_processing()
    
    # if success:
    #     print("\n✅ Your Gemini API is ready for bill OCR!")
    #     print("🔧 You can now proceed with your bill splitting app")
        
    #     # Offer to test with user image
    #     user_image = input("\n📁 Do you have a receipt image to test? Enter path (or press Enter to skip): ").strip()
    #     if user_image:
    #         test_with_uploaded_image(user_image)
    # else:
    #     print("\n❌ Image processing test failed")
    #     print("Check your API key and try again")
    
    print("\n" + "=" * 50)
    print("Test completed!")