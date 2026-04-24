import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import base64
import fitz  # 🔥 PyMuPDF

st.set_page_config(layout="wide")

st.title("🚀 Sign PRO – Live PDF Preview")

uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")

if uploaded_pdf:

    pdf_bytes = uploaded_pdf.read()

    pdf_reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(pdf_reader.pages)

    page_num = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1
    )

    # 🔥 PDF → IMAGE (NO pdf2image!)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_num - 1)
    pix = page.get_pixmap()

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Convert PDF image to base64
    bg_buffer = BytesIO()
    img.save(bg_buffer, format="PNG")
    bg_base64 = base64.b64encode(bg_buffer.getvalue()).decode()
    bg_url = f"data:image/png;base64,{bg_base64}"

    st.markdown("### ✍️ Draw Signature")

    sig_canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="sig"
    )

    if sig_canvas.image_data is not None:

        signature_image = Image.fromarray(
            sig_canvas.image_data.astype("uint8")
        )

        sig_buffer = BytesIO()
        signature_image.save(sig_buffer, format="PNG")
        sig_base64 = base64.b64encode(sig_buffer.getvalue()).decode()
        sig_url = f"data:image/png;base64,{sig_base64}"

        st.markdown("### 📄 Drag & Resize directly on PDF")

        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=0,
            background_image=img,  # 🔥 REAL PDF HERE
            height=800,
            width=600,
            drawing_mode="transform",
            initial_drawing={
                "version": "4.4.0",
                "objects": [
                    {
                        "type": "image",
                        "left": 200,
                        "top": 300,
                        "scaleX": 0.5,
                        "scaleY": 0.5,
                        "angle": 0,
                        "src": sig_url
                    }
                ]
            },
            key="main_canvas"
        )

        if st.button("💾 Apply Signature"):

            if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:

                obj = canvas_result.json_data["objects"][0]

                x = obj["left"]
                y = obj["top"]
                scale_x = obj["scaleX"]
                scale_y = obj["scaleY"]

                sig_buffer.seek(0)

                packet = BytesIO()
                can = pdf_canvas(packet)

                width = 200 * scale_x
                height = 100 * scale_y

                can.drawImage(
                    ImageReader(sig_buffer),
                    x,
                    img.height - y,
                    width=width,
                    height=height,
                    mask='auto'
                )

                can.save()
                packet.seek(0)

                overlay_pdf = PdfReader(packet)
                writer = PdfWriter()

                for i, page in enumerate(pdf_reader.pages):
                    if i == page_num - 1:
                        page.merge_page(overlay_pdf.pages[0])
                    writer.add_page(page)

                output = BytesIO()
                writer.write(output)
                output.seek(0)

                st.download_button(
                    "⬇️ Download Signed PDF",
                    output,
                    file_name="signed.pdf"
                )
