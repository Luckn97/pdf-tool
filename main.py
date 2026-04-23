import streamlit as st
import pdfplumber
import difflib
from io import BytesIO
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# PDF SIGN
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")

# ======================
# HERO UI
# ======================
st.markdown("""
<style>
.big-title {
    font-size: 42px;
    font-weight: 700;
}
.subtitle {
    color: #aaa;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🚀 PDF Toolkit PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Compare • Convert • Sign PDFs instantly</div>', unsafe_allow_html=True)

# ======================
# NAVIGATION
# ======================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Compare", "🧠 AI Compare", "🔄 Convert", "✍️ Sign"])

# ======================
# HELPER
# ======================
def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# ======================
# COMPARE
# ======================
with tab1:
    st.subheader("Compare PDFs")

    f1 = st.file_uploader("PDF 1", type="pdf", key="c1")
    f2 = st.file_uploader("PDF 2", type="pdf", key="c2")

    if f1 and f2:
        t1 = extract_text(f1)
        t2 = extract_text(f2)

        diff = list(difflib.ndiff(t1.splitlines(), t2.splitlines()))

        for line in diff:
            if line.startswith("- "):
                st.error(line)
            elif line.startswith("+ "):
                st.success(line)

# ======================
# AI COMPARE
# ======================
with tab2:
    st.subheader("AI Compare (Smart Diff)")

    f1 = st.file_uploader("Original", type="pdf", key="a1")
    f2 = st.file_uploader("Modified", type="pdf", key="a2")

    if f1 and f2:
        t1 = extract_text(f1)
        t2 = extract_text(f2)

        changes = list(difflib.unified_diff(t1.split(), t2.split()))

        for line in changes:
            if line.startswith("-"):
                st.error(f"Removed: {line}")
            elif line.startswith("+"):
                st.success(f"Added: {line}")

# ======================
# CONVERT
# ======================
with tab3:
    st.subheader("Convert TXT → PDF")

    txt = st.file_uploader("Upload TXT", type="txt")

    if txt:
        content = txt.read().decode("utf-8")

        buffer = BytesIO()
        c = canvas.Canvas(buffer)

        y = 800
        for line in content.split("\n"):
            c.drawString(50, y, line)
            y -= 15

        c.save()
        buffer.seek(0)

        st.download_button("Download PDF", buffer, "converted.pdf")

# ======================
# SIGN (REAL DRAW)
# ======================
with tab4:
    st.subheader("Draw & Sign PDF")

    pdf_file = st.file_uploader("Upload PDF", type="pdf")

    st.markdown("### ✍️ Draw Signature")

    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=3,
        stroke_color="white",  # 👈 FIX: sichtbar im Darkmode
        background_color="#111",
        height=200,
        width=400,
        drawing_mode="freedraw",
        key="canvas"
    )

    if pdf_file and canvas_result.image_data is not None:

        img = canvas_result.image_data.astype("uint8")

        # Transparent machen
        img_pil = Image.fromarray(img).convert("RGBA")
        datas = img_pil.getdata()

        newData = []
        for item in datas:
            if item[0] < 50 and item[1] < 50 and item[2] < 50:
                newData.append((255, 255, 255, 0))
            else:
                newData.append((0, 0, 0, 255))

        img_pil.putdata(newData)

        # Save temp image
        sig_buffer = BytesIO()
        img_pil.save(sig_buffer, format="PNG")
        sig_buffer.seek(0)

        st.image(img_pil, caption="Signature Preview")

        if st.button("Sign PDF"):

            reader = PdfReader(pdf_file)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Overlay PDF
            packet = BytesIO()
            can = canvas.Canvas(packet)

            can.drawImage(Image.open(sig_buffer), 100, 100, width=150, height=50)
            can.save()

            packet.seek(0)
            overlay = PdfReader(packet)

            writer.pages[0].merge_page(overlay.pages[0])

            output = BytesIO()
            writer.write(output)
            output.seek(0)

            st.download_button("Download Signed PDF", output, "signed.pdf")
