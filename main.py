import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image

st.set_page_config(layout="wide")

st.title("🚀 Sign PRO – Clean UI")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")

if uploaded_pdf:

    # Read PDF
    pdf_reader = PdfReader(uploaded_pdf)
    total_pages = len(pdf_reader.pages)

    page_num = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1
    )

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

        # 👉 EINZIGE PDF VIEW + DRAG + RESIZE + PREVIEW
        st.markdown("### 📄 Place Signature (Drag & Resize directly on PDF)")

        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=0,
            background_color="#ffffff",
            height=800,
            width=600,
            drawing_mode="transform",  # 🔥 enables drag + resize
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
                        "src": signature_image
                    }
                ]
            },
            key="main_canvas"
        )

        if st.button("💾 Apply Signature"):

            if canvas_result.json_data:

                obj = canvas_result.json_data["objects"][0]

                x = obj["left"]
                y = obj["top"]
                scale_x = obj["scaleX"]
                scale_y = obj["scaleY"]

                # Convert signature to bytes
                sig_buffer = BytesIO()
                signature_image.save(sig_buffer, format="PNG")
                sig_buffer.seek(0)

                packet = BytesIO()
                can = pdf_canvas(packet)

                # Scale applied
                width = 200 * scale_x
                height = 100 * scale_y

                can.drawImage(
                    ImageReader(sig_buffer),
                    x,
                    800 - y,
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
