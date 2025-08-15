import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io
import json

def extract_items_from_receipt(image_bytes: bytes):
    """
    Accepts image bytes, processes with Gemini, and returns extracted items as JSON
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in .env file")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Load image from bytes
    img = Image.open(io.BytesIO(image_bytes))
    prompt = '''
You are an expert OCR and data extraction system. Analyze the provided receipt image and extract the information in the exact JSON structure shown below.

Required JSON structure:
{
  "restaurant_name": "string",
  "items": [
    {"name": "string", "price": 0.00, "is_tax_or_tip": false}
  ],
  "tax_amount": 0.00,
  "tip_amount": 0.00,
  "total_amount": 0.00
}

Instructions:
1. Return ONLY a valid JSON object that matches the structure above.
2. Do NOT include any code fences (e.g., ```json).
3. Do NOT include any additional explanation or text outside the JSON.
4. Use numbers (e.g., 18.99) for all monetary values (no currency symbols).
5. If a value is missing from the receipt, set it to 0 or an empty string (for restaurant_name).
6. The "items" array must contain each purchased item, with:
   - "name" as the item's name (string).
   - "price" as the item's price (float).
   - "is_tax_or_tip" as true for tax or tip lines, false for regular items.
7. Ensure the JSON is syntactically valid, with no trailing commas.

Return ONLY the JSON object.
    '''
    response = model.generate_content([prompt, img], timeout=30)
    if not response:
        raise RuntimeError("Empty response from Gemini API")
    raw_output = response.text.strip()
    # Remove code fences and extract JSON block
    if raw_output.startswith("```"):
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()
    # Find the first '{' and last '}' to extract the JSON object
    start = raw_output.find('{')
    end = raw_output.rfind('}')
    if start != -1 and end != -1:
        json_str = raw_output[start:end+1]
    else:
        json_str = raw_output
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini response is not valid JSON: {e}\nRaw output: {raw_output}")
    return parsed
