import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image
import io
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(layout="wide")

st.title("✍️ Sign PRO – Click Placement (Stable)")

# Upload
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    pdf_bytes = uploaded_file.read()
    images = convert_from_bytes(pdf_bytes)

    total_pages = len(images)

    page_num = st.number_input(
        "Select Page",
        min_value=1,
        max_value=total_pages,
        value=1
    )

    img = images[page_num - 1]

    st.subheader("📄 Click on PDF to place signature")

    # 👉 WICHTIG: Bild NORMAL anzeigen (kein canvas background!)
    st.image(img, use_container_width=True)

    # Klick Koordinaten simulieren (Workaround statt st_canvas)
    x = st.slider("X Position", 0, img.width, img.width // 2)
    y = st.slider("Y Position", 0, img.height, img.height // 2)

    # Signature Upload (besser als zeichnen für Stabilität)
    sig_file = st.file_uploader("Upload Signature (PNG empfohlen)", type=["png"])

    if sig_file:
        sig = Image.open(sig_file).convert("RGBA")

        st.subheader("🔍 Preview")

        preview = img.copy()
        preview.paste(sig, (x, y), sig)

        st.image(preview, use_container_width=True)

        if st.button("💾 Sign PDF"):

            packet = io.BytesIO()
            can = canvas.Canvas(packet)

            # Y invertieren (PDF Koordinaten!)
            pdf_y = img.height - y - 50

            can.drawImage(
                sig_file,
                x,
                pdf_y,
                width=150,
                height=50,
                mask='auto'
            )

            can.save()

            packet.seek(0)

            new_pdf = PdfReader(packet)
            existing_pdf = PdfReader(io.BytesIO(pdf_bytes))
            output = PdfWriter()

            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]

                if i == page_num - 1:
                    page.merge_page(new_pdf.pages[0])

                output.add_page(page)

            out_stream = io.BytesIO()
            output.write(out_stream)

            st.success("✅ Signed successfully!")

            st.download_button(
                "Download Signed PDF",
                data=out_stream.getvalue(),
                file_name="signed.pdf"
            )
