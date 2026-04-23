import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(layout="wide")

st.title("✍️ Sign PRO – Stable Version (No pdf2image)")

# Upload PDF
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    total_pages = len(doc)

    # Stabiler Page Selector (kein Slider Bug mehr)
    page_num = st.number_input(
        "Select Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1
    )

    page = doc[page_num - 1]

    # Render Page als Image
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.subheader("📄 PDF Preview")

    st.image(img, use_container_width=True)

    # Position auswählen
    st.subheader("📍 Position")

    col1, col2 = st.columns(2)

    with col1:
        x = st.slider("X Position", 0, img.width, img.width // 2)

    with col2:
        y = st.slider("Y Position", 0, img.height, img.height // 2)

    # Signature Upload
    st.subheader("✍️ Upload Signature")

    sig_file = st.file_uploader("Upload Signature (PNG)", type=["png"])

    if sig_file:

        sig = Image.open(sig_file).convert("RGBA")

        # Preview
        st.subheader("🔍 Live Preview")

        preview = img.copy()
        preview.paste(sig, (x, y), sig)

        st.image(preview, use_container_width=True)

        # Sign PDF
        if st.button("💾 Sign PDF"):

            # Signature vorbereiten
            sig_bytes = sig_file.read()
            sig_rect = fitz.Rect(x, y, x + 150, y + 50)

            # Y Koordinate fixen (PyMuPDF hat andere Origin)
            page_height = page.rect.height
            corrected_rect = fitz.Rect(
                x,
                page_height - y - 50,
                x + 150,
                page_height - y
            )

            page.insert_image(corrected_rect, stream=sig_bytes)

            output = io.BytesIO()
            doc.save(output)

            st.success("✅ PDF signed successfully!")

            st.download_button(
                "Download Signed PDF",
                data=output.getvalue(),
                file_name="signed.pdf"
            )
