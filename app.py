
import streamlit as st
from PIL import Image
from analyzer import analyze_label

st.set_page_config(page_title="NourishLens", page_icon="🌿", layout="centered")

SAGE = "#9CAF88"       # brand color
SAGE_DARK = "#4F6340"  # darker sage for text on light backgrounds (readable)

# Apple look: system font, rounded corners, soft sage accents
st.markdown(f"""
<style>
html, body, .stApp, .stApp * {{ font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; }}
.block-container {{ max-width: 640px; padding-top: 2.5rem; }}
button, img, [data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px !important; }}
h1 {{ color: {SAGE_DARK}; letter-spacing: -0.02em; }}
h3 {{ font-size: 1.15rem !important; }}
[data-testid="stBaseButton-primary"], [data-testid="baseButton-primary"] {{
  background: {SAGE} !important; border: none !important; color: #1F2A18 !important;
  font-weight: 600 !important; min-height: 50px;
}}
[data-testid="stBaseButton-primary"]:hover {{ filter: brightness(0.95); }}

/* Hide Streamlit's default top bar so our nav bar replaces it */
header[data-testid="stHeader"] {{ display: none; }}
.block-container {{ padding-top: 6rem !important; }}

/* Apple-style frosted glass nav bar */
.nl-nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000; height: 56px;
  display: flex; align-items: center; justify-content: space-between; padding: 0 28px;
  background: rgba(251, 252, 248, 0.75);
  backdrop-filter: saturate(180%) blur(20px); -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}}
.nl-logo {{ display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem; color: #1F2A18; }}
.nl-logo-mark {{
  width: 30px; height: 30px; border-radius: 8px; background: {SAGE};
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}}
.nl-links a {{ margin-left: 24px; font-size: 0.9rem; color: #1F2A18 !important; text-decoration: none; opacity: 0.75; }}
.nl-links a:hover {{ opacity: 1; }}

/* Left-aligned hero */
.nl-hero-title {{ font-size: 2.6rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; color: #1F2A18; }}
.nl-hero-sub {{ font-size: 1.15rem; opacity: 0.6; margin: 10px 0 8px; }}
</style>
""", unsafe_allow_html=True)

# Nav bar: logo top left, links top right
st.markdown("""
<div class="nl-nav">
  <div class="nl-logo"><div class="nl-logo-mark">🌿</div>NourishLens</div>
  <div class="nl-links">
    <a href="#your-goals" target="_self">Goals</a>
    <a href="#ingredient-label" target="_self">Scan</a>
  </div>
</div>
""", unsafe_allow_html=True)


def score_ring(score: int) -> str:
    """Apple-Activity-style ring that fills to the score."""
    score = max(0, min(100, int(score)))
    color = SAGE if score >= 70 else "#E8B04B" if score >= 40 else "#D9776B"
    circ = 2 * 3.1416 * 44
    return f"""
    <div style="display:flex;justify-content:center;margin:8px 0 4px">
      <svg width="140" height="140" viewBox="0 0 112 112" role="img" aria-label="Score {score} out of 100">
        <circle cx="56" cy="56" r="44" fill="none" stroke="rgba(127,127,127,0.15)" stroke-width="11"/>
        <circle cx="56" cy="56" r="44" fill="none" stroke="{color}" stroke-width="11" stroke-linecap="round"
          stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ * (1 - score / 100):.1f}" transform="rotate(-90 56 56)"/>
        <text x="56" y="60" text-anchor="middle" font-size="30" font-weight="700" fill="currentColor">{score}</text>
        <text x="56" y="76" text-anchor="middle" font-size="9" fill="currentColor" opacity="0.55">OUT OF 100</text>
      </svg>
    </div>"""


# Hero (left aligned, like an Apple product page)
st.markdown(
    '<div class="nl-hero-title">Know what\'s in it.</div>'
    '<div class="nl-hero-sub">Scan any food or skincare label and see how it fits your goals.</div>',
    unsafe_allow_html=True,
)

# 1. Goals
st.subheader("Your Goals")
selected_goals = st.multiselect(
    "Choose one or more",
    [
        "Acne: Hormonal & Insulin Pathways",
        "Acne: Gut & Inflammation",
        "Acne: Topical Skin Barrier (Skincare)",
        "Blood Sugar Balance",
        "Athletic: Lean Bulk (High Protein/Calories)",
        "Weight Loss / Calorie Deficit",
    ],
    default=["Acne: Hormonal & Insulin Pathways"],
)
custom_rules = st.text_input("Custom filters (optional)", placeholder="e.g. whey, coconut oil, seed oils")

# 2. Photo (or a one-tap sample for demos)
st.subheader("Ingredient Label")
uploaded_file = st.file_uploader("Add a clear photo of the ingredients", type=["jpg", "jpeg", "png", "webp"])
if st.button("No photo handy? Try a sample label"):
    st.session_state.use_sample = True
if uploaded_file:
    st.session_state.use_sample = False

image = None
if uploaded_file:
    image = Image.open(uploaded_file)
elif st.session_state.get("use_sample"):
    image = Image.open("sample_label.png")

if image:
    st.image(image, width=220)

    if st.button("Analyze Label", type="primary", use_container_width=True):
        with st.spinner("Reading the label…"):
            try:
                result = analyze_label(image, selected_goals, custom_rules)
            except Exception:
                st.error("Couldn't analyze this label. Try again, or use a sharper photo.")
                st.stop()

        # Summary card with the score ring
        with st.container(border=True):
            st.markdown(score_ring(result.alignment_score), unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center'><b>{result.product_type}</b><br>{result.verdict_headline}</div>",
                unsafe_allow_html=True,
            )

        st.subheader("Worth Knowing")
        if result.triggers:
            for t in result.triggers:
                with st.container(border=True):
                    st.markdown(f"🟠 **{t.ingredient}** · {t.pathway}\n\n{t.explanation}")
        else:
            st.caption("Nothing flagged for your goals.")

        st.subheader("Working For You")
        if result.supportive_wins:
            for w in result.supportive_wins:
                with st.container(border=True):
                    st.markdown(f"🟢 **{w.ingredient}**\n\n{w.benefit}")
        else:
            st.caption("No standout helpful ingredients on this label.")

        st.subheader("Try This")
        st.info(f"💡 {result.non_restrictive_tip}")
