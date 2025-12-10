from google import genai
from PIL import Image
from io import BytesIO
import os
import sys

# Import API key from config file
try:
    from config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("No API key found. Please create config.py with GEMINI_API_KEY")

os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_clothing_image(user_image_path, clothing_image_path, prompt, output_path="generated_outfit.png"):
    """
    Generate an image of the user wearing the clothing
    
    Args:
        user_image_path: Path to your image
        clothing_image_path: Path to the clothing image
        prompt: Description of what you want (e.g., "wearing this green shirt")
        output_path: Where to save the generated image (default: generated_outfit.png)
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Load both images
        user_image = Image.open(user_image_path)
        clothing_image = Image.open(clothing_image_path)
        
        print(f"Generating image...")
        print(f"Prompt: {prompt}")
        print("This may take a moment...")
        
        # Generate the image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, user_image, clothing_image],
        )
        
        # Process the response
        image_saved = False
        text_response = ""
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_response += part.text
                print(f"Response: {part.text}")
            elif part.inline_data is not None:
                generated_image = Image.open(BytesIO(part.inline_data.data))
                generated_image.save(output_path)
                print(f"✅ Image saved as '{output_path}'")
                image_saved = True
        
        if image_saved:
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
            
    except FileNotFoundError as e:
        return {"success": False, "message": f"File not found: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python imageGen.py <your_image> <clothing_image> <prompt>")
        print()
        print("Example:")
        print('  python imageGen.py me.jpg shirt.jpg "Create an image of me wearing this green shirt"')
        print()
        sys.exit(1)
    
    user_image = sys.argv[1]
    clothing_image = sys.argv[2]
    prompt = sys.argv[3]
    
    result = generate_clothing_image(user_image, clothing_image, prompt)
    print(f"\nResult: {result['message']}")
