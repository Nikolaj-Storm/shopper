# 🚀 SerpAPI Setup Guide

## What is SerpAPI?

SerpAPI is a real-time API that scrapes Google Shopping, Google Images, and other search engines. It's **much more reliable** than browser automation because it handles all the anti-bot protection for you!

## 📝 Setup Steps

### 1. Get Your Free SerpAPI Key

1. Go to **https://serpapi.com/**
2. Click "Sign Up" (free plan available)
3. Sign up with your email
4. Go to your Dashboard
5. Copy your API key

**Free Plan:** 100 searches/month (perfect for testing!)

### 2. Add Key to config.py

Open `backend/config.py` and replace the placeholder:

```python
SERPAPI_KEY = "your-actual-key-here"
```

### 3. Run the Script!

```bash
# Basic search
python clothingScraperSerpAPI.py "blue shirt"

# Search with more results
python clothingScraperSerpAPI.py "red dress" --max-results 20

# Include additional Google Images results
python clothingScraperSerpAPI.py "black jeans" --with-images
```

## 🎯 What You Get

Each product includes:
- ✅ **Title** - Product name
- ✅ **Price** - Current price
- ✅ **Rating** - Star rating (if available)
- ✅ **Reviews** - Number of reviews
- ✅ **Delivery** - Shipping info
- ✅ **Link** - Product page URL
- ✅ **Image URL** - Direct link to product image
- ✅ **Source** - Store name

## 📊 Output Files

The script creates:
1. **JSON file with all products** - `clothing_results_[query]_serpapi.json`
2. **JSON file with images** (if --with-images) - `clothing_images_[query]_serpapi.json`
3. **Gemini AI analysis** - Printed to console with recommendations

## 💡 Advantages Over Web Scraping

| Web Scraping | SerpAPI |
|--------------|---------|
| ❌ Often blocked by anti-bot | ✅ Always works |
| ❌ Slow (60+ seconds) | ✅ Fast (2-3 seconds) |
| ❌ Breaks when site changes | ✅ Always up-to-date |
| ❌ Demo data only | ✅ **Real product data** |
| ❌ Unreliable | ✅ Production-ready |

## 🔗 Useful Links

- **SerpAPI Dashboard:** https://serpapi.com/dashboard
- **API Documentation:** https://serpapi.com/google-shopping-api
- **Pricing:** https://serpapi.com/pricing

## 📌 Example Usage

```python
# In your own Python code
from clothingScraperSerpAPI import search_google_shopping

products = search_google_shopping("nike sneakers", max_results=10)

for product in products:
    print(f"{product['title']} - {product['price']}")
    print(f"Image: {product['image']}")
```

## ❓ Troubleshooting

**Error: No SerpAPI key found**
- Make sure you added your key to `secrets.py`
- Make sure the file is saved

**Error: Invalid API key**
- Check that you copied the full key from SerpAPI dashboard
- Make sure there are no extra spaces

**No results found**
- Try a different search query
- Make sure your SerpAPI account has remaining credits

