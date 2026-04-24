import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
import io

st.set_page_config(layout="wide")

st.title("📄 Place Signature (Drag & Resize)")

# Upload PDF
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if pdf_file:
    # PDF öffnen
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_num = st.number_input("Page", min_value=1, max_value=len(doc), value=1)
    page = doc[page_num - 1]

    # PDF → Image (sauber & stabil)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # höhere Qualität
    img_bytes = pix.tobytes("png")

    pdf_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # FIX: sichere Skalierung
    MAX_WIDTH = 900
    scale = MAX_WIDTH / pdf_image.width
    new_width = int(pdf_image.width * scale)
    new_height = int(pdf_image.height * scale)

    pdf_image = pdf_image.resize((new_width, new_height))

    st.write("👉 Drag & resize your signature directly on the PDF")

    # Signatur zeichnen
    st.subheader("✍️ Draw Signature")

    signature_canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=3,
        stroke_color="black",
        background_color="white",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="signature",
    )

    signature_image = None

    if signature_canvas.image_data is not None:
        signature_image = Image.fromarray(
            signature_canvas.image_data.astype("uint8")
        ).convert("RGBA")

    # 🔥 WICHTIGER FIX:
    # Canvas darf NIE None als background_image bekommen
    if pdf_image is not None and signature_image is not None:

        # Haupt-Canvas (PDF + Drag & Resize)
        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=1,
            stroke_color="blue",
            background_image=pdf_image,  # ← jetzt garantiert gültig
            update_streamlit=True,
            height=new_height,
            width=new_width,
            drawing_mode="transform",  # 🔥 Drag + Resize Mode
            initial_drawing={
                "version": "4.4.0",
                "objects": [
                    {
                        "type": "image",
                        "left": 50,
                        "top": 50,
                        "scaleX": 0.5,
                        "scaleY": 0.5,
                        "angle": 0,
                        "src": signature_canvas.image_data.tolist(),
                    }
                ],
            },
            key="main_canvas",
        )

        st.success("👉 Position & Größe direkt auf dem PDF anpassen")
