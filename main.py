import streamlit as st
import fitz
import numpy as np
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide")

# -------------------------------
# HEADER (PRO LOOK)
# -------------------------------
st.markdown("""
<style>
.title {
    font-size:40px;
    font-weight:700;
}
.subtitle {
    color:gray;
    margin-bottom:20px;
}
</style>

<div class="title">🚀 PDF Toolkit PRO</div>
<div class="subtitle">Compare • AI Compare • Convert • Sign</div>
""", unsafe_allow_html=True)

# -------------------------------
# NAVIGATION
# -------------------------------
menu = st.radio(
    "Select Feature",
    ["Compare", "AI Compare", "Convert", "Sign PRO"],
    horizontal=True
)

# -------------------------------
# SIGN PRO FEATURE
# -------------------------------
if menu == "Sign PRO":

    st.markdown("## ✍️ Sign PRO")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file:
        pdf_bytes = pdf_file.read()

        if len(pdf_bytes) == 0:
            st.error("Empty PDF")
            st.stop()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        if total_pages == 0:
            st.error("PDF has no pages")
            st.stop()

        # -------------------------------
        # PAGE SELECT (FIXED)
        # -------------------------------
        page_num = st.slider(
            "Select Page",
            min_value=1,
            max_value=int(total_pages),
            value=1
        )

        page = doc[page_num - 1]

        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # -------------------------------
        # DRAW SIGNATURE
        # -------------------------------
        st.subheader("✍️ Draw Signature")

        sig_canvas = st_canvas(
            stroke_width=4,
            stroke_color="#FFFFFF",
            background_color="#000000",
            height=200,
            width=400,
            drawing_mode="freedraw",
            key="sig",
        )

        signature = None

        if sig_canvas.image_data is not None:
            sig = sig_canvas.image_data

            sig = (sig[:, :, :3]).astype(np.uint8)
            gray = np.mean(sig, axis=2)

            mask = gray > 50
            sig[mask] = [0, 0, 0]

            rgba = np.zeros((sig.shape[0], sig.shape[1], 4), dtype=np.uint8)
            rgba[:, :, :3] = sig
            rgba[:, :, 3] = np.where(mask, 0, 255)

            signature = Image.fromarray(rgba)

        # -------------------------------
        # PLACE SIGNATURE
        # -------------------------------
        st.subheader("🎯 Place Signature")

        canvas = st_canvas(
            background_image=img,
            update_streamlit=True,
            height=img.height,
            width=img.width,
            drawing_mode="rect",
            key="placement",
        )

        rect = None

        if canvas.json_data is not None:
            objects = canvas.json_data["objects"]
            if len(objects) > 0:
                rect = objects[-1]

        # -------------------------------
        # LIVE PREVIEW
        # -------------------------------
        st.subheader("👀 Live Preview")

        preview_img = img.copy()

        if rect and signature:
            x = int(rect["left"])
            y = int(rect["top"])
            w = int(rect["width"])
            h = int(rect["height"])

            sig_resized = signature.resize((w, h))
            preview_img.paste(sig_resized, (x, y), sig_resized)

        st.image(preview_img, use_column_width=True)

        # -------------------------------
        # MULTI PAGE
        # -------------------------------
        st.subheader("📄 Apply to Pages")

        apply_all = st.checkbox("Apply to ALL pages")
        pages_selected = st.multiselect(
            "Or select pages",
            list(range(1, total_pages + 1)),
            default=[page_num],
        )

        # -------------------------------
        # EXPORT PDF
        # -------------------------------
        if st.button("🚀 Generate Signed PDF"):

            if not signature or not rect:
                st.error("Draw signature AND place rectangle")
            else:
                for i in range(total_pages):
                    if apply_all or (i + 1 in pages_selected):

                        page = doc[i]

                        x = rect["left"]
                        y = rect["top"]
                        w = rect["width"]
                        h = rect["height"]

                        rect_pdf = fitz.Rect(x, y, x + w, y + h)

                        img_bytes = io.BytesIO()
                        signature.save(img_bytes, format="PNG")

                        page.insert_image(rect_pdf, stream=img_bytes.getvalue())

                output = io.BytesIO()
                doc.save(output)

                st.success("✅ PDF Signed!")

                st.download_button(
                    "⬇️ Download Signed PDF",
                    data=output.getvalue(),
                    file_name="signed.pdf",
                    mime="application/pdf",
                )

# -------------------------------
# PLACEHOLDER FEATURES
# -------------------------------
elif menu == "Compare":
    st.info("Compare coming next...")

elif menu == "AI Compare":
    st.info("AI Compare coming next...")

elif menu == "Convert":
    st.info("Convert coming next...")
