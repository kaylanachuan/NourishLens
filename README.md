# 🌿 NourishLens

Snap any food or skincare label and see how every ingredient fits your goals.

[screenshot or short GIF of the app here]

## What it does

- Upload a photo of an ingredient label (or try the built-in sample)
- Pick your goals: hormonal acne, gut health, blood sugar, lean bulk, weight loss, and more
- Get an alignment score out of 100, with every ingredient color-coded as flagged, helpful, or neutral
- Tap any ingredient to see why it matters for your goals
- Compare two products side by side, with the good and bad of each

## How it works

1. A label photo is sent to the Gemini API, which reads the ingredients.
2. The response is structured with Pydantic into triggers, supportive ingredients, and a score.
3. Streamlit renders the results.

## Tech stack

Python, Streamlit, Google Gemini API (`google-genai`), Pillow, Pydantic

## Setup

```bash
git clone https://github.com/kaylanachuan/NourishLens.git
cd NourishLens
python3 -m venv venv
source venv/bin/activate
pip install streamlit google-genai pillow pydantic python-dotenv
```

Create a `.env` file in the project folder:

```
GEMINI_API_KEY=your_key_here
```

Get a key at [Google AI Studio](https://aistudio.google.com/apikey). Never commit this file.

## Run

```bash
streamlit run app.py
```

## Project structure

- `app.py`: Streamlit UI
- `analyzer.py`: Gemini calls and result models
- `test_gemini.py`: quick API sanity check

## Notes

NourishLens is an educational tool, not medical advice.

## Roadmap

- (things you'd like to add next)
