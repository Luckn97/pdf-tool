import streamlit as st
import pdfplumber
import difflib
from io import BytesIO

st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")

# ======================
# HEADER
# ======================
st.title("🚀 PDF Toolkit PRO")
st.markdown("Compare • Convert • Sign")

# ======================
# MENU (FIXED)
# ======================
menu = st.radio(
    "Select Feature",
    ["Compare", "AI Compare", "Convert", "Sign"],
    horizontal=True
)

# ======================
# HELPER: TEXT EXTRACT
# ======================
def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# ======================
# COMPARE (BASIC)
# ======================
if menu == "Compare":
    st.header("📊 PDF Compare")

    file1 = st.file_uploader("Upload PDF 1", type="pdf")
    file2 = st.file_uploader("Upload PDF 2", type="pdf")

    if file1 and file2:
        text1 = extract_text(file1)
        text2 = extract_text(file2)

        diff = list(difflib.ndiff(text1.splitlines(), text2.splitlines()))

        st.subheader("Differences:")
        for line in diff:
            if line.startswith("- "):
                st.markdown(f"🔴 {line}")
            elif line.startswith("+ "):
                st.markdown(f"🟢 {line}")

# ======================
# AI COMPARE (SMART)
# ======================
elif menu == "AI Compare":
    st.header("🧠 AI Compare (Smart Diff)")

    file1 = st.file_uploader("Upload Original PDF", type="pdf")
    file2 = st.file_uploader("Upload Modified PDF", type="pdf")

    if file1 and file2:
        text1 = extract_text(file1)
        text2 = extract_text(file2)

        changes = list(difflib.unified_diff(
            text1.split(),
            text2.split(),
            lineterm=""
        ))

        st.subheader("Smart Changes:")
        for line in changes:
            if line.startswith("-"):
                st.markdown(f"🔴 Removed: {line[1:]}")
            elif line.startswith("+"):
                st.markdown(f"🟢 Added: {line[1:]}")

# ======================
# CONVERT (SAFE VERSION)
# ======================
elif menu == "Convert":
    st.header("🔄 Convert to PDF")

    uploaded = st.file_uploader("Upload TXT file", type=["txt"])

    if uploaded:
        text = uploaded.read().decode("utf-8")

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        y = 750
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 15

        c.save()
        buffer.seek(0)

        st.download_button(
            "Download PDF",
            buffer,
            file_name="converted.pdf",
            mime="application/pdf"
        )

# ======================
# SIGN (BASIC STABLE)
# ======================
elif menu == "Sign":
    st.header("✍️ PDF Sign (Basic Stable Version)")

    pdf_file = st.file_uploader("Upload PDF", type="pdf")

    signature_text = st.text_input("Enter Signature (for now text-based)")

    if pdf_file and signature_text:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas

        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # Create signature overlay
        packet = BytesIO()
        can = canvas.Canvas(packet)

        can.drawString(100, 100, signature_text)
        can.save()

        packet.seek(0)
        overlay = PdfReader(packet)

        writer.pages[0].merge_page(overlay.pages[0])

        output = BytesIO()
        writer.write(output)
        output.seek(0)

        st.download_button(
            "Download Signed PDF",
            output,
            file_name="signed.pdf",
            mime="application/pdf"
        )
