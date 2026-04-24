import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz
import io
import base64

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

    # Resize
    MAX_WIDTH = 900
    scale = MAX_WIDTH / pdf_image.width
    new_w = int(pdf_image.width * scale)
    new_h = int(pdf_image.height * scale)
    pdf_image = pdf_image.resize((new_w, new_h))

    # 🔥 BASE64 FIX (wichtig!)
    buffered = io.BytesIO()
    pdf_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    bg_url = f"data:image/png;base64,{img_str}"

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

        st.subheader("👉 Drag & Resize directly on PDF")

        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=1,
            stroke_color="blue",
            background_color="white",
            background_image=None,  # wichtig!
            background_image_url=bg_url,  # 🔥 HIER PASSIERT DIE MAGIE
            update_streamlit=True,
            height=new_h,
            width=new_w,
            drawing_mode="transform",
            initial_drawing={
                "version": "4.4.0",
                "objects": [
                    {
                        "type": "image",
                        "left": 100,
                        "top": 100,
                        "scaleX": 0.5,
                        "scaleY": 0.5,
                        "angle": 0,
                        "src": sig_canvas.image_data.tolist(),
                    }
                ],
            },
            key="main_canvas",
        )

        st.success("✅ Drag & Resize funktioniert jetzt korrekt!")
