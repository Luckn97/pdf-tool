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

        signature = Image.fromarray(sig_canvas.image_data.astype("uint8")).convert("RGBA")

        st.subheader("👉 Drag & Resize")

        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=1,
            stroke_color="blue",
            background_color="white",
            height=new_h,
            width=new_w,
            drawing_mode="transform",
            initial_drawing={
                "version": "4.4.0",
                "objects": [
                    {
                        "type": "rect",
                        "left": 100,
                        "top": 100,
                        "width": 200,
                        "height": 100,
                        "fill": "rgba(0,0,0,0)",
                        "stroke": "blue",
                    }
                ],
            },
            key="main_canvas",
        )

        # 🔥 LIVE PREVIEW (hier passiert die Magie)
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]

            preview = pdf_image.copy()

            for obj in objects:
                if obj["type"] == "rect":
                    x = int(obj["left"])
                    y = int(obj["top"])
                    w = int(obj["width"] * obj["scaleX"])
                    h = int(obj["height"] * obj["scaleY"])

                    sig_resized = signature.resize((w, h))
                    preview.paste(sig_resized, (x, y), sig_resized)

            st.subheader("👀 Live Preview")
            st.image(preview, use_column_width=True)

        st.success("✅ Stabil + kein Canvas Bug mehr")
