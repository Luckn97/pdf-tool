import streamlit as st
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide")

# -------------------------------
# HEADER
# -------------------------------
st.markdown("""
<style>
.title {
    font-size:42px;
    font-weight:700;
}
.subtitle {
    color:#888;
    margin-bottom:25px;
}
</style>

<div class="title">🚀 PDF Toolkit PRO</div>
<div class="subtitle">Compare • AI Compare • Convert • Sign</div>
""", unsafe_allow_html=True)

# -------------------------------
# MENU
# -------------------------------
menu = st.radio(
    "",
    ["Compare", "AI Compare", "Convert", "Sign PRO"],
    horizontal=True
)

# ===============================
# SIGN PRO
# ===============================
if menu == "Sign PRO":

    st.markdown("## ✍️ Sign PRO")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file is None:
        st.info("Upload a PDF to start")
        st.stop()

    try:
        pdf_bytes = pdf_file.read()

        if not pdf_bytes:
            st.error("PDF is empty")
            st.stop()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    except Exception as e:
        st.error("Failed to read PDF")
        st.stop()

    # -------------------------------
    # SAFE PAGE COUNT
    # -------------------------------
    total_pages = int(len(doc))

    if total_pages <= 0:
        st.error("PDF has no pages")
        st.stop()

    # -------------------------------
    # SAFE SLIDER (FIXED)
    # -------------------------------
    page_num = st.slider(
        "Select Page",
        min_value=1,
        max_value=max(1, total_pages),
        value=1,
        step=1
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
        key="signature_canvas",
    )

    signature = None

    if sig_canvas.image_data is not None:
        sig = sig_canvas.image_data

        sig = (sig[:, :, :3]).astype(np.uint8)
        gray = np.mean(sig, axis=2)

        mask = gray > 40

        rgba = np.zeros((sig.shape[0], sig.shape[1], 4), dtype=np.uint8)
        rgba[:, :, :3] = sig
        rgba[:, :, 3] = np.where(mask, 0, 255)

        signature = Image.fromarray(rgba)

    # -------------------------------
    # PLACE SIGNATURE
    # -------------------------------
    st.subheader("🎯 Place Signature (Drag & Resize)")

    canvas = st_canvas(
        background_image=img,
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="rect",
        key="placement_canvas",
    )

    rect = None

    if canvas.json_data is not None:
        objects = canvas.json_data.get("objects", [])
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
        w = max(1, int(rect["width"]))
        h = max(1, int(rect["height"]))

        sig_resized = signature.resize((w, h))

        preview_img.paste(sig_resized, (x, y), sig_resized)

    st.image(preview_img, use_column_width=True)

    # -------------------------------
    # MULTI PAGE
    # -------------------------------
    st.subheader("📄 Apply to Pages")

    apply_all = st.checkbox("Apply to ALL pages")

    pages_selected = st.multiselect(
        "Select specific pages",
        list(range(1, total_pages + 1)),
        default=[page_num],
    )

    # -------------------------------
    # GENERATE PDF
    # -------------------------------
    if st.button("🚀 Generate Signed PDF"):

        if signature is None:
            st.error("Draw a signature first")
            st.stop()

        if rect is None:
            st.error("Select placement area")
            st.stop()

        try:
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

            st.success("✅ PDF Signed Successfully")

            st.download_button(
                "⬇️ Download PDF",
                data=output.getvalue(),
                file_name="signed.pdf",
                mime="application/pdf",
            )

        except Exception as e:
            st.error("Error while generating PDF")

# ===============================
# PLACEHOLDER FEATURES
# ===============================
elif menu == "Compare":
    st.markdown("## 📊 Compare")
    st.info("Coming next...")

elif menu == "AI Compare":
    st.markdown("## 🤖 AI Compare")
    st.info("Coming next...")

elif menu == "Convert":
    st.markdown("## 🔄 Convert")
    st.info("Coming next...")
