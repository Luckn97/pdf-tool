import streamlit as st
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

st.set_page_config(layout="wide")

st.title("🚀 Sign PRO – Stable Version (No pdf2image)")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")

if uploaded_pdf:
    pdf_bytes = uploaded_pdf.read()

    # 📄 Load PDF with PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)

    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # 🔥 SCALE FIX
    display_width = 700
    ratio = display_width / img.width
    new_height = int(img.height * ratio)
    img_resized = img.resize((display_width, new_height))

    st.subheader("✍️ Draw Signature")

    sig_canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=3,
        stroke_color="black",
        background_color="#fff",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="sig",
    )

    st.subheader("📄 Drag signature onto PDF")

    # Position State
    if "pos" not in st.session_state:
        st.session_state.pos = {"x": 200, "y": 200}

   # 🔥 PIL → Bytes konvertieren
img_bytes = io.BytesIO()
img_resized.save(img_bytes, format="PNG")
img_bytes.seek(0)

drag = st_canvas(
    fill_color="rgba(0,0,0,0)",
    stroke_width=0,
    background_image=Image.open(img_bytes),
    height=new_height,
    width=display_width,
    drawing_mode="transform",
    key="drag"
)

    # Update position
    if drag.json_data and "objects" in drag.json_data:
        objs = drag.json_data["objects"]
        if len(objs) > 0:
            obj = objs[0]
            st.session_state.pos["x"] = obj["left"]
            st.session_state.pos["y"] = obj["top"]

    # 🔥 LIVE PREVIEW
    if sig_canvas.image_data is not None:
        sig_img = Image.fromarray(sig_canvas.image_data.astype("uint8"))

        overlay = img_resized.copy()
        overlay.paste(
            sig_img.resize((120, 40)),
            (int(st.session_state.pos["x"]), int(st.session_state.pos["y"])),
            sig_img.resize((120, 40))
        )

        st.image(overlay, caption="Live Preview")

    # 💾 EXPORT
    if st.button("✅ Apply Signature to PDF"):
        sig_img = Image.fromarray(sig_canvas.image_data.astype("uint8"))

        packet = io.BytesIO()
        can = canvas.Canvas(packet)

        # 🔥 Skalierung zurück ins echte PDF
        scale_back = img.width / display_width

        x_pdf = st.session_state.pos["x"] * scale_back
        y_pdf = img.height - (st.session_state.pos["y"] * scale_back)

        sig_buffer = io.BytesIO()
        sig_img.save(sig_buffer, format="PNG")
        sig_buffer.seek(0)

        can.drawImage(
            Image.open(sig_buffer),
            x_pdf,
            y_pdf,
            width=150,
            height=50,
            mask='auto'
        )

        can.save()
        packet.seek(0)

        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        overlay_pdf = PdfReader(packet)

        page = reader.pages[0]
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)

        st.download_button(
            "⬇️ Download Signed PDF",
            out,
            file_name="signed.pdf"
        )
