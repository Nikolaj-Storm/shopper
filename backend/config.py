import os

# Env vars for API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Paths (adjust based on Render's ephemeral filesystem)
OUTPUT_IMAGE_DIR = "./generated_images"
REFERENCE_IMAGE_PATH = "./Images/Emmanuel_Reference.png"
