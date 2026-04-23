import streamlit as st
import os
import fitz
import numpy as np
from PIL import Image, ImageDraw
from skimage.metrics import structural_similarity as ssim
from streamlit_drawable_canvas import st_canvas
import difflib

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")

st.title("🚀 PDF Toolkit PRO")
st.caption("Compare, analyze & sign PDFs like a pro")

menu = st.tabs(["📊 Compare", "✍️ Sign"])

# -----------------------------
# PDF → Images
# -----------------------------
def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

# -----------------------------
# SIGN TAB (MULTI PAGE PRO)
# -----------------------------
with menu[1]:
    st.subheader("✍️ Sign PDF (Multi Page Pro)")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file:

        if pdf_file.size == 0:
            st.error("❌ Empty file")
            st.stop()

        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
        except:
            st.error("❌ Cannot read PDF")
            st.stop()

        if total_pages == 0:
            st.error("❌ No pages found")
            st.stop()

        st.success(f"📄 {total_pages} pages detected")

        # 👉 Seiten auswählen
        pages_to_sign = st.multiselect(
            "Select pages to sign",
            list(range(1, total_pages + 1)),
            default=[1]
        )

        # 👉 Preview
        st.markdown("### 📄 PDF Preview")

        preview_images = pdf_to_images(pdf_path)

        for i, img in enumerate(preview_images):
            st.markdown(f"Page {i+1}")
            st.image(img, use_column_width=True)

        st.markdown("---")

        # 👉 Signature zeichnen
        st.markdown("### ✍️ Draw Signature")

        canvas_sig = st_canvas(
            height=200,
            width=400,
            drawing_mode="freedraw",
            stroke_color="white",
            background_color="#0e1117",
            stroke_width=4,
            key="sig"
        )

        if canvas_sig.image_data is not None:

            sig_img = Image.fromarray(canvas_sig.image_data.astype("uint8"))
            sig_img = sig_img.convert("RGBA")

            # 👉 Clean Signature
            new_data = []
            for r, g, b, a in sig_img.getdata():
                if r < 60 and g < 60 and b < 60:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((0, 0, 0, 255))
            sig_img.putdata(new_data)

            st.markdown("### 🎯 Position Signature (Page 1 Reference)")

            # 👉 Referenzseite
            page = doc[0]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            MAX_WIDTH = 800
            scale = 1
            if img.width > MAX_WIDTH:
                scale = MAX_WIDTH / img.width
                img = img.resize((int(img.width * scale), int(img.height * scale)))

            st.image(img, use_column_width=True)

            canvas = st_canvas(
                height=img.height,
                width=img.width,
                drawing_mode="transform",
                background_color="rgba(0,0,0,0)",
                key="pdf"
            )

            st.info("👉 Drag & resize signature → applies to all selected pages")

            if st.button("🚀 Apply Signature to Pages"):

                if canvas.json_data is not None:
                    objects = canvas.json_data.get("objects", [])

                    if len(objects) > 0:
                        obj = objects[0]

                        x = obj["left"] / scale
                        y = obj["top"] / scale
                        w = obj["scaleX"] * sig_img.width / scale
                        h = obj["scaleY"] * sig_img.height / scale

                        sig_path = os.path.join(OUTPUT_DIR, "sig.png")
                        sig_img.save(sig_path)

                        doc = fitz.open(pdf_path)

                        for page_index in pages_to_sign:
                            page = doc[page_index - 1]
                            rect = fitz.Rect(x, y, x + w, y + h)
                            page.insert_image(rect, filename=sig_path)

                        out = os.path.join(OUTPUT_DIR, "signed_multi.pdf")
                        doc.save(out)

                        with open(out, "rb") as f:
                            st.download_button("⬇️ Download Signed PDF", f)

                        st.success("✅ Signature applied to selected pages")
