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
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_num = st.number_input("Page", min_value=1, max_value=len(doc), value=1)
    page = doc[page_num - 1]

    # 🔥 PDF → Pixmap → PNG Bytes → PIL (SAFE WAY)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    png_bytes = pix.tobytes("png")

    # 🔥 EXTREM WICHTIG: Neu laden → verhindert Streamlit Fehler
    pdf_image = Image.open(io.BytesIO(png_bytes)).convert("RGB")

    # Skalierung (verhindert oversized canvas)
    MAX_WIDTH = 900
    scale = MAX_WIDTH / pdf_image.width
    new_size = (int(pdf_image.width * scale), int(pdf_image.height * scale))
    pdf_image = pdf_image.resize(new_size)

    st.write("👉 Drag & resize your signature directly on the PDF")

    # Signatur zeichnen
    st.subheader("✍️ Draw Signature")

    sig_canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=3,
        stroke_color="black",
        background_color="white",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="sig",
    )

    if sig_canvas.image_data is not None:

        signature = Image.fromarray(sig_canvas.image_data.astype("uint8")).convert("RGBA")

        # 🔥 DOUBLE SAFE: nochmals neu encoden
        buffer = io.BytesIO()
        pdf_image.save(buffer, format="PNG")
        buffer.seek(0)
        safe_bg = Image.open(buffer)

        # MAIN CANVAS
        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=1,
            stroke_color="blue",
            background_image=safe_bg,  # ← jetzt 100% safe
            update_streamlit=True,
            height=new_size[1],
            width=new_size[0],
            drawing_mode="transform",
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
                        "src": sig_canvas.image_data.tolist(),
                    }
                ],
            },
            key="main_canvas",
        )

        st.success("👉 Drag & resize directly on the PDF")
