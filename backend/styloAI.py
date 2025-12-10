from google import genai
import os
import sys
import json
from serpapi import GoogleSearch
from PIL import Image
from io import BytesIO
import requests

# Import API keys from config file
try:
    from config import GEMINI_API_KEY, SERPAPI_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    SERPAPI_KEY = os.getenv('SERPAPI_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("No Gemini API key found. Please add GEMINI_API_KEY to config.py")
    if not SERPAPI_KEY:
        raise ValueError("No SerpAPI key found. Please add SERPAPI_KEY to config.py")

os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
client = genai.Client(api_key=GEMINI_API_KEY)

def parse_natural_language_query(user_prompt):
    """
    Use Gemini to parse natural language into search parameters
    
    Args:
        user_prompt: Natural language query from user
        
    Returns:
        Dictionary with search_query and other relevant params
    """
    print(f"\n🤖 Analyzing your request with Gemini...")
    print(f"   Input: \"{user_prompt}\"")
    
    parsing_prompt = f"""You are a fashion shopping assistant. Analyze this user's request and extract the key search terms for finding clothing items. you are allowed to infer from sentiment, which key search terms would be relevant. but remember, user specified key information is allways to be prioriticed.

User's Request: "{user_prompt}"

Extract and return a JSON object with these SPECIFIC fields:
1. "clothing_type" - CRITICAL: The specific type of clothing (e.g., "shirt", "dress", "tuxedo", "sneakers", "suit", "jacket")
2. "color" - CRITICAL: The specific color mentioned (e.g., "blue", "red", "black", "navy blue", "white") - if no color mentioned, use "any"
3. "brand" - CRITICAL: Any specific brand mentioned (e.g., "Nike", "Gucci", "Gap", "H&M") - if no brand mentioned, use "any"
4. "style" - The style or occasion (e.g., "formal", "casual", "athletic", "business")
5. "gender" - Target gender if mentioned ("men", "women", "unisex", or "not specified")
6. "search_query" - The best complete search term for Google Shopping combining the above (2-5 words)
7. "additional_details" - Any other important context

IMPORTANT: Extract brand, color, and clothing_type as SEPARATE fields. These will be used for filtering.

You are allowed to infer "clothing_type" "color""brand""style""gender""search_query" from the sentiment of the promt, and general logic (ex. if user says "i wwant an outfit that makes me look like james bond", you might infer a tailored suit, omega watch and such)

Examples:
Input: "I am looking for an outfit for a formal event for men. Like a tuxedo"
Output: {{"clothing_type": "tuxedo", "color": "black", "brand": "any", "style": "formal", "gender": "men", "search_query": "men's black tuxedo", "additional_details": "formal event"}}

Input: "I need a casual blue shirt for work"
Output: {{"clothing_type": "shirt", "color": "blue", "brand": "any", "style": "business casual", "gender": "not specified", "search_query": "blue dress shirt", "additional_details": "work appropriate"}}

Input: "red Nike hoodie"
Output: {{"clothing_type": "hoodie", "color": "red", "brand": "Nike", "style": "casual", "gender": "unisex", "search_query": "red Nike hoodie", "additional_details": "none"}}

Input: "navy blue suit"
Output: {{"clothing_type": "suit", "color": "navy blue", "brand": "any", "style": "formal", "gender": "not specified", "search_query": "navy blue suit", "additional_details": "none"}}

Input: "Gucci black leather jacket"
Output: {{"clothing_type": "jacket", "color": "black", "brand": "Gucci", "style": "luxury", "gender": "unisex", "search_query": "Gucci black leather jacket", "additional_details": "leather material"}}

Now analyze the user's request and provide ONLY the JSON object, no other text."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=parsing_prompt
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        parsed_data = json.loads(response_text)
        
        print(f"   ✅ Parsed query: \"{parsed_data.get('search_query', user_prompt)}\"")
        print(f"   👕 Clothing Type: {parsed_data.get('clothing_type', 'N/A')}")
        print(f"   🎨 Color: {parsed_data.get('color', 'N/A')}")
        print(f"   🏷️  Brand: {parsed_data.get('brand', 'N/A')}")
        print(f"   ✨ Style: {parsed_data.get('style', 'N/A')}")
        print(f"   👤 Gender: {parsed_data.get('gender', 'N/A')}")
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        print(f"   ⚠️  Could not parse Gemini response, using original query")
        print(f"   Raw response: {response_text}")
        return {
            "search_query": user_prompt,
            "clothing_type": "clothing",
            "color": "any",
            "brand": "any",
            "style": "general",
            "gender": "not specified",
            "additional_details": "none"
        }
    except Exception as e:
        print(f"   ⚠️  Error parsing query: {str(e)}")
        return {
            "search_query": user_prompt,
            "clothing_type": "clothing",
            "color": "any",
            "brand": "any",
            "style": "general",
            "gender": "not specified",
            "additional_details": "none"
        }

def search_clothing(query, max_results=10):
    """
    Search Google Shopping using SerpAPI for clothing items
    
    Args:
        query: Search query (e.g., "blue shirt", "red dress")
        max_results: Maximum number of results to return
    
    Returns:
        List of product dictionaries with brand, image_url, and product_link
    """
    print(f"🔍 Searching Google Shopping for '{query}' via SerpAPI...")
    
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": max_results
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        products = []
        shopping_results = results.get("shopping_results", [])
        
        print(f"   Found {len(shopping_results)} products!")
        
        for item in shopping_results[:max_results]:
            product = {
                "brand": item.get("source", "Unknown"),
                "image_url": item.get("thumbnail", "N/A"),
                "product_link": item.get("product_link", "N/A"),
            }
            products.append(product)
            print(f"   ✓ {product['brand']}")
        
        return products
        
    except Exception as e:
        print(f"❌ SerpAPI search failed: {str(e)}")
        print("\n💡 Make sure you have a valid SerpAPI key in secrets.py")
        return []

def download_image(url, save_path):
    """
    Download an image from URL
    
    Args:
        url: Image URL
        save_path: Path to save the image
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            return True
    except Exception as e:
        print(f"   ✗ Failed to download image: {str(e)}")
    return False

def generate_outfit_visualization(user_image_path, clothing_image_url, output_path, product_info=None):
    """
    Generate an image of the user wearing the clothing using Gemini
    
    Args:
        user_image_path: Path to user's reference image
        clothing_image_url: URL or path to clothing image
        output_path: Where to save the generated image
        product_info: Optional dict with brand and product info
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Load user image
        print(f"\n🎨 Generating outfit visualization...")
        user_image = Image.open(user_image_path)
        
        # Download or load clothing image
        if clothing_image_url.startswith('http'):
            print(f"   Downloading clothing image...")
            response = requests.get(clothing_image_url, timeout=10)
            clothing_image = Image.open(BytesIO(response.content))
        else:
            clothing_image = Image.open(clothing_image_url)
        
        # Create prompt - Using a more directive approach with visual editing language
        if product_info:
            prompt = f"""CLOTHING SWAP TASK - This is a photo editing operation where you REPLACE clothing.

SOURCE: First image (person's reference photo)
CLOTHING REFERENCE: Second image (product photo showing the clothing item)
PRODUCT: {product_info.get('brand', 'Unknown brand')}

YOUR TASK IS TO PERFORM A VIRTUAL TRY-ON / CLOTHING REPLACEMENT:

STEP 1 - IDENTIFY THE CLOTHING:
Look at the second image and identify the specific clothing item (shirt, jacket, dress, suit, hoodie, etc.). If there's a model wearing it, focus ONLY on the garment itself - ignore the model's body, face, and pose.

STEP 2 - REMOVE OLD CLOTHING:
Digitally remove or replace the clothing that the person is currently wearing in the first image.

STEP 3 - APPLY NEW CLOTHING:
Place the clothing from the second image onto the person in the first image. This is like Photoshop's clothing swap - the NEW clothing must now be on their body:
- Match the exact color, pattern, texture, and style from the second image
- Make it fit their body shape and pose naturally
- Blend it seamlessly so it looks like they're actually wearing it
- Ensure proper shadows, wrinkles, and fabric draping for realism

STEP 4 - PRESERVE EVERYTHING ELSE:
Keep ABSOLUTELY EVERYTHING else from the first image unchanged:
- Same background
- Same pose and body position
- Same face and features
- Same camera angle
- Same lighting (just adapt it to show the new clothing)

VERIFICATION - The output must clearly show:
✓ The person IS wearing the clothing from the second image
✓ The clothing color/style matches the second image
✓ Everything else (background, face, pose) matches the first image
✗ DO NOT return the original first image unchanged
✗ DO NOT keep the old clothing

Think of this as: "Take the person from image 1, dress them in the clothing from image 2, keep everything else from image 1."

Generate this clothing swap now."""
        else:
            prompt = """CLOTHING SWAP TASK: Replace the person's clothing with the clothing from the second image.

STEPS:
1. Identify the clothing item in the second image
2. Remove the person's current clothing in the first image  
3. Put the new clothing on the person
4. Keep everything else (background, face, pose) the same

The person MUST be wearing the NEW clothing in the output. This is a virtual try-on."""
        
        print(f"   Processing with Gemini...")
        
        # Generate the image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, user_image, clothing_image],
        )
        
        # Process the response
        image_saved = False
        text_response = ""
        
        # Check if response has candidates
        if not response or not hasattr(response, 'candidates') or not response.candidates:
            return {
                "success": False,
                "message": "Gemini returned no response. The model may not support image generation.",
                "text_response": ""
            }
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_response += part.text
            elif part.inline_data is not None:
                generated_image = Image.open(BytesIO(part.inline_data.data))
                generated_image.save(output_path)
                print(f"   ✅ Image saved as '{output_path}'")
                image_saved = True
        
        if image_saved:
            print(f"   💡 Tip: If clothing didn't change, try again - AI models can be inconsistent")
            return {
                "success": True,
                "message": f"Image saved to {output_path}",
                "text_response": text_response
            }
        else:
            return {
                "success": False,
                "message": "No image data returned",
                "text_response": text_response
            }
            
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def main():
    """Main function to search for clothes and generate outfit visualizations"""
    if len(sys.argv) < 2:
        print("Usage: python styloAI.py \"<natural_language_query>\" [--reference <path>] [--max-results N] [--generate-all] [--no-parse]")
        print()
        print("Examples:")
        print('  python styloAI.py "I am looking for an outfit for a formal event for men. Like a tuxedo"')
        print('  python styloAI.py "I need a casual blue shirt for work"')
        print('  python styloAI.py "red hoodie" --max-results 5 --generate-all')
        print('  python styloAI.py "blue shirt" --no-parse  # Skip AI parsing, use direct search')
        print()
        print("Options:")
        print("  --reference PATH   Path to your reference image (default: ../Images/Rahul.jpg)")
        print("  --max-results N    Maximum number of products to search (default: 2)")
        print("  --generate-all     Generate visualizations for ALL products (default: generates all found)")
        print("  --no-parse         Skip AI parsing and use query directly")
        print()
        print("Generated images will be saved to: C:\\Users\\Rahul\\Stylo.ai\\backend\\clothing_images\\")
        print()
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    
    # Get max results
    max_results = 2  # Default to 2 sources
    if '--max-results' in args:
        idx = args.index('--max-results')
        if idx + 1 < len(args):
            try:
                max_results = int(args[idx + 1])
            except ValueError:
                print("⚠️  Invalid max-results value, using default: 2")
    
    # Get reference image
    reference_image = r"./Images/Rahul.jpg"
    if '--reference' in args:
        idx = args.index('--reference')
        if idx + 1 < len(args):
            reference_image = args[idx + 1]
    
    # Check if reference image exists
    if not os.path.exists(reference_image):
        print(f"❌ Reference image not found: {reference_image}")
        print("Please provide a valid reference image path with --reference")
        sys.exit(1)
    
    generate_all = '--generate-all' in args
    skip_parsing = '--no-parse' in args
    
    # Remove flags from query
    user_query = " ".join([arg for arg in args if not arg.startswith('--') and not arg.isdigit()])
    
    # Parse natural language query with Gemini (unless --no-parse is used)
    if skip_parsing:
        query = user_query
        parsed_info = None
    else:
        parsed_info = parse_natural_language_query(user_query)
        query = parsed_info.get('search_query', user_query)
    
    print(f"\n{'='*70}")
    print(f"👔 STYLO.AI - Virtual Outfit Generator")
    print(f"{'='*70}")
    if parsed_info and not skip_parsing:
        print(f"Original Request: {user_query}")
        print(f"Parsed Search: {query}")
        print(f"Clothing Type: {parsed_info.get('clothing_type', 'N/A')}")
        print(f"Style: {parsed_info.get('style', 'N/A')}")
        print(f"Gender: {parsed_info.get('gender', 'N/A')}")
    else:
        print(f"Search: {query}")
    print(f"Reference Image: {reference_image}")
    print(f"{'='*70}\n")
    
    # Search for products
    products = search_clothing(query, max_results)
    
    if not products:
        print("\n❌ No products found. Try a different search query.")
        return
    
    print(f"\n{'='*70}")
    print(f"✅ Found {len(products)} products!")
    print(f"{'='*70}\n")
    
    # Display results
    for i, product in enumerate(products, 1):
        print(f"{i}. Brand: {product['brand']}")
        print(f"   🔗 Product Link: {product['product_link']}")
        print(f"   📸 Image URL: {product['image_url']}")
        print()
    
    # Save search results to JSON
    output_file = f"search_results_{query.replace(' ', '_')}.json"
    output_data = {
        "user_query": user_query,
        "parsed_info": parsed_info,
        "search_query_used": query,
        "products": products
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Search results saved to: {output_file}\n")
    
    # Generate outfit visualizations
    print(f"{'='*70}")
    print(f"🎨 Generating Outfit Visualizations")
    print(f"{'='*70}\n")
    
    # Create output directory
    output_dir = r"C:\Users\Rahul\Stylo.ai\backend\clothing_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created directory: {output_dir}\n")
    
    # Determine how many to generate (default to all products since we only fetch 2)
    num_to_generate = len(products) if generate_all else len(products)
    
    generated_images = []
    
    for i in range(num_to_generate):
        product = products[i]
        print(f"[{i+1}/{num_to_generate}] Generating outfit with {product['brand']}...")
        
        filename = f"generated_outfit_{query.replace(' ', '_')}_{i+1}_{product['brand'].replace(' ', '_')}.png"
        output_path = os.path.join(output_dir, filename)
        
        result = generate_outfit_visualization(
            reference_image,
            product['image_url'],
            output_path,
            product_info=product
        )
        
        if result['success']:
            generated_images.append(output_path)
            print(f"   ✅ Success!\n")
        else:
            print(f"   ❌ Failed: {result['message']}\n")
    
    # Summary
    print(f"{'='*70}")
    print(f"✨ SUMMARY")
    print(f"{'='*70}")
    print(f"Products Found: {len(products)}")
    print(f"Outfits Generated: {len(generated_images)}/{num_to_generate}")
    print(f"\n📁 All images saved to: {output_dir}")
    print(f"\nGenerated Images:")
    for img in generated_images:
        print(f"  • {os.path.basename(img)}")
    print(f"\n💡 Tip: Use --max-results N to search more products!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

