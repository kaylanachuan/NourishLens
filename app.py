import streamlit as st
from PIL import Image
from analyzer import analyze_label

st.set_page_config(page_title="NourishLens", page_icon="🌿", layout="centered")

# Header
st.title("🌿 NourishLens")
st.caption("Personalized, non-restrictive grocery & beauty scanning powered by Gemini Vision")

# 1. Profile / Goal Toggles (Users can pick multiple!)
st.subheader("1. Your Personal Health Profile")
selected_goals = st.multiselect(
    "Select one or more active goals:",
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

custom_rules = st.text_input(
    "Custom filters (optional):",
    placeholder="e.g., Flag whey, coconut oil, seed oils, or pore-clogging esters",
)

# 2. Image Upload
st.subheader("2. Scan an Ingredient Label")
uploaded_file = st.file_uploader("Upload or take a photo of the ingredients panel", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", width=260)

    if st.button("Run NourishLens Analysis", type="primary", use_container_width=True):
        with st.spinner("Reading label & checking pathways with Gemini..."):
            try:
                result = analyze_label(image, selected_goals, custom_rules)

                st.divider()
                col1, col2 = st.columns([1, 2])
                col1.metric("Alignment Score", f"{result.alignment_score}/100")
                col2.markdown(f"**Category:** {result.product_type}\n\n{result.verdict_headline}")

                st.markdown("### ⚠️ Potential Triggers for Your Profile")
                if result.triggers:
                    for t in result.triggers:
                        st.warning(f"**{t.ingredient}** — *{t.pathway}*\n\n{t.explanation}")
                else:
                    st.success("No major triggers flagged for your selected goals!")

                st.markdown("### ✨ Supportive Nutrients & Wins")
                if result.supportive_wins:
                    for w in result.supportive_wins:
                        st.success(f"**{w.ingredient}**: {w.benefit}")
                else:
                    st.write("No standout micronutrient or barrier wins detected on this label.")

                st.info(f"💡 **Non-Restrictive Swap / Pairing Tip:** {result.non_restrictive_tip}")

            except Exception as e:
                st.error(f"Something went wrong: {e}")