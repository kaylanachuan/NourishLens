import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# Load GEMINI_API_KEY from your .env file
load_dotenv()

# 1. Define the exact JSON structure Gemini must return
class IngredientFlag(BaseModel):
    ingredient: str = Field(description="Exact ingredient name from the label")
    pathway: str = Field(description="e.g., Hormonal/IGF-1, Gut Inflammation, Pore-Clogging, or High Glycemic")
    explanation: str = Field(description="Calm, biological explanation of why this affects the user's goal")

class SupportiveWin(BaseModel):
    ingredient: str = Field(description="Beneficial ingredient or nutrient from the label")
    benefit: str = Field(description="How this supports skin barrier, gut health, blood sugar, or muscle growth")

class ProductAnalysis(BaseModel):
    product_type: str = Field(description="Food/Beverage or Skincare/Cosmetic")
    alignment_score: int = Field(description="0 to 100 score strictly tailored to the user's active profile")
    verdict_headline: str = Field(description="Short, empowering 1-sentence summary without food shaming")
    triggers: list[IngredientFlag]
    supportive_wins: list[SupportiveWin]
    non_restrictive_tip: str = Field(description="Practical pairing tip or cleaner swap without rigid fear-mongering")

# 2. Function that sends the image + user goals to Gemini
def analyze_label(image: Image.Image, selected_goals: list[str], custom_rules: str) -> ProductAnalysis:
    # Resize large phone photos so upload and token processing happen in <1 second
    img_copy = image.copy()
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
    img_copy.thumbnail((1024, 1024))

    # Initialize client with a 25-second timeout (in milliseconds) so it never hangs
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=25000),
    )

    system_prompt = """
    You are NourishLens, a root-cause nutrition and skin health analyst.
    Philosophy:
    - Acne is an internal signal (gut dysbiosis, insulin/IGF-1 spikes, inflammation, nutrient gaps), NOT something solved by rigid food fear.
    - Never use shaming words like 'toxic', 'poison', or 'bad food'. Explain biological pathways calmly.
    - Always look for BOTH potential triggers AND supportive nutrients/ingredients (zinc, omega-3s, fiber, ceramides, protein).
    - Score 0-100 strictly based on the user's selected goals (e.g., Bulking rewards protein & calories; Hormonal Acne flags whey & high-glycemic sugars; Skincare flags comedogenic oils like coconut oil).
    - Provide an actionable, non-restrictive pairing tip or swap.
    """

    user_prompt = f"""
    Analyze this product label for a user with these active goals:
    - Selected Profiles: {', '.join(selected_goals) if selected_goals else 'General Balanced Wellness'}
    - Custom Filters/Notes: {custom_rules or 'None'}
    """

    # Use gemini-3.5-flash-lite for fast responses and generous free-tier limits
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[img_copy, user_prompt],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=ProductAnalysis,
        ),
    )

    return ProductAnalysis.model_validate_json(response.text)