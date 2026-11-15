import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError
from PIL import Image

# Load GEMINI_API_KEY from your .env file
load_dotenv()


# ---------------------------------------------------------------------------
# 1. What each goal looks for.
#    To add a new goal or concern: add one line here, and a matching chip in app.py.
#    The keys must match the values app.py sends (FOOD_GOALS values, SKIN_TYPES, SKIN_CONCERNS).
# ---------------------------------------------------------------------------

FOOD_GUIDE = {
    "Acne: Hormonal & Insulin Pathways":
        "Flag dairy/whey/casein (IGF-1 and insulin signaling) and refined sugars/syrups (high glycemic load). "
        "Reward fiber, protein, zinc and omega-3s.",
    "Acne: Gut & Inflammation":
        "Flag refined omega-6 seed oils (sunflower, safflower, canola, soybean, 'vegetable' oil), emulsifiers "
        "(polysorbate 80, carrageenan, carboxymethylcellulose) and artificial sweeteners. "
        "Reward fiber, fermented ingredients, polyphenols and omega-3s.",
    "Blood Sugar Balance":
        "Flag added sugars, syrups and refined starches, especially near the top of the list. "
        "Reward fiber, protein and fats that slow absorption.",
    "Athletic: Lean Bulk (High Protein/Calories)":
        "Reward bioavailable protein, healthy fats and calorie density. "
        "Do NOT penalize calories or whey unless an acne goal is also selected.",
    "Weight Loss / Calorie Deficit":
        "Flag added sugars, refined starches and calorie-dense oils. Reward protein and fiber that support fullness.",
}

SKIN_TYPE_GUIDE = {
    "Oily":
        "Prefers lightweight, water- or gel-based textures. Heavy butters, waxes and rich oils near the top of the "
        "list may feel heavy or clog pores. Reward niacinamide, salicylic acid, zinc PCA and light humectants "
        "(glycerin, hyaluronic acid).",
    "Dry":
        "Needs richer textures: emollients and occlusives (shea butter, squalane, petrolatum, ceramides, fatty "
        "alcohols like cetearyl alcohol) plus humectants. Do NOT penalize thick creams. Flag drying ingredients: "
        "denatured alcohol near the top of the list and harsh sulfates (sodium lauryl sulfate).",
    "Combination":
        "Needs balance: lightweight hydration that won't overload oily areas. Flag very heavy occlusives and very "
        "drying alcohols alike.",
    "Normal":
        "Few restrictions; focus on the selected concerns.",
}

SKIN_CONCERN_GUIDE = {
    "Acne-prone":
        "Flag commonly comedogenic ingredients: coconut oil, isopropyl myristate/palmitate, cocoa butter, wheat germ "
        "oil, algae extract, laureth-4, heavy waxes. Mention that comedogenic ratings come from older tests and depend "
        "on concentration and the whole formula. Reward salicylic acid, azelaic acid, niacinamide, zinc and "
        "non-comedogenic hydrators.",
    "Sensitive":
        "Flag fragrance/parfum, essential oils, denatured alcohol near the top, menthol and strong acids. Reward short "
        "ingredient lists, ceramides, panthenol, allantoin, glycerin and centella.",
    "Eczema-prone":
        "Prioritize barrier repair. Flag fragrance/parfum, essential oils, harsh sulfates, methylisothiazolinone and "
        "high alcohol. Reward ceramides, colloidal oatmeal, petrolatum, shea butter, glycerin and panthenol.",
    "Rosacea-prone":
        "Flag fragrance, alcohol, menthol, camphor, peppermint/eucalyptus, witch hazel and strong exfoliants; some "
        "chemical sunscreen filters (avobenzone, oxybenzone) can sting. Reward azelaic acid, niacinamide, zinc oxide "
        "mineral sunscreen, ceramides and centella.",
    "Signs of aging":
        "Reward vitamin C (ascorbic acid and derivatives), retinoids (retinol, retinal) or bakuchiol, peptides, "
        "niacinamide and broad-spectrum sunscreen. Note that retinoids and vitamin C can irritate sensitive skin.",
    "Dark spots":
        "Reward vitamin C, niacinamide, azelaic acid, tranexamic acid, alpha arbutin, licorice root extract and daily "
        "sunscreen. Flag irritants that can worsen post-inflammatory marks.",
}


# ---------------------------------------------------------------------------
# 2. The exact JSON structure Gemini must return.
#    Every r.something used in app.py must exist here.
# ---------------------------------------------------------------------------

class IngredientFlag(BaseModel):
    ingredient: str = Field(description="Ingredient name, written exactly as it appears in all_ingredients")
    pathway: str = Field(description="Short label, e.g. Hormonal/IGF-1, Gut Inflammation, High Glycemic, "
                                     "Pore-Clogging, Irritation/Fragrance, Barrier-Drying")
    explanation: str = Field(description="Calm, biological explanation of why this may affect the user's goals")
    matters_most_for: str = Field(description="Who this matters most for, e.g. 'oily or acne-prone skin' or "
                                              "'anyone managing blood sugar'. Mention if it is fine or even helpful "
                                              "for other profiles")


class SupportiveWin(BaseModel):
    ingredient: str = Field(description="Ingredient name, written exactly as it appears in all_ingredients")
    benefit: str = Field(description="How this supports the user's goals: skin barrier, hydration, calming, "
                                     "gut health, blood sugar, muscle growth, etc.")


class Swap(BaseModel):
    instead_of: str = Field(description="The ingredient or product quality this swap addresses, "
                                        "e.g. 'coconut oil base' or 'brown rice syrup'")
    look_for: str = Field(description="An ingredient profile to look for instead. Never a brand or product name")
    why: str = Field(description="One sentence on why this fits the user's profile")


class AvoidMatch(BaseModel):
    term: str = Field(description="The avoid-list term, written exactly as the user typed it")
    ingredient: str = Field(description="The matching ingredient, written exactly as it appears in all_ingredients")


class ProductAnalysis(BaseModel):
    product_name: str = Field(description="Short product name from the package, e.g. 'Chocolate Peanut Protein Bar'. "
                                          "If not visible, describe the product in 2-4 words")
    product_type: str = Field(description="Exactly 'Food/Beverage' or 'Skincare/Cosmetic'")
    product_category: str = Field(description="The specific kind of product, lowercase and singular, using the most "
                                              "common name: e.g. 'moisturizer', 'sunscreen', 'cleanser', 'serum', "
                                              "'toner', 'protein bar', 'granola', 'yogurt'. A moisturizer with SPF "
                                              "counts as 'sunscreen'")
    all_ingredients: list[str] = Field(description="Every ingredient on the label, in label order, using short clean "
                                                   "names, no duplicates. Include BOTH the Active and the Inactive "
                                                   "ingredients when the label has both sections")
    unread_note: str = Field(description="Empty string if the whole ingredient list was readable. Otherwise one short "
                                         "sentence on what could not be read, e.g. 'The inactive ingredients are too "
                                         "small or curved to read.'")
    alignment_score: int = Field(description="0 to 100 score for the profile that matches the product type, based "
                                             "only on the ingredients actually read")
    verdict_headline: str = Field(description="Short, empowering 1-sentence summary without shaming")
    triggers: list[IngredientFlag]
    avoid_matches: list[AvoidMatch] = Field(description="Every ingredient that is, contains or comes from something on "
                                                        "the user's avoid list. Empty if there is no avoid list or no match")
    supportive_wins: list[SupportiveWin]
    swaps: list[Swap] = Field(description="1 to 3 swaps tailored to the user's profile; empty if already a great fit")
    non_restrictive_tip: str = Field(description="Practical pairing, layering or usage tip without fear-mongering")


# ---------------------------------------------------------------------------
# 3. Instructions for Gemini
# ---------------------------------------------------------------------------

def _section(title, guide):
    return title + "\n" + "\n".join(f"  * {name}: {rule}" for name, rule in guide.items())


SYSTEM_PROMPT = f"""
You are NourishLens, a root-cause nutrition and skin health analyst.

Philosophy:
- Skin issues are signals (internal and topical), not something solved by fear. Never use shaming words like
  'toxic', 'poison' or 'bad'. Explain pathways calmly, using words like "may" and "can".
- Context over verdicts: the same ingredient can be a problem for one person and helpful for another (shea butter
  may clog pores on oily, acne-prone skin yet repair a dry barrier). Always say who a flag matters most for.
- Ingredients are listed roughly by amount, so those near the top matter more than trace ingredients at the end.

Steps:
1. Decide product_type ('Food/Beverage' or 'Skincare/Cosmetic') and product_category (the specific kind of
   product, e.g. 'moisturizer' or 'sunscreen'), using the packaging and the ingredients.
2. List EVERY ingredient in all_ingredients, then use those exact names in triggers and supportive_wins.
   Sunscreens and many skincare products split the list into "Active ingredients" and "Inactive ingredients";
   read and include both. If part of the list is unreadable, say so in unread_note.
3. Score ONLY against the part of the profile that matches the product type: food goals for food, skin type and
   skin concerns for skincare. If that part is empty, score for general balanced wellness (food) or general skin
   health (skincare).
4. Look for BOTH triggers and supportive ingredients. The score must agree with them: a product with no triggers
   and several supportive ingredients should score high. Never lower the score because part of the label was
   unreadable; report that in unread_note instead, and don't mention it in verdict_headline.
5. Avoid list: if the user gave ingredients to avoid, check every ingredient against it, including synonyms,
   scientific names and derivatives (e.g. 'parfum' or 'linalool' for fragrance; 'casein' or 'milk solids' for dairy;
   'cocos nucifera oil' or 'coconut alkanes' for coconut oil). Record each match in avoid_matches AND add it to
   triggers with pathway 'Your filter' and a short explanation of how it relates to that term. Lower the score
   for each match, since the user has said they want to avoid it. This applies to food and skincare alike.
6. Suggest swaps as ingredient profiles to look for (e.g. "a zinc oxide mineral sunscreen with an oil-free gel
   base"), tailored to the user's profile. Never name brands or specific products.

{_section("FOOD GOALS", FOOD_GUIDE)}

{_section("SKIN TYPES", SKIN_TYPE_GUIDE)}

{_section("SKIN CONCERNS", SKIN_CONCERN_GUIDE)}
"""


# ---------------------------------------------------------------------------
# 4. Send the image + profile to Gemini
# ---------------------------------------------------------------------------

# Try the stronger model first, then fall back if it's busy or unavailable
MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]


class AnalysisError(Exception):
    """A problem worth showing the user as-is (bad key, models busy, unreadable answer)."""


def analyze_label(image: Image.Image, food_goals: list[str], skin_type: Optional[str],
                  skin_concerns: list[str], avoid: list[str]) -> ProductAnalysis:
    # Resize large phone photos so uploads stay fast
    img_copy = image.copy()
    if img_copy.mode in ("RGBA", "P"):
        img_copy = img_copy.convert("RGB")
    img_copy.thumbnail((2048, 2048))  # big enough for small print on bottles and tubes

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise AnalysisError("No Gemini API key found. Add GEMINI_API_KEY=... to the .env file, then restart the app.")

    # 45 seconds per attempt: enough for the main model to finish, so slow answers aren't thrown away
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=45000))

    user_prompt = f"""
    Analyze this product label for a user with this profile:
    - Food goals: {', '.join(food_goals) if food_goals else 'None selected'}
    - Skin type: {skin_type or 'Not set'}
    - Skin concerns: {', '.join(skin_concerns) if skin_concerns else 'None selected'}
    - Ingredients to avoid: {', '.join(avoid) if avoid else 'None'}
    """

    for model_name in MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[img_copy, user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=ProductAnalysis,
                ),
            )
            return ProductAnalysis.model_validate_json(response.text)
        except errors.APIError as e:
            # A bad or unauthorized key fails the same way on every model, so stop instead of retrying
            if e.code in (400, 401, 403) and "model" not in str(e).lower():
                raise AnalysisError(f"Gemini rejected the request ({e.code}). Check the API key in your .env file.") from e
            print(f"[Fallback] {model_name} failed ({e.code}: {e}), trying next...")
        except ValidationError as e:
            print(f"[Fallback] {model_name} returned an incomplete answer ({e.error_count()} problems), trying next...")
        except Exception as e:  # timeouts, network hiccups
            print(f"[Fallback] {model_name} unavailable ({type(e).__name__}: {e}), trying next...")

    raise AnalysisError("Gemini is busy or unreachable right now. Click Analyze again in a few seconds. "
                        "(The terminal shows the exact error.)")