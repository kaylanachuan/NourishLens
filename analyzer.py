import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# Load GEMINI_API_KEY from your .env file
load_dotenv()


# 1. Define the exact JSON structure Gemini must return
#    Every r.something used in app.py must exist here.
class IngredientFlag(BaseModel):
    ingredient: str = Field(description="Ingredient name, written exactly as it appears in all_ingredients")
    pathway: str = Field(description="e.g., Hormonal/IGF-1, Gut Inflammation, Pore-Clogging, or High Glycemic")
    explanation: str = Field(description="Calm, biological explanation of why this affects the user's goal")


class SupportiveWin(BaseModel):
    ingredient: str = Field(description="Ingredient name, written exactly as it appears in all_ingredients")
    benefit: str = Field(description="How this supports skin barrier, gut health, blood sugar, or muscle growth")


class ProductAnalysis(BaseModel):
    product_name: str = Field(description="Short product name from the package, e.g. 'Chocolate Peanut Protein Bar'. If not visible, describe the product in 2-4 words")
    product_type: str = Field(description="Food/Beverage or Skincare/Cosmetic")
    all_ingredients: list[str] = Field(description="Every ingredient on the label, in label order, using short clean names, no duplicates")
    alignment_score: int = Field(description="0 to 100 score strictly tailored to the user's active profile")
    verdict_headline: str = Field(description="Short, empowering 1-sentence summary without food shaming")
    triggers: list[IngredientFlag]
    supportive_wins: list[SupportiveWin]
    non_restrictive_tip: str = Field(description="Practical pairing tip or cleaner swap without rigid fear-mongering")


# 2. Function that sends the image + user goals to Gemini
def analyze_label(image: Image.Image, selected_goals: list[str], custom_rules: str) -> ProductAnalysis:
    # Resize large phone photos so uploads stay fast
    img_copy = image.copy()
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
    img_copy.thumbnail((1024, 1024))

    # 12-second timeout per attempt so a busy model fails over quickly
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=12000),
    )

    system_prompt = """
    You are NourishLens, a root-cause nutrition and skin health analyst.
    Philosophy:
    - Acne is an internal signal (gut dysbiosis, insulin/IGF-1 spikes, inflammation, nutrient gaps), NOT something solved by rigid food fear.
    - Never use shaming words like 'toxic', 'poison', or 'bad food'. Explain biological pathways calmly, using words like "may" and "can".
    - First, list EVERY ingredient on the label in all_ingredients. Then use those exact same names in triggers and supportive_wins.
    - Thoroughly read EVERY ingredient on the label:
      * For Acne (Hormonal/Insulin or Gut/Inflammation): Flag dairy/whey/casein (IGF-1/insulin spike), refined sugars/syrups (high glycemic load), and refined omega-6 seed oils (sunflower oil, safflower oil, canola oil, soybean oil, vegetable oil — inflammatory pathways), plus emulsifiers/artificial sweeteners.
      * For Acne (Topical/Skincare): Flag comedogenic/pore-clogging ingredients (coconut oil, isopropyl myristate, cocoa butter, heavy waxes, pore-clogging esters).
      * For Bulking: Reward bioavailable protein, healthy fats, and calorie density; do NOT penalize calories or whey unless Acne is also selected.
      * For Blood Sugar / Weight Loss: Flag added sugars, refined starches, and calorie-dense oils when aligned with the goal.
    - Always look for BOTH potential triggers AND supportive nutrients/ingredients (zinc, omega-3s, fiber, ceramides, protein).
    - Provide an actionable, non-restrictive pairing tip or swap.
    """

    user_prompt = f"""
    Analyze this product label thoroughly for a user with these active goals:
    - Selected Profiles: {', '.join(selected_goals) if selected_goals else 'General Balanced Wellness'}
    - Custom Filters/Notes: {custom_rules or 'None'}
    """

    # Try the stronger model first, then fall back if it's busy
    for model_name in ["gemini-3.8-flash", "gemini-3.5-flash-lite"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[img_copy, user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ProductAnalysis,
                ),
            )
            return ProductAnalysis.model_validate_json(response.text)
        except Exception as e:
            print(f"[Fallback] {model_name} unavailable ({e}), trying next...")
            continue

    raise RuntimeError("All Gemini models are temporarily busy—please click Analyze again in a few seconds.")