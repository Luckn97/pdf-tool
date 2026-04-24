import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz
import io

st.set_page_config(layout="wide")

st.title("📄 Place Signature (Drag & Resize)")

pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if pdf_file:
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page_num = st.number_input("Page", min_value=1, max_value=len(doc), value=1)
    page = doc[page_num - 1]

    # PDF → Image
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_bytes = pix.tobytes("png")
    pdf_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # Resize (wichtig für UI)
    MAX_WIDTH = 900
    scale = MAX_WIDTH / pdf_image.width
    new_w = int(pdf_image.width * scale)
    new_h = int(pdf_image.height * scale)

    pdf_image = pdf_image.resize((new_w, new_h))

    st.write("👉 Draw signature")

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

        st.write("👉 Drag & resize signature on PDF")

        col1, col2 = st.columns([1, 3])

        with col2:
            # PDF anzeigen
            st.image(pdf_image, use_column_width=True)

            # Canvas drüber (OHNE background_image)
            canvas_result = st_canvas(
                fill_color="rgba(0,0,0,0)",
                stroke_width=1,
                stroke_color="blue",
                background_color="rgba(0,0,0,0)",  # transparent!
                height=new_h,
                width=new_w,
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
                key="canvas",
            )

        st.success("👉 Works stable now – drag & resize without crashes")
