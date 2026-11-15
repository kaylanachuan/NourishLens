import base64  # NourishLens UI: sage theme, scan animation, tappable ingredients, compare mode
import io
import math

import streamlit as st
from PIL import Image
from analyzer import analyze_label

st.set_page_config(page_title="NourishLens", page_icon="🌿", layout="wide")

INK = "#1F2A18"
SAGE = "#9CAF88"
SAGE_LIGHT = "#E3EADB"
ACCENT = "#4F6340"  # dark sage
WARN, WARN_BG = "#C2621A", "#FDE8D7"
GOOD, GOOD_BG = "#4F6340", "#E2ECD8"
NEUTRAL, NEUTRAL_BG = "#55555C", "rgba(255,255,255,0.75)"

# Chip label -> what the analyzer sees (keys in analyzer.FOOD_GUIDE)
FOOD_GOALS = {
    "Hormonal acne": "Acne: Hormonal & Insulin Pathways",
    "Gut & inflammation": "Acne: Gut & Inflammation",
    "Blood sugar": "Blood Sugar Balance",
    "Lean bulk": "Athletic: Lean Bulk (High Protein/Calories)",
    "Weight loss": "Weight Loss / Calorie Deficit",
}
# Must match the keys in analyzer.SKIN_TYPE_GUIDE and analyzer.SKIN_CONCERN_GUIDE
SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal"]
SKIN_CONCERNS = ["Acne-prone", "Sensitive", "Eczema-prone", "Rosacea-prone", "Signs of aging", "Dark spots"]

st.markdown(f"""
<style>
@import url("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap");
/* PP Editorial New: drop the font files into the static/ folder (see config.toml).
   Instrument Serif is a free look-alike that shows until those files are added. */
@font-face {{ font-family: "PP Editorial New"; src: url("app/static/PPEditorialNew-Regular.otf") format("opentype");
  font-weight: 400; font-style: normal; font-display: swap; }}
@font-face {{ font-family: "PP Editorial New"; src: url("app/static/PPEditorialNew-Italic.otf") format("opentype");
  font-weight: 400; font-style: italic; font-display: swap; }}
:root {{ --nl-serif: "PP Editorial New", "Instrument Serif", Georgia, serif; }}
.stApp .nl-serif, .stApp h3, .stApp h3 *, .stApp .nl-hero-title, .stApp .nl-hero-title *, .stApp .nl-status, .stApp .nl-product-name,
.stApp .nl-count, .stApp .nl-stats b, .stApp .nl-cmp-name, .stApp .nl-logo, .stApp .nl-ring-num > span {{
  font-family: var(--nl-serif) !important; }}

html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]) {{
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; }}

/* Soft sage background that slowly shifts */
.stApp {{
  color: {INK};
  background: linear-gradient(125deg, #DCE6D1 0%, #E8EEE1 30%, #D3DFC6 60%, #E9EFE3 100%);
  background-size: 260% 260%; animation: nl-bg 20s ease-in-out infinite;
}}
@keyframes nl-bg {{ 0% {{ background-position: 0% 40%; }} 50% {{ background-position: 100% 60%; }} 100% {{ background-position: 0% 40%; }} }}
.block-container {{ max-width: 1160px; padding: 6.2rem 2rem 4rem !important; }}
header[data-testid="stHeader"] {{ display: none; }}
h3 {{ color: {INK} !important; font-size: 1.7rem !important; font-weight: 400 !important; letter-spacing: -.01em; line-height: 1.15 !important; }}

/* Frosted glass cards */
[class*="st-key-card"] {{
  background: rgba(255,255,255,0.72); border: 1px solid rgba(255,255,255,0.85); border-radius: 26px;
  padding: 28px !important; box-shadow: 0 10px 40px rgba(31,42,24,0.08);
  backdrop-filter: blur(28px) saturate(170%); -webkit-backdrop-filter: blur(28px) saturate(170%);
}}

/* Nav */
.nl-nav {{ position: fixed; top: 0; left: 0; right: 0; z-index: 1000; height: 58px; display: flex;
  align-items: center; justify-content: space-between; padding: 0 32px;
  background: rgba(156,175,136,0.94); border-bottom: 1px solid rgba(31,42,24,0.06);
  backdrop-filter: blur(24px) saturate(180%); -webkit-backdrop-filter: blur(24px) saturate(180%); }}
.nl-logo {{ display: flex; align-items: center; gap: 10px; font-weight: 400; font-size: 1.45rem; }}
.nl-logo-mark {{ width: 32px; height: 32px; border-radius: 9px; display: flex; align-items: center; justify-content: center;
  background: white; font-size: 17px; }}
.nl-links a {{ margin-left: 28px; font-size: .95rem; font-weight: 500; color: {INK} !important; text-decoration: none; opacity: .85; }}
.nl-links a.nl-cta {{ opacity: 1; margin-left: 28px; padding: 8px 16px; border-radius: 999px; background: {INK}; color: white !important;
  font-size: .9rem; font-weight: 600; text-decoration: none; }}

/* Hero */
.nl-hero-title {{ font-size: 4.6rem; font-weight: 400; letter-spacing: -.025em; line-height: 1; }}
.nl-grad {{ background: linear-gradient(90deg, #4F6340, #7F9A6A 55%, #9CAF88); font-style: italic; padding-right: .06em; -webkit-background-clip: text;
  background-clip: text; color: transparent; }}
.nl-hero-sub {{ font-size: 1.25rem; opacity: .6; margin: 14px 0 22px; }}
.nl-step {{ font-size: .76rem; font-weight: 700; letter-spacing: .08em; color: {ACCENT}; text-transform: uppercase; }}

/* iOS-style segmented control */
[role="radiogroup"][aria-label="Mode"] {{
  background: rgba(255,255,255,0.45); padding: 4px; border-radius: 14px; gap: 2px; display: inline-flex;
  border: 1px solid rgba(255,255,255,0.8); }}
button[data-variant="segmented_control"] {{ border: none !important; background: transparent !important;
  border-radius: 10px !important; padding: 8px 22px !important; font-weight: 600 !important; color: #6B6B70 !important; }}
button[data-variant="segmented_control"][aria-checked="true"] {{ background: white !important; color: {INK} !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}

/* Food / Skin tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 18px; }}
.stTabs [data-baseweb="tab"] p {{ font-weight: 600; font-size: 1rem; }}
.stTabs [aria-selected="true"] p {{ color: {ACCENT} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {ACCENT} !important; }}
.nl-mini {{ font-size: .74rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; opacity: .5; margin: 4px 0 -4px; }}
.nl-route {{ font-size: .85rem; opacity: .6; margin-top: 10px; line-height: 1.4; }}

/* Goal chips */
button[data-variant="pills"] {{ border-radius: 999px !important; padding: 8px 16px !important;
  background: rgba(255,255,255,0.7) !important; border: 1px solid rgba(255,255,255,0.9) !important; color: {INK} !important; }}
button[data-variant="pills"][aria-pressed="true"] {{ background: {ACCENT} !important; color: white !important; border-color: {ACCENT} !important; }}
button[data-variant="pills"][aria-pressed="true"] * {{ color: white !important; }}

/* Upload */
[data-testid="stFileUploaderDropzone"] {{ min-height: 150px; flex-direction: column; justify-content: center; align-items: center;
  text-align: center; gap: 10px; border: 2px dashed rgba(79,99,64,0.4) !important; background: rgba(255,255,255,0.55) !important;
  border-radius: 18px !important; }}
[data-testid="stFileUploader"] label p {{ font-weight: 600; }}
button {{ border-radius: 12px !important; }}
[data-testid="stBaseButton-primary"] {{ background: linear-gradient(135deg, #6B8558, {ACCENT}) !important; border: none !important;
  color: white !important; font-weight: 700 !important; min-height: 54px; font-size: 1.05rem !important;
  box-shadow: 0 8px 22px rgba(79,99,64,0.30); }}
[data-testid="stBaseButton-tertiary"] {{ color: {ACCENT} !important; font-weight: 600 !important; }}

/* Scanning animation */
.nl-scan {{ position: relative; border-radius: 18px; overflow: hidden; margin: 8px auto; max-width: 440px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.10); }}
.nl-scan img {{ width: 100%; display: block; }}
.nl-scan::after {{ content: ""; position: absolute; inset: 0; background: rgba(79,99,64,0.06); }}
.nl-scan-line {{ position: absolute; left: -5%; right: -5%; height: 3px; background: #A8C98A; z-index: 2;
  box-shadow: 0 0 14px 4px rgba(156,190,120,0.85), 0 -30px 40px 10px rgba(156,175,136,0.25);
  animation: nl-sweep 1.4s ease-in-out infinite alternate; }}
@keyframes nl-sweep {{ from {{ top: 0%; }} to {{ top: 100%; }} }}
.nl-scan-text {{ text-align: center; font-weight: 600; margin-top: 14px; animation: nl-pulse 1.2s ease-in-out infinite; }}
@keyframes nl-pulse {{ 50% {{ opacity: .45; }} }}

/* Score ring with counting number */
@property --n {{ syntax: '<integer>'; initial-value: 0; inherits: false; }}
.nl-ring {{ position: relative; margin: 0 auto; }}
.nl-ring-num {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.nl-count {{ font-weight: 400; letter-spacing: -.02em; counter-reset: n var(--n); animation: nl-count 1.3s cubic-bezier(.2,.8,.2,1) forwards; }}
.nl-count::after {{ content: counter(n); }}
@keyframes nl-count {{ from {{ --n: 0; }} to {{ --n: var(--target); }} }}
.nl-ring-num small {{ font-size: .62rem; letter-spacing: .08em; opacity: .5; font-weight: 600; }}
@keyframes nl-fill {{ from {{ stroke-dashoffset: var(--circ); }} }}
.nl-arc {{ animation: nl-fill 1.3s cubic-bezier(.2,.8,.2,1); }}

/* Results bits */
.nl-product {{ display: flex; gap: 14px; align-items: center; padding-bottom: 16px; border-bottom: 1px solid rgba(0,0,0,0.06); }}
.nl-product img {{ width: 58px; height: 58px; object-fit: cover; border-radius: 12px; border: 1px solid rgba(0,0,0,.08); }}
.nl-product-name {{ font-weight: 400; font-size: 1.45rem; }}
.nl-product-meta {{ font-size: .82rem; opacity: .55; margin-top: 2px; }}
.nl-scored {{ display: inline-block; margin-top: 6px; font-size: .78rem; font-weight: 600; color: {ACCENT};
  background: {GOOD_BG}; padding: 3px 10px; border-radius: 999px; }}
.nl-hint {{ border-radius: 14px; padding: 10px 14px; margin-top: 12px; font-size: .9rem; line-height: 1.4;
  background: rgba(255,255,255,0.8); border: 1px dashed rgba(79,99,64,0.4); }}
.nl-status {{ text-align: center; font-weight: 400; font-size: 2.1rem; letter-spacing: -.01em; margin-top: 6px; }}
.nl-verdict {{ text-align: center; opacity: .68; margin: 4px auto 6px; max-width: 420px; line-height: 1.45; }}
.nl-sec {{ font-size: .76rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; opacity: .5; margin: 18px 0 2px; }}
.nl-stats {{ display: flex; gap: 10px; margin: 6px 0 4px; }}
.nl-stats div {{ flex: 1; border-radius: 16px; padding: 12px 14px; }}
.nl-stats b {{ display: block; font-size: 2.2rem; font-weight: 400; line-height: 1.1; }}
.nl-stats span {{ font-size: .82rem; font-weight: 600; }}
.nl-detail {{ border-radius: 16px; padding: 14px 16px; margin-top: 4px; background: rgba(255,255,255,0.8); border-left: 4px solid; }}
.nl-detail-title {{ font-weight: 700; }}
.nl-badge {{ font-size: .72rem; font-weight: 700; padding: 3px 9px; border-radius: 999px; margin-left: 8px; vertical-align: 2px; }}
.nl-detail-body {{ opacity: .75; margin-top: 4px; line-height: 1.45; }}
.nl-detail-for {{ margin-top: 8px; font-size: .86rem; line-height: 1.4; }}
.nl-detail-for b {{ color: {WARN}; }}
.nl-swap {{ border-radius: 16px; padding: 12px 16px; margin-top: 8px; background: rgba(255,255,255,0.8); line-height: 1.45; }}
.nl-swap-top {{ font-size: .82rem; opacity: .6; }}
.nl-swap-look {{ font-weight: 700; color: {ACCENT}; margin-top: 2px; }}
.nl-swap-why {{ opacity: .75; font-size: .92rem; margin-top: 2px; }}
.nl-tip {{ border-radius: 16px; padding: 14px 16px; margin-top: 16px; line-height: 1.45;
  background: linear-gradient(135deg, rgba(226,236,216,0.95), rgba(239,243,233,0.95)); }}
.nl-empty {{ text-align: center; padding: 6px 16px 12px; }}

/* Compare */
.nl-cmp {{ display: flex; gap: 14px; margin-top: 6px; }}
.nl-cmp-col {{ flex: 1; text-align: center; border-radius: 20px; padding: 18px 12px 16px; background: rgba(255,255,255,0.55);
  border: 2px solid transparent; position: relative; }}
.nl-cmp-col.win {{ border-color: {SAGE}; background: rgba(255,255,255,0.85); box-shadow: 0 8px 26px rgba(79,99,64,0.15); }}
.nl-win {{ position: absolute; top: -13px; left: 50%; transform: translateX(-50%); background: {ACCENT}; color: white;
  font-size: .75rem; font-weight: 700; padding: 4px 12px; border-radius: 999px; white-space: nowrap; }}
.nl-cmp-name {{ font-weight: 400; font-size: 1.25rem; margin-top: 6px; }}
.nl-cmp-type {{ font-size: .78rem; opacity: .55; margin-top: 2px; }}
.nl-cmp-row {{ font-size: .88rem; margin-top: 6px; }}
.nl-why {{ margin-top: 16px; border-radius: 16px; padding: 14px 16px; background: rgba(255,255,255,0.8); line-height: 1.5; }}
.nl-list {{ text-align: left; font-size: .85rem; margin-top: 12px; line-height: 1.4; }}
.nl-list ul {{ padding-left: 18px; margin: 4px 0 10px; }}
.nl-list li i {{ opacity: .65; }}
</style>
<div class="nl-nav">
  <div class="nl-logo"><div class="nl-logo-mark">🌿</div>NourishLens</div>
  <div class="nl-links"><a href="#goals" target="_self">How it works</a><a href="#results" target="_self">Results</a>
    <a class="nl-cta" href="#scan" target="_self">Scan a label</a></div>
</div>
""", unsafe_allow_html=True)


def to_b64(img, size=600):
    im = img.convert("RGB").copy()
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def ring(score, size=170, rid="r"):
    pct = None if score is None else max(0, min(100, int(score)))
    c1, c2 = (("#B9CFA4", "#4F6340") if (pct or 0) >= 70 else ("#FFC27A", "#E07A2E") if (pct or 0) >= 40
              else ("#FF9A8B", "#D9534F"))
    circ = 2 * math.pi * 46
    arc = "" if pct is None else (
        f'<circle class="nl-arc" style="--circ:{circ:.1f}" cx="56" cy="56" r="46" fill="none" stroke="url(#{rid})" '
        f'stroke-width="10" stroke-linecap="round" stroke-dasharray="{circ:.1f}" '
        f'stroke-dashoffset="{circ * (1 - pct / 100):.1f}" transform="rotate(-90 56 56)"/>')
    num = ('<span style="font-size:2.6rem;font-weight:400">–</span>' if pct is None else
           f'<span class="nl-count" style="--target:{pct};font-size:{size * 0.27:.0f}px"></span>')
    return (f'<div class="nl-ring" style="width:{size}px;height:{size}px">'
            f'<svg width="{size}" height="{size}" viewBox="0 0 112 112"><defs><linearGradient id="{rid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<circle cx="56" cy="56" r="46" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="10"/>{arc}</svg>'
            f'<div class="nl-ring-num">{num}<small>OUT OF 100</small></div></div>')


def status(score):
    return "Great fit" if score >= 70 else "A mixed fit" if score >= 40 else "Worth a closer look"


def scanning(img, text="Reading the label…"):
    return (f'<div class="nl-scan"><img src="{to_b64(img)}"><div class="nl-scan-line"></div></div>'
            f'<div class="nl-scan-text">{text}</div>')


def same(a, b):
    a, b = a.lower().strip(), b.lower().strip()
    return a == b or a in b or b in a


def kind_of(r, name):
    if any(same(t.ingredient, name) for t in r.triggers):
        return "warn"
    if any(same(w.ingredient, name) for w in r.supportive_wins):
        return "good"
    return "neutral"


def win_sentence(w):
    """One friendly sentence about the top supportive ingredient, or nothing if there isn't one."""
    if not w.supportive_wins or not w.supportive_wins[0].benefit:
        return ""
    top = w.supportive_wins[0]
    return f'{top.ingredient} adds {top.benefit[0].lower() + top.benefit[1:]}'


def pros_cons(rr):
    """Two short lists for a compare column: what's flagged (and who it matters for) and what's working."""
    bad = "".join(f'<li><b>{t.ingredient}</b>: {t.explanation}'
                  + (f' <i>Matters most for {t.matters_most_for}.</i>' if t.matters_most_for else "")
                  + '</li>' for t in rr.triggers) \
        or '<li style="opacity:.6">Nothing flagged</li>'
    good = "".join(f'<li><b>{w.ingredient}</b>: {w.benefit}</li>' for w in rr.supportive_wins) \
        or '<li style="opacity:.6">Nothing standout</li>'
    return (f'<div class="nl-list"><div style="color:{WARN}"><b>Worth knowing</b></div><ul>{bad}</ul>'
            f'<div style="color:{GOOD}"><b>Working for you</b></div><ul>{good}</ul></div>')


def is_skincare(r):
    t = r.product_type.lower()
    return "skin" in t or "cosmetic" in t


def scored_for(profile, skin):
    """What the score was measured against, e.g. 'Dry skin, Sensitive' or 'Hormonal acne, Blood sugar'."""
    if skin:
        parts = ([f"{profile['skin_type']} skin"] if profile["skin_type"] else []) + profile["concerns"]
        return ", ".join(parts)
    return ", ".join(profile["food"])


def swaps_html(r):
    if not r.swaps:
        return ""
    cards = "".join(f'<div class="nl-swap"><div class="nl-swap-top">Instead of {s.instead_of}</div>'
                    f'<div class="nl-swap-look">→ {s.look_for}</div><div class="nl-swap-why">{s.why}</div></div>'
                    for s in r.swaps)
    return '<div class="nl-sec">Better matches to look for</div>' + cards


# ---------- Hero ----------
st.markdown('<div class="nl-hero-title">Know what\'s <span class="nl-grad">in it.</span></div>'
            '<div class="nl-hero-sub">Snap any food or skincare label. See how every ingredient fits your goals.</div>',
            unsafe_allow_html=True)
mode = st.segmented_control("Mode", ["Single scan", "Compare two"], default="Single scan",
                            label_visibility="collapsed", key="mode") or "Single scan"
st.write("")

left, right = st.columns([5, 6], gap="large")

with left:
    with st.container(key="card_goals"):
        st.markdown('<div class="nl-step" id="goals">Step 1</div>', unsafe_allow_html=True)
        st.subheader("What are you working on?", anchor=False)
        food_tab, skin_tab = st.tabs(["🥗  Food goals", "🧴  Skin profile"])
        with food_tab:
            picked = st.pills("Food goals", list(FOOD_GOALS), selection_mode="multi", default=["Hormonal acne"],
                              label_visibility="collapsed") or []
        with skin_tab:
            st.markdown('<div class="nl-mini">Skin type</div>', unsafe_allow_html=True)
            skin_type = st.pills("Skin type", SKIN_TYPES, selection_mode="single", label_visibility="collapsed")
            st.markdown('<div class="nl-mini">Concerns</div>', unsafe_allow_html=True)
            skin_concerns = st.pills("Skin concerns", SKIN_CONCERNS, selection_mode="multi",
                                     label_visibility="collapsed") or []
        st.markdown('<div class="nl-route">Food is scored against your food goals, skincare against your skin profile. '
                    'NourishLens figures out which one it is from the label.</div>', unsafe_allow_html=True)
        with st.expander("Add custom filters"):
            custom_rules = st.text_input("Anything specific to flag", placeholder="e.g. whey, coconut oil, fragrance")

        food_goals = [FOOD_GOALS[p] for p in picked]
        profile = {"food": list(picked), "skin_type": skin_type, "concerns": list(skin_concerns)}

    with st.container(key="card_label"):
        st.markdown('<div class="nl-step" id="scan">Step 2</div>', unsafe_allow_html=True)
        if mode == "Single scan":
            st.subheader("Scan the ingredient label", anchor=False)
            up = st.file_uploader("📷  Drop a photo or take one", type=["jpg", "jpeg", "png", "webp"])
            if st.button("No photo handy? Try a sample label →", type="tertiary"):
                st.session_state.sample = True
            img = Image.open(up) if up else (Image.open("sample_label.png") if st.session_state.get("sample") else None)
            if img:
                st.image(img, width=170)
            if st.button("Analyze Label", type="primary", use_container_width=True, disabled=img is None):
                st.session_state.run, st.session_state.img = "single", img
        else:
            st.subheader("Compare two products", anchor=False)
            a, b = st.columns(2)
            up_a = a.file_uploader("Product A", type=["jpg", "jpeg", "png", "webp"])
            up_b = b.file_uploader("Product B", type=["jpg", "jpeg", "png", "webp"])
            if st.button("No photos handy? Try two sample labels →", type="tertiary"):
                st.session_state.sample2 = True
            s2 = st.session_state.get("sample2")
            img_a = Image.open(up_a) if up_a else (Image.open("sample_label.png") if s2 else None)
            img_b = Image.open(up_b) if up_b else (Image.open("sample_label_2.png") if s2 else None)
            if img_a and img_b:
                a.image(img_a, use_container_width=True)
                b.image(img_b, use_container_width=True)
            if st.button("⇄  Compare", type="primary", use_container_width=True, disabled=not (img_a and img_b)):
                st.session_state.run, st.session_state.imgs = "compare", (img_a, img_b)

with right:
    with st.container(key="card_results"):
        st.markdown('<div class="nl-step" id="results">Your results</div>', unsafe_allow_html=True)
        run = st.session_state.pop("run", None)
        args = (food_goals, skin_type, skin_concerns, custom_rules)

        if run == "single":
            ph = st.empty()
            ph.markdown(scanning(st.session_state.img, "Reading the ingredients…"), unsafe_allow_html=True)
            try:
                st.session_state.result = analyze_label(st.session_state.img, *args)
                st.session_state.thumb = to_b64(st.session_state.img, 160)
                st.session_state.result_profile = profile  # remember what this result was scored for
            except Exception:
                st.error("Couldn't analyze this label. Try again, or use a sharper photo.")
            ph.empty()
        elif run == "compare":
            ph = st.empty()
            ia, ib = st.session_state.imgs
            ph.markdown(f'<div style="display:flex;gap:12px">{scanning(ia, "Reading A…")}{scanning(ib, "Reading B…")}</div>',
                        unsafe_allow_html=True)
            try:
                st.session_state.cmp = (analyze_label(ia, *args), analyze_label(ib, *args))
                st.session_state.cmp_profile = profile
            except Exception:
                st.error("Couldn't analyze these labels. Try again, or use sharper photos.")
            ph.empty()

        r = st.session_state.get("result")
        cmp = st.session_state.get("cmp")

        if mode == "Single scan" and r:
            prof = st.session_state.get("result_profile", profile)
            skin = is_skincare(r)
            target = scored_for(prof, skin)

            # Remove duplicate ingredient names (duplicates would break the tappable tags)
            ingredients = list(dict.fromkeys(i for i in r.all_ingredients if i.strip()))
            kinds = {name: kind_of(r, name) for name in ingredients}
            n_neutral = sum(1 for k in kinds.values() if k == "neutral")

            scored_chip = (f'<div class="nl-scored">Scored for: {target}</div>' if target else
                           f'<div class="nl-scored">Scored for: general {"skin health" if skin else "wellness"}</div>')
            st.markdown(
                f'<div class="nl-product"><img src="{st.session_state.thumb}"><div>'
                f'<div class="nl-product-name">{r.product_name}</div>'
                f'<div class="nl-product-meta">{r.product_type} · {len(ingredients)} ingredients</div>'
                f'{scored_chip}</div></div>'
                + ('' if target else
                   f'<div class="nl-hint">Want a personal score? Set your '
                   f'{"skin type and concerns under <b>Skin profile</b>" if skin else "<b>Food goals</b>"} '
                   f'in Step 1, then analyze again.</div>')
                + '<div style="height:18px"></div>'
                + ring(r.alignment_score, 180, "single")
                + f'<div class="nl-status">{status(r.alignment_score)}</div><div class="nl-verdict">{r.verdict_headline}</div>'
                + f'<div class="nl-stats">'
                  f'<div style="background:{WARN_BG};color:{WARN}"><b>{len(r.triggers)}</b><span>Worth knowing</span></div>'
                  f'<div style="background:{GOOD_BG};color:{GOOD}"><b>{len(r.supportive_wins)}</b><span>Working for you</span></div>'
                  f'<div style="background:rgba(255,255,255,.7);color:{NEUTRAL}"><b>{n_neutral}</b><span>Neutral</span></div></div>'
                + '<div class="nl-sec">Every ingredient · tap one to learn more</div>',
                unsafe_allow_html=True)

            # Color each ingredient tag by its kind
            styles = {"warn": (WARN_BG, WARN), "good": (GOOD_BG, GOOD), "neutral": (NEUTRAL_BG, NEUTRAL)}
            css = ""
            for i, name in enumerate(ingredients, start=1):
                bg, fg = styles[kinds[name]]
                css += (f'.st-key-tags button[data-variant="pills"]:nth-child({i}) {{ background:{bg} !important; '
                        f'color:{fg} !important; border:1px solid transparent !important; font-weight:600; }}')
            css += ('.st-key-tags button[data-variant="pills"][aria-pressed="true"] { box-shadow: 0 0 0 2px currentColor; }'
                    '.st-key-tags button[data-variant="pills"][aria-pressed="true"] * { color: inherit !important; }')
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

            with st.container(key="tags"):
                # Default to the first flagged ingredient that actually appears in the list
                first_flag = next((n for n in ingredients if kinds[n] == "warn"), None)
                chosen = st.pills("Ingredients", ingredients, default=first_flag, label_visibility="collapsed")

            if chosen:
                k = kinds.get(chosen, "neutral")
                extra = ""
                if k == "warn":
                    t = next(t for t in r.triggers if same(t.ingredient, chosen))
                    color, badge, body = WARN, f'<span class="nl-badge" style="background:{WARN_BG};color:{WARN}">{t.pathway}</span>', t.explanation
                    if t.matters_most_for:
                        extra = f'<div class="nl-detail-for"><b>Matters most for:</b> {t.matters_most_for}</div>'
                elif k == "good":
                    w = next(w for w in r.supportive_wins if same(w.ingredient, chosen))
                    color, badge, body = GOOD, f'<span class="nl-badge" style="background:{GOOD_BG};color:{GOOD}">Supports you</span>', w.benefit
                else:
                    color, badge, body = "#B9B9BE", "", "Nothing to note for your goals."
                st.markdown(f'<div class="nl-detail" style="border-color:{color}"><div class="nl-detail-title">{chosen}{badge}</div>'
                            f'<div class="nl-detail-body">{body}</div>{extra}</div>', unsafe_allow_html=True)

            st.markdown(swaps_html(r) + f'<div class="nl-tip">💡 <b>Try this:</b> {r.non_restrictive_tip}</div>',
                        unsafe_allow_html=True)

        elif mode == "Compare two" and cmp:
            ra, rb = cmp
            win = 0 if ra.alignment_score >= rb.alignment_score else 1
            cols = ""
            for idx, (rr, lab) in enumerate([(ra, "A"), (rb, "B")]):
                badge = '<div class="nl-win">✓ Better fit for you</div>' if idx == win else ""
                cols += (f'<div class="nl-cmp-col {"win" if idx == win else ""}">{badge}'
                         + ring(rr.alignment_score, 130, f"c{idx}")
                         + f'<div class="nl-cmp-name">{lab} · {rr.product_name}</div>'
                           f'<div class="nl-cmp-type">{rr.product_type}</div>'
                           f'<div class="nl-cmp-row" style="color:{WARN}">● {len(rr.triggers)} worth knowing</div>'
                           f'<div class="nl-cmp-row" style="color:{GOOD}">● {len(rr.supportive_wins)} working for you</div>'
                         + pros_cons(rr) + '</div>')
            w, l = (ra, rb) if win == 0 else (rb, ra)
            mixed = is_skincare(ra) != is_skincare(rb)
            note = ('<div class="nl-hint">Heads up: one of these is food and one is skincare, so each was scored '
                    'against a different part of your profile. Compare two of the same kind for a fairer match-up.</div>'
                    if mixed else "")
            st.markdown(
                f'<div class="nl-cmp">{cols}</div>{note}'
                f'<div class="nl-why"><b>Why {w.product_name} wins:</b> {len(w.triggers)} flagged vs {len(l.triggers)}, and '
                f'{len(w.supportive_wins)} ingredients working for you vs {len(l.supportive_wins)}. '
                f'{win_sentence(w)}</div>'
                + swaps_html(l)
                + f'<div class="nl-tip">💡 <b>Try this:</b> {w.non_restrictive_tip}</div>',
                unsafe_allow_html=True)
        else:
            hint = "Add two labels, then tap Compare." if mode == "Compare two" else "Set your goals, add a label, then tap Analyze."
            st.markdown(ring(None, 170) + f'<div class="nl-empty" style="margin-top:14px"><b>Your results will appear here</b><br>'
                        f'<span style="opacity:.6">{hint}</span></div>', unsafe_allow_html=True)