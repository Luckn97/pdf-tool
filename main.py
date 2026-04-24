import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz
import io

st.set_page_config(layout="wide")

st.title("📄 Sign PDF – PRO")

pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

def make_transparent(img):
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    return img

if pdf_file:
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    # PDF → Image
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    pdf_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

    # Resize
    MAX_WIDTH = 900
    scale = MAX_WIDTH / pdf_image.width
    new_w = int(pdf_image.width * scale)
    new_h = int(pdf_image.height * scale)
    pdf_image = pdf_image.resize((new_w, new_h))

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

        signature = Image.fromarray(sig_canvas.image_data.astype("uint8"))
        signature = make_transparent(signature)

        st.subheader("🎯 Position Signature")

        col1, col2 = st.columns(2)

        with col1:
            x = st.slider("X", 0, new_w, 200)
            y = st.slider("Y", 0, new_h, 200)

        with col2:
            scale_sig = st.slider("Size", 0.1, 1.5, 0.5)

        # Resize signature
        w = int(signature.width * scale_sig)
        h = int(signature.height * scale_sig)
        sig_resized = signature.resize((w, h))

        # Overlay
        preview = pdf_image.copy()
        preview.paste(sig_resized, (x, y), sig_resized)

        st.subheader("👀 Live Preview")
        st.image(preview, use_column_width=True)
