from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64

try:
    from config import OUTPUT_IMAGE_DIR, REFERENCE_IMAGE_PATH, GEMINI_API_KEY
except ImportError:
    OUTPUT_IMAGE_DIR = "./generated_images"
    REFERENCE_IMAGE_PATH = None
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Import our Stylo.AI functions
from styloAI import (
    parse_natural_language_query,
    search_clothing,
    generate_outfit_visualization
)

# Import Gemini for reference image generation
from google import genai
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="Stylo.AI API",
    version="1.0.0",
    description="Virtual Outfit Generator API - Natural language to outfit visualizations"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class GenerateOutfitRequest(BaseModel):
    prompt: str
    reference_image: Optional[str] = None  # Will default to config value or last generated if None
    max_results: Optional[int] = 2

class ProductInfo(BaseModel):
    brand: str
    image_url: str
    product_link: str

class GenerateOutfitResponse(BaseModel):
    success: bool
    message: str
    user_query: str
    parsed_query: str
    clothing_type: Optional[str]
    color: Optional[str]
    brand: Optional[str]
    style: Optional[str]
    gender: Optional[str]
    products: List[ProductInfo]
    generated_images: List[str]
    timestamp: str
    latest_image: str  # New field to return the latest generated image

class SearchProductsRequest(BaseModel):
    prompt: str
    max_results: Optional[int] = 10

class SearchProductsResponse(BaseModel):
    success: bool
    user_query: str
    parsed_query: str
    clothing_type: Optional[str]
    color: Optional[str]
    brand: Optional[str]
    style: Optional[str]
    gender: Optional[str]
    products: List[ProductInfo]

class GenerateTryonRequest(BaseModel):
    product: ProductInfo
    reference_image: Optional[str] = None

class GenerateTryonResponse(BaseModel):
    success: bool
    message: str
    generated_image: str
    timestamp: str

class GenerateReferenceResponse(BaseModel):
    success: bool
    message: str
    reference_image: str
    timestamp: str

@app.get("/")
async def root():
    """API root - provides information about available endpoints"""
    return {
        "service": "Stylo.AI API",
        "version": "1.0.0",
        "status": "online",
        "description": "Virtual Outfit Generator - Natural language to outfit visualizations",
        "endpoints": {
            "GET /api/config": "Get Supabase client configuration for the frontend",
            "POST /api/generate-outfit": "Generate outfit visualizations from natural language",
            "POST /api/generate-reference": "Convert user photo to clean reference image",
            "GET /api/image/{filename}": "Retrieve a generated outfit image",
            "GET /api/images": "List all generated images",
            "DELETE /api/image/{filename}": "Delete a generated image",
            "GET /health": "Health check endpoint",
            "GET /docs": "Interactive API documentation"
        }
    }

@app.get("/api/config")
async def get_config():
    """Return public Supabase client configuration for the frontend"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_anon_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration not set in environment variables"
        )
    return {
        "supabase_url": supabase_url,
        "supabase_anon_key": supabase_anon_key
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Stylo.AI API",
        "version": "1.0.0"
    }

@app.post("/api/generate-outfit", response_model=GenerateOutfitResponse)
async def generate_outfit(request: GenerateOutfitRequest):
    """
    Generate outfit visualizations based on natural language prompt
 
    Args:
        prompt: Natural language description (e.g., "I need a formal suit for a wedding")
        reference_image: Path to user's reference image (optional)
        max_results: Number of products to search (default: 2)
 
    Returns:
        Generated outfit information and image paths
    """
    try:
        print(f"\n🎨 Processing request: {request.prompt}")
        # Resolve reference image path
        if request.reference_image:
            # Strip directory traversal and resolve inside generated_images dir
            cleaned_reference = Path(request.reference_image).name
            base_dir = Path(__file__).resolve().parent
            reference_image = str((base_dir / OUTPUT_IMAGE_DIR / cleaned_reference).resolve())
            print(f"Resolved reference image path: {reference_image}")
        elif REFERENCE_IMAGE_PATH and os.path.exists(REFERENCE_IMAGE_PATH):
            reference_image = REFERENCE_IMAGE_PATH
        else:
            raise HTTPException(
                status_code=400,
                detail="No reference image available. Please upload a photo first via /api/generate-reference."
            )
        if not os.path.exists(reference_image):
            print(f"File exists check failed for: {reference_image}")
            raise HTTPException(
                status_code=400,
                detail="Reference image not found. It may have been lost after a server restart. Please re-upload your photo."
            )
        # Step 1: Parse natural language query
        parsed_info = parse_natural_language_query(request.prompt)
        search_query = parsed_info.get('search_query', request.prompt)
        print(f" Parsed query: {search_query}")
        # Step 2: Search for products
        products = search_clothing(search_query, request.max_results)
        if not products:
            raise HTTPException(
                status_code=404,
                detail="No products found for the given query"
            )
        print(f" Found {len(products)} products")
        # Step 3: Generate outfit visualizations
        output_dir = Path(OUTPUT_IMAGE_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_images = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i, product in enumerate(products):
            print(f" Generating image {i+1}/{len(products)}...")
            filename = f"outfit_{timestamp}_{i+1}_{product['brand'].replace(' ', '_')}.png"
            output_path = str(output_dir / filename)
            result = generate_outfit_visualization(
                reference_image,
                product['image_url'],
                output_path,
                product_info=product
            )
            if result['success']:
                # Store relative path for API response
                generated_images.append(filename)
                print(f" ✓ Generated: {filename}")
            else:
                print(f" ✗ Failed: {result['message']}")
        if not generated_images:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate any outfit visualizations"
            )
        # Step 4: Return response with the latest generated image
        latest_image = generated_images[0] if generated_images else reference_image.split('/')[-1]  # Use first generated or original reference filename
        return GenerateOutfitResponse(
            success=True,
            message=f"Successfully generated {len(generated_images)} outfit visualization(s)",
            user_query=request.prompt,
            parsed_query=search_query,
            clothing_type=parsed_info.get('clothing_type'),
            color=parsed_info.get('color'),
            brand=parsed_info.get('brand'),
            style=parsed_info.get('style'),
            gender=parsed_info.get('gender'),
            products=[ProductInfo(**p) for p in products],
            generated_images=generated_images,
            timestamp=timestamp,
            latest_image=latest_image  # New field to pass back the latest image
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f" \u274c Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/api/search-products", response_model=SearchProductsResponse)
async def search_products(request: SearchProductsRequest):
    """
    Search for clothing products based on natural language prompt
    """
    try:
        print(f"\n🔍 Searching products: {request.prompt}")
        parsed_info = parse_natural_language_query(request.prompt)
        search_query = parsed_info.get('search_query', request.prompt)
        products = search_clothing(search_query, request.max_results)
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found for the given query")
            
        print(f" Found {len(products)} products")
        return SearchProductsResponse(
            success=True,
            user_query=request.prompt,
            parsed_query=search_query,
            clothing_type=parsed_info.get('clothing_type'),
            color=parsed_info.get('color'),
            brand=parsed_info.get('brand'),
            style=parsed_info.get('style'),
            gender=parsed_info.get('gender'),
            products=[ProductInfo(**p) for p in products]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f" ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-tryon", response_model=GenerateTryonResponse)
async def generate_tryon(request: GenerateTryonRequest):
    """
    Generate a virtual try-on visualization for a single product
    """
    try:
        print(f"\n👕 Generating try-on for: {request.product.brand}")
        
        # Resolve reference image
        if request.reference_image:
            cleaned_reference = Path(request.reference_image).name
            base_dir = Path(__file__).resolve().parent
            reference_image = str((base_dir / OUTPUT_IMAGE_DIR / cleaned_reference).resolve())
        elif REFERENCE_IMAGE_PATH and os.path.exists(REFERENCE_IMAGE_PATH):
            reference_image = REFERENCE_IMAGE_PATH
        else:
            raise HTTPException(status_code=400, detail="No reference image available. Please upload a photo first via /api/generate-reference.")

        if not os.path.exists(reference_image):
            raise HTTPException(status_code=400, detail="Reference image not found.")

        # Ensure output directory exists
        output_dir = Path(OUTPUT_IMAGE_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outfit_{timestamp}_{request.product.brand.replace(' ', '_')}.png"
        output_path = str(output_dir / filename)

        # Use our styloAI integration
        result = generate_outfit_visualization(
            reference_image,
            request.product.image_url,
            output_path,
            product_info=request.product.dict()
        )

        if not result['success']:
            raise HTTPException(status_code=500, detail=result['message'])

        print(f" ✓ Generated: {filename}")
        return GenerateTryonResponse(
            success=True,
            message="Successfully generated outfit",
            generated_image=filename,
            timestamp=timestamp
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f" ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{filename}")
async def get_image(filename: str):
    """
    Retrieve a generated outfit image
    Args:
        filename: Name of the generated outfit image file
    Returns:
        The image file
    """
    image_path = Path(OUTPUT_IMAGE_DIR) / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(
        str(image_path),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@app.get("/api/images")
async def list_images():
    """
    List all generated outfit images
    Returns:
        List of available image filenames
    """
    image_dir = Path(OUTPUT_IMAGE_DIR)
    if not image_dir.exists():
        return {"images": []}
    images = [
        f.name for f in image_dir.iterdir()
        if f.suffix.lower() in ['.png', '.jpg', '.jpeg']
    ]
    return {
        "total": len(images),
        "images": sorted(images, reverse=True)  # Most recent first
    }

@app.delete("/api/image/{filename}")
async def delete_image(filename: str):
    """
    Delete a generated outfit image
    Args:
        filename: Name of the image file to delete
    Returns:
        Success message
    """
    image_path = Path(OUTPUT_IMAGE_DIR) / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        image_path.unlink()
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete image: {str(e)}"
        )

@app.post("/api/generate-reference", response_model=GenerateReferenceResponse)
async def generate_reference(file: UploadFile = File(...)):
    """
    Convert a user's photo to a clean reference image with white background
    Similar to Emmanuel_Reference.png style - professional, clean, centered pose
    Args:
        file: Uploaded image file (JPEG, PNG, etc.)
    Returns:
        Path to generated reference image
    """
    try:
        print(f"\n📸 Processing reference image generation...")
        print(f" Content type: {file.content_type}")
        # Read uploaded file
        contents = await file.read()
        print(f" File size: {len(contents)} bytes")
        user_image = Image.open(BytesIO(contents))
        print(f" Uploaded image: {file.filename} ({user_image.size}, mode: {user_image.mode})")
        # Create prompt for Gemini to generate clean reference photo purely by removing the background
        prompt = """PHOTO EDITING TASK - Background Removal Only:
SOURCE IMAGE: The uploaded photo of a person.
YOUR TASK:
1. Extract the person exactly as they are in the source image.
2. Place them on a pure white background with no shadows.
3. DO NOT change their pose, DO NOT change their facial expression, DO NOT change their clothing, and DO NOT change their body shape or size.
4. Keep the person's clothing, face, and features EXACTLY as they are in the original photo.
5. Just give me the original person cut out perfectly on a white background.
Generate this clean photo now."""
        contents = [prompt, user_image]

        print(f" Generating reference image with Gemini...")
        # Generate the clean reference image using image generation model
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
        )
        # Process response
        image_saved = False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reference_{timestamp}_{file.filename.replace(' ', '_')}"  # Define filename here
        # Create output directory if it doesn't exist
        output_dir = Path(OUTPUT_IMAGE_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        if not response or not hasattr(response, 'candidates') or not response.candidates:
            raise HTTPException(
                status_code=500,
                detail="Gemini did not return a response"
            )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                generated_image = Image.open(BytesIO(part.inline_data.data))
                generated_image.save(output_path)
                print(f" ✅ Reference image saved: {filename}")
                image_saved = True
                break
        if not image_saved:
            raise HTTPException(
                status_code=500,
                detail="No image data returned from Gemini"
            )
        return GenerateReferenceResponse(
            success=True,
            message="Reference image generated successfully",
            reference_image=filename,
            timestamp=timestamp
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f" ❌ Error: {str(e)}")
        print(f" Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating reference image: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    import os
    # Get port from environment variable (Render sets this)
    port = int(os.getenv("PORT", 10000))  # Updated to match Render's detected port
    print("\n" + "="*60)
    print("🚀 Starting Stylo.AI Backend API")
    print("="*60)
    print(f"📍 API Root: http://0.0.0.0:{port}")
    print(f"📖 API Docs: http://0.0.0.0:{port}/docs")
    print(f"💚 Health Check: http://0.0.0.0:{port}/health")
    print("="*60)
    print("🎨 Ready to generate outfit visualizations!")
    print("⏹️ Press Ctrl+C to stop")
    print("="*60 + "\n")
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
