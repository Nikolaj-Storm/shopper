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
            "POST /api/generate-outfit": "Generate outfit visualizations from natural language",
            "POST /api/generate-reference": "Convert user photo to clean reference image",
            "GET /api/image/{filename}": "Retrieve a generated outfit image",
            "GET /api/images": "List all generated images",
            "DELETE /api/image/{filename}": "Delete a generated image",
            "GET /health": "Health check endpoint",
            "GET /docs": "Interactive API documentation"
        }
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
        print(f" ❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

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
        # Load reference style image if available (optional)
        style_reference_path = Path(__file__).resolve().parent.parent / "Images" / "Emmanuel_Reference.png"
        style_reference_image = None
        if style_reference_path.exists():
            style_reference_image = Image.open(style_reference_path)
            print(f" Reference style image loaded: {style_reference_image.size}, mode: {style_reference_image.mode}")
        else:
            print(f" No style reference image found at {style_reference_path}, proceeding without it")

        # Create prompt for Gemini to generate clean reference photo
        if style_reference_image:
            prompt = """PHOTO EDITING TASK - Create a clean, professional reference photo:
SOURCE IMAGE: First image (user's uploaded photo)
STYLE REFERENCE: Second image (the target style to match - this is the EXACT pose you need to replicate)
YOUR TASK:
1. Extract the person from the first image
2. Create a clean, professional portrait matching the EXACT style and pose of the second image:
   - Make Sure the background is completely white and has no shadows
   - Person centered in frame
   - Full body visible (head to feet or at least to knees)
   - **CRITICAL: Arms must be LIFTED SLIGHTLY OUT TO THE SIDES (like an A-pose or game character reference pose)**
   - **CRITICAL: Look at the reference image - replicate this EXACT arm position with arms raised slightly away from body**
   - Neutral, straight-on pose facing camera directly
   - Standing straight and upright
   - Good lighting, professional photo quality
   - Remove any background objects, clutter, or distractions
   - Keep the person's clothing, face, and features exactly as they are
   - Professional studio-quality portrait
IMPORTANT POSE REQUIREMENTS:
- Arms: LIFTED SLIGHTLY TO THE SIDES at approximately 20-30 degrees from body (like a game avatar T-pose/A-pose)
- Arms should be extended out to sides, NOT hanging down, NOT crossed, NOT in pockets
- This creates space between arms and torso - essential for clothing visualization
- Body: Facing forward, centered, standing straight
- Hands: Relaxed, fingers extended naturally
- Feet: Slightly apart, natural standing position
- Head: Looking directly at camera
- Background: Pure white with no shadows
- Lighting: Even and professional
- Person should be in sharp focus
This is for use as a reference photo for virtual try-on - the slightly lifted arm position (like a game character reference) is CRITICAL for proper clothing visualization.
Generate this clean reference photo now with arms lifted slightly to the sides."""
            contents = [prompt, user_image, style_reference_image]
        else:
            prompt = """PHOTO EDITING TASK - Create a clean, professional reference photo:
SOURCE IMAGE: The uploaded photo of a person.
YOUR TASK:
1. Extract the person from the uploaded image
2. Create a clean, professional full-body portrait:
   - Pure white background with no shadows
   - Person centered in frame
   - Full body visible (head to feet or at least to knees)
   - **CRITICAL: Arms must be LIFTED SLIGHTLY OUT TO THE SIDES (A-pose, approximately 20-30 degrees from body)**
   - Arms extended out to sides, NOT hanging down, NOT crossed, NOT in pockets
   - Neutral, straight-on pose facing camera directly
   - Standing straight and upright
   - Good lighting, professional photo quality
   - Remove any background objects, clutter, or distractions
   - Keep the person's clothing, face, and features exactly as they are
   - Professional studio-quality portrait
This is for use as a virtual try-on reference photo. The slightly lifted arm position is CRITICAL.
Generate this clean reference photo now."""
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
