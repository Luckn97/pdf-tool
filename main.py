import streamlit as st
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

st.set_page_config(layout="wide")

st.title("📄 Drag & Resize directly on PDF")

# -------------------------
# PDF UPLOAD
# -------------------------
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if pdf_file:

    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page = doc.load_page(0)

    # 🔥 Render PDF → PIL Image
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # höhere Qualität
    img_bytes = pix.tobytes("png")
    pdf_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # -------------------------
    # SIGNATURE DRAW
    # -------------------------
    st.subheader("✍️ Draw Signature")

    sig_canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="sig",
    )

    signature_img = None

    if sig_canvas.image_data is not None:
        signature_img = Image.fromarray(
            sig_canvas.image_data.astype("uint8")
        ).convert("RGBA")

    # -------------------------
    # MAIN DRAG AREA
    # -------------------------
    st.subheader("🖱️ Place Signature (Drag & Resize)")

    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=1,
        stroke_color="#000000",
        background_image=pdf_image,  # ✅ FIXED
        update_streamlit=True,
        height=600,
        width=pdf_image.width if pdf_image.width < 900 else 900,
        drawing_mode="transform",
        key="main_canvas",
    )

    # -------------------------
    # EXPORT
    # -------------------------
    if st.button("💾 Apply Signature"):

        if signature_img and canvas_result.json_data:

            objects = canvas_result.json_data["objects"]

            if len(objects) > 0:
                obj = objects[-1]

                left = obj["left"]
                top = obj["top"]
                scale_x = obj["scaleX"]
                scale_y = obj["scaleY"]

                # Resize signature
                new_w = int(signature_img.width * scale_x)
                new_h = int(signature_img.height * scale_y)
                sig_resized = signature_img.resize((new_w, new_h))

                # Overlay auf PDF
                pdf_image_rgba = pdf_image.convert("RGBA")
                pdf_image_rgba.paste(sig_resized, (int(left), int(top)), sig_resized)

                # Save to PDF
                output = io.BytesIO()
                pdf_image_rgba.convert("RGB").save(output, format="PDF")

                st.success("✅ Done!")
                st.download_button(
                    "⬇️ Download signed PDF",
                    data=output.getvalue(),
                    file_name="signed.pdf",
                    mime="application/pdf",
                )
