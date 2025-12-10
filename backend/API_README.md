# Stylo.AI API Documentation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python api.py
```

The server will start at: **http://localhost:8000**

### 3. Open Web Interface
Open your browser and go to: **http://localhost:8000**

Or view API docs at: **http://localhost:8000/docs**

## 📡 API Endpoints

### POST `/api/generate-outfit`
Generate outfit visualizations from natural language

**Request Body:**
```json
{
  "prompt": "I need a formal navy blue suit for a wedding",
  "reference_image": "C:\\Users\\Rahul\\Stylo.ai\\Images\\Rahul.jpg",
  "max_results": 2
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

### GET `/api/image/{filename}`
Retrieve a generated outfit image

**Example:**
```
GET /api/image/outfit_20250104_143052_1_Macys.png
```

### GET `/api/images`
List all generated outfit images

**Response:**
```json
{
  "total": 5,
  "images": [
    "outfit_20250104_143052_1_Macys.png",
    "outfit_20250104_142830_2_HM.png"
  ]
}
```

### DELETE `/api/image/{filename}`
Delete a generated outfit image

### GET `/health`
Health check endpoint

## 🧪 Testing with cURL

### Generate Outfit
```bash
curl -X POST "http://localhost:8000/api/generate-outfit" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I need a casual blue shirt for work",
    "max_results": 2
  }'
```

### Get Image
```bash
curl "http://localhost:8000/api/image/outfit_20250104_143052_1_Macys.png" \
  --output outfit.png
```

## 🎨 Web Interface

The web interface at `http://localhost:8000` provides:
- Natural language input for outfit requests
- Real-time generation progress
- Display of generated outfit visualizations
- Product information and links
- Example prompts to try

## 📁 File Structure

```
backend/
├── api.py                 # FastAPI server
├── styloAI.py            # Core AI logic
├── requirements.txt       # Dependencies
├── static/
│   └── index.html        # Web interface
└── clothing_images/      # Generated images (auto-created)
```

## 🔧 Configuration

### Change Reference Image
Default: `C:\Users\Rahul\Stylo.ai\Images\Rahul.jpg`

To use a different image, pass it in the request:
```json
{
  "prompt": "blue shirt",
  "reference_image": "path/to/your/image.jpg"
}
```

### Change Number of Results
Default: 2 products

```json
{
  "prompt": "blue shirt",
  "max_results": 5
}
```

### Output Directory
Generated images are saved to:
`C:\Users\Rahul\Stylo.ai\backend\clothing_images\`

## 🐛 Troubleshooting

### Server won't start
- Make sure port 8000 is not in use
- Check all dependencies are installed: `pip install -r requirements.txt`

### Images not generating
- Verify your Gemini API key in `config.py`
- Verify your SerpAPI key in `config.py`
- Check the reference image path exists

### CORS errors
- Make sure the API server is running
- Check browser console for specific errors

## 📝 Example Prompts

- "I am looking for an outfit for a formal event for men. Like a tuxedo"
- "I need a casual blue shirt for work"
- "Looking for Nike sneakers for running"
- "I want a red hoodie for the gym"
- "Professional navy blue suit for business meetings"

## 🚀 Production Deployment

For production:
1. Change CORS origins in `api.py` to specific domains
2. Use environment variables for API keys
3. Add authentication if needed
4. Use a production ASGI server like Gunicorn
5. Set up HTTPS
6. Configure proper logging

