# Stylo.AI Backend API

AI-powered virtual outfit generator that transforms natural language prompts into realistic outfit visualizations.

## 🚀 Features

- **Natural Language Processing**: Converts user prompts into search queries using Gemini AI
- **Product Search**: Finds real clothing products via SerpAPI Google Shopping
- **AI Outfit Generation**: Creates realistic visualizations using Gemini Vision
- **RESTful API**: Clean, documented endpoints for easy integration
- **Image Management**: Store, retrieve, and delete generated outfits

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API Key
- SerpAPI Key (free tier: 100 searches/month)

## ⚙️ Installation

1. **Clone the repository**
```bash
git clone <your-repo>
cd backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up API keys**

Create `config.py` in the backend directory:
```python
GEMINI_API_KEY = "your-gemini-api-key-here"
SERPAPI_KEY = "your-serpapi-key-here"
```

4. **Set up reference image**

Place your reference image at:
```
C:\Users\Rahul\Stylo.ai\Images\Rahul.jpg
```

Or update the path in `api.py` (line 315)

## 🏃 Running the Server

```bash
python api.py
```

The server will start at `http://localhost:8000`

## 📡 API Endpoints

### **POST** `/api/generate-outfit`
Generate outfit visualizations from natural language

**Request:**
```json
{
  "prompt": "I need a formal navy blue suit for a wedding",
  "reference_image": "path/to/your/image.jpg",  // optional
  "max_results": 2  // optional, default: 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated 2 outfit visualization(s)",
  "user_query": "I need a formal navy blue suit for a wedding",
  "parsed_query": "men's navy blue suit",
  "clothing_type": "suit",
  "style": "formal",
  "gender": "men",
  "products": [
    {
      "brand": "Macy's",
      "image_url": "https://...",
      "product_link": "https://..."
    }
  ],
  "generated_images": [
    "outfit_20250104_143052_1_Macys.png"
  ],
  "timestamp": "20250104_143052"
}
```

### **GET** `/api/image/{filename}`
Retrieve a generated outfit image

### **GET** `/api/images`
List all generated outfit images

### **DELETE** `/api/image/{filename}`
Delete a generated outfit image

### **GET** `/health`
Health check endpoint

### **GET** `/docs`
Interactive API documentation (Swagger UI)

## 🧪 Example Usage

### cURL
```bash
curl -X POST "http://localhost:8000/api/generate-outfit" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I need a casual blue shirt for work",
    "max_results": 2
  }'
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate-outfit",
    json={
        "prompt": "I want a red hoodie for the gym",
        "max_results": 2
    }
)

data = response.json()
print(f"Generated {len(data['generated_images'])} outfits!")
```

### JavaScript
```javascript
fetch('http://localhost:8000/api/generate-outfit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'I need a formal black tuxedo',
    max_results: 2
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## 📁 Project Structure

```
backend/
├── api.py                    # FastAPI server
├── styloAI.py               # Core AI logic (parsing, search, generation)
├── clothingScraperSerpAPI.py # SerpAPI integration
├── imageGen.py              # Image generation utilities
├── config.py                # API keys (create this)
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── clothing_images/        # Generated images (auto-created)
└── README.md               # This file
```

## 🔧 Configuration

### Change Reference Image
Update in `api.py` or pass in request:
```python
reference_image = r"C:\path\to\your\image.jpg"
```

### Change Output Directory
Update in `styloAI.py` (line 391):
```python
output_dir = r"C:\path\to\output\folder"
```

### Adjust Number of Products
Default is 2 products. Change via API request or in `api.py`:
```python
max_results = 5
```

## 🐛 Troubleshooting

### Server won't start
- Verify port 8000 is available
- Check all dependencies: `pip install -r requirements.txt`
- Ensure `config.py` exists with valid API keys

### No images generated
- Verify Gemini API key is valid
- Verify SerpAPI key is valid and has credits
- Check reference image path exists
- Review server logs for errors

### CORS errors
- CORS is enabled for all origins (`*`)
- Update `allow_origins` in `api.py` for production

### Clothing not changing in images
- This is an AI model limitation
- Try running the same query again
- Simpler clothing items work better
- Use clear, simple prompts

## 🚀 Deployment

### Production Checklist
1. Update CORS origins to specific domains
2. Use environment variables for API keys
3. Add authentication/rate limiting
4. Use production ASGI server (Gunicorn/Uvicorn)
5. Set up HTTPS
6. Configure logging
7. Set up monitoring

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 API Keys Setup

### Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to `config.py`

### Get SerpAPI Key
1. Go to [SerpAPI](https://serpapi.com/)
2. Sign up (free tier: 100 searches/month)
3. Copy your API key
4. Add to `config.py`

## 💡 Tips for Better Results

### Prompt Examples
- "I need a formal navy blue suit for a wedding"
- "Looking for a casual white t-shirt"
- "I want a red hoodie for gym workouts"
- "Professional gray blazer for business meetings"

### For Best Results
- Use clear, specific descriptions
- Include occasion/style (formal, casual, professional)
- Mention colors explicitly
- Simple clothing items work better than complex outfits

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines]

## 📧 Contact

[Add contact information]

