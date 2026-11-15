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

GOALS = {
    "Hormonal acne": "Acne: Hormonal & Insulin Pathways",
    "Gut & inflammation": "Acne: Gut & Inflammation",
    "Skin barrier": "Acne: Topical Skin Barrier (Skincare)",
    "Blood sugar": "Blood Sugar Balance",
    "Lean bulk": "Athletic: Lean Bulk (High Protein/Calories)",
    "Weight loss": "Weight Loss / Calorie Deficit",
}

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
.nl-cmp-row {{ font-size: .88rem; margin-top: 6px; }}
.nl-why {{ margin-top: 16px; border-radius: 16px; padding: 14px 16px; background: rgba(255,255,255,0.8); line-height: 1.5; }}
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
        picked = st.pills("Goals", list(GOALS), selection_mode="multi", default=["Hormonal acne"],
                          label_visibility="collapsed")
        selected_goals = [GOALS[p] for p in picked or []]
        with st.expander("Add custom filters"):
            custom_rules = st.text_input("Anything specific to flag", placeholder="e.g. whey, coconut oil, seed oils")

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

        if run == "single":
            ph = st.empty()
            ph.markdown(scanning(st.session_state.img, "Reading the ingredients…"), unsafe_allow_html=True)
            try:
                st.session_state.result = analyze_label(st.session_state.img, selected_goals, custom_rules)
                st.session_state.thumb = to_b64(st.session_state.img, 160)
            except Exception:
                st.error("Couldn't analyze this label. Try again, or use a sharper photo.")
            ph.empty()
        elif run == "compare":
            ph = st.empty()
            ia, ib = st.session_state.imgs
            ph.markdown(f'<div style="display:flex;gap:12px">{scanning(ia, "Reading A…")}{scanning(ib, "Reading B…")}</div>',
                        unsafe_allow_html=True)
            try:
                st.session_state.cmp = (analyze_label(ia, selected_goals, custom_rules),
                                        analyze_label(ib, selected_goals, custom_rules))
            except Exception:
                st.error("Couldn't analyze these labels. Try again, or use sharper photos.")
            ph.empty()

        r = st.session_state.get("result")
        cmp = st.session_state.get("cmp")

        if mode == "Single scan" and r:
            # Remove duplicate ingredient names (duplicates would break the tappable tags)
            ingredients = list(dict.fromkeys(i for i in r.all_ingredients if i.strip()))
            kinds = {name: kind_of(r, name) for name in ingredients}
            n_neutral = sum(1 for k in kinds.values() if k == "neutral")

            st.markdown(
                f'<div class="nl-product"><img src="{st.session_state.thumb}"><div>'
                f'<div class="nl-product-name">{r.product_name}</div>'
                f'<div class="nl-product-meta">{r.product_type} · {len(ingredients)} ingredients · Scanned just now</div>'
                f'</div></div><div style="height:18px"></div>'
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
                if k == "warn":
                    t = next(t for t in r.triggers if same(t.ingredient, chosen))
                    color, badge, body = WARN, f'<span class="nl-badge" style="background:{WARN_BG};color:{WARN}">{t.pathway}</span>', t.explanation
                elif k == "good":
                    w = next(w for w in r.supportive_wins if same(w.ingredient, chosen))
                    color, badge, body = GOOD, f'<span class="nl-badge" style="background:{GOOD_BG};color:{GOOD}">Supports you</span>', w.benefit
                else:
                    color, badge, body = "#B9B9BE", "", "Nothing to note for your goals."
                st.markdown(f'<div class="nl-detail" style="border-color:{color}"><div class="nl-detail-title">{chosen}{badge}</div>'
                            f'<div class="nl-detail-body">{body}</div></div>', unsafe_allow_html=True)

            st.markdown(f'<div class="nl-tip">💡 <b>Try this:</b> {r.non_restrictive_tip}</div>', unsafe_allow_html=True)

        elif mode == "Compare two" and cmp:
            ra, rb = cmp
            win = 0 if ra.alignment_score >= rb.alignment_score else 1
            cols = ""
            for idx, (rr, lab) in enumerate([(ra, "A"), (rb, "B")]):
                badge = '<div class="nl-win">✓ Better fit for you</div>' if idx == win else ""
                cols += (f'<div class="nl-cmp-col {"win" if idx == win else ""}">{badge}'
                         + ring(rr.alignment_score, 130, f"c{idx}")
                         + f'<div class="nl-cmp-name">{lab} · {rr.product_name}</div>'
                           f'<div class="nl-cmp-row" style="color:{WARN}">● {len(rr.triggers)} worth knowing</div>'
                           f'<div class="nl-cmp-row" style="color:{GOOD}">● {len(rr.supportive_wins)} working for you</div></div>')
            w, l = (ra, rb) if win == 0 else (rb, ra)
            st.markdown(
                f'<div class="nl-cmp">{cols}</div>'
                f'<div class="nl-why"><b>Why {w.product_name} wins:</b> {len(w.triggers)} flagged vs {len(l.triggers)}, and '
                f'{len(w.supportive_wins)} ingredients working for you vs {len(l.supportive_wins)}. '
                f'{win_sentence(w)}</div>'
                f'<div class="nl-tip">💡 <b>Try this:</b> {w.non_restrictive_tip}</div>',
                unsafe_allow_html=True)
        else:
            hint = "Add two labels, then tap Compare." if mode == "Compare two" else "Pick your goals, add a label, then tap Analyze."
            st.markdown(ring(None, 170) + f'<div class="nl-empty" style="margin-top:14px"><b>Your results will appear here</b><br>'
                        f'<span style="opacity:.6">{hint}</span></div>', unsafe_allow_html=True)