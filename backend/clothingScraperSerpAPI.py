from google import genai
import os
import sys
import json
from serpapi import GoogleSearch

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

def search_google_shopping(query, max_results=10):
    """
    Search Google Shopping using SerpAPI
    
    Args:
        query: Search query (e.g., "blue shirt", "red dress")
        max_results: Maximum number of results to return
    
    Returns:
        List of product dictionaries with title, price, link, image, and source
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
        print("   Get a free key at: https://serpapi.com/")
        return []

def search_google_images(query, max_results=10):
    """
    Search Google Images using SerpAPI to get high-quality product images
    
    Args:
        query: Search query
        max_results: Maximum number of image results
    
    Returns:
        List of image dictionaries
    """
    print(f"\n🖼️  Searching Google Images for '{query}' via SerpAPI...")
    
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": max_results
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        images = []
        image_results = results.get("images_results", [])
        
        print(f"   Found {len(image_results)} images!")
        
        for item in image_results[:max_results]:
            image = {
                "title": item.get("title", "N/A"),
                "link": item.get("link", "N/A"),
                "original": item.get("original", "N/A"),
                "thumbnail": item.get("thumbnail", "N/A"),
                "source": item.get("source", "N/A"),
            }
            images.append(image)
        
        return images
        
    except Exception as e:
        print(f"⚠️  Google Images search failed: {str(e)}")
        return []

def summarize_with_gemini(query, products):
    """
    Use Gemini to analyze and summarize the product results
    
    Args:
        query: Original search query
        products: List of product dictionaries
    
    Returns:
        Gemini's summary and analysis
    """
    if not products:
        return "No products found to analyze."
    
    # Format product data for Gemini
    products_text = f"Search Query: '{query}'\n\nProducts Found ({len(products)} items):\n\n"
    for i, product in enumerate(products, 1):
        products_text += f"{i}. Brand: {product['brand']}\n"
        products_text += f"   Product Link: {product['product_link']}\n"
        products_text += f"   Image URL: {product['image_url']}\n\n"
    
    prompt = f"""You are a fashion and shopping assistant. Analyze these clothing brands from Google Shopping and provide:

1. A brief overview of the brands found
2. Quality/reputation insights about these brands
3. Which brands are best known for quality vs budget options
4. Top 3 brand recommendations for this search query
5. Any shopping tips about these brands

{products_text}

Please provide a helpful, concise analysis focused on the brands."""
    
    print("\n🤖 Asking Gemini to analyze the brands...\n")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def main():
    """Main function to run the clothing scraper with SerpAPI"""
    if len(sys.argv) < 2:
        print("Usage: python clothingScraperSerpAPI.py <search_query> [--with-images] [--max-results N] [--analyze]")
        print()
        print("Examples:")
        print('  python clothingScraperSerpAPI.py "blue shirt"')
        print('  python clothingScraperSerpAPI.py "red dress" --with-images')
        print('  python clothingScraperSerpAPI.py "black jeans" --max-results 20 --analyze')
        print()
        print("Options:")
        print("  --with-images      Also search Google Images for additional product photos")
        print("  --max-results N    Maximum number of results (default: 10)")
        print("  --analyze          Enable Gemini AI brand analysis")
        print()
        print("Setup:")
        print("  1. Get a free SerpAPI key at: https://serpapi.com/")
        print("  2. Add SERPAPI_KEY = 'your-key-here' to secrets.py")
        print()
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    with_images = '--with-images' in args
    analyze = '--analyze' in args
    
    # Get max results
    max_results = 10
    if '--max-results' in args:
        idx = args.index('--max-results')
        if idx + 1 < len(args):
            try:
                max_results = int(args[idx + 1])
            except ValueError:
                print("⚠️  Invalid max-results value, using default: 10")
    
    # Remove flags from query
    query = " ".join([arg for arg in args if not arg.startswith('--') and not arg.isdigit()])
    
    print(f"\n{'='*70}")
    print(f"🛍️  CLOTHING SEARCH WITH SERPAPI: {query}")
    print(f"{'='*70}\n")
    
    # Search for products
    products = search_google_shopping(query, max_results)
    
    if not products:
        print("\n❌ No products found. Try a different search query.")
        return
    
    print(f"\n{'='*70}")
    print(f"✅ Found {len(products)} products!")
    print(f"{'='*70}\n")
    
    # Display results - simplified format
    for i, product in enumerate(products, 1):
        print(f"{i}. Brand: {product['brand']}")
        print(f"   🔗 Product Link: {product['product_link']}")
        print(f"   📸 Image URL: {product['image_url']}")
        print()
    
    # Save to JSON
    output_file = f"clothing_results_{query.replace(' ', '_')}_serpapi.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"💾 Product results saved to: {output_file}\n")
    
    # Search for additional images if requested
    if with_images:
        images = search_google_images(query, max_results)
        if images:
            images_file = f"clothing_images_{query.replace(' ', '_')}_serpapi.json"
            with open(images_file, 'w', encoding='utf-8') as f:
                json.dump(images, f, indent=2, ensure_ascii=False)
            print(f"💾 Image results saved to: {images_file}\n")
            
            print(f"\n{'='*70}")
            print(f"🖼️  Additional Product Images:")
            print(f"{'='*70}\n")
            for i, img in enumerate(images[:5], 1):  # Show first 5
                print(f"{i}. {img['title']}")
                print(f"   Original: {img['original']}")
                print(f"   Thumbnail: {img['thumbnail']}")
                print(f"   Source: {img['source']}")
                print()
    
    # Get Gemini summary if requested
    if analyze:
        print(f"{'='*70}")
        summary = summarize_with_gemini(query, products)
        print(summary)
        print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

