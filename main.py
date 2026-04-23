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
# COMPARE TAB
# -----------------------------
with menu[0]:
    st.subheader("📊 PDF Comparison")

    file1 = st.file_uploader("Upload PDF A", type=["pdf"])
    file2 = st.file_uploader("Upload PDF B", type=["pdf"])

    if file1 and file2:
        path1 = os.path.join(UPLOAD_DIR, file1.name)
        path2 = os.path.join(UPLOAD_DIR, file2.name)

        with open(path1, "wb") as f:
            f.write(file1.read())
        with open(path2, "wb") as f:
            f.write(file2.read())

        if st.button("Compare PDFs"):
            imgs1 = pdf_to_images(path1)
            imgs2 = pdf_to_images(path2)

            for i in range(min(len(imgs1), len(imgs2))):
                st.markdown(f"### Page {i+1}")

                g1 = np.array(imgs1[i].convert("L"))
                g2 = np.array(imgs2[i].convert("L"))

                score, diff = ssim(g1, g2, full=True)

                diff = (1 - diff) * 255
                diff = diff.astype("uint8")

                st.metric("Similarity", f"{score:.3f}")
                st.image(Image.fromarray(diff))

# -----------------------------
# SIGN TAB (FINAL PRO VERSION)
# -----------------------------
with menu[1]:
    st.subheader("✍️ Sign PDF (Pro Mode)")

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

        pages_to_sign = st.multiselect(
            "Select pages to sign",
            list(range(1, total_pages + 1)),
            default=[1]
        )

        # -----------------------------
        # DRAW SIGNATURE
        # -----------------------------
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

            # 👉 Clean signature (transparent + black)
            new_data = []
            for r, g, b, a in sig_img.getdata():
                if r < 60 and g < 60 and b < 60:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((0, 0, 0, 255))
            sig_img.putdata(new_data)

            # -----------------------------
            # POSITION (REFERENCE PAGE)
            # -----------------------------
            st.markdown("### 🎯 Position Signature")

            ref_page = doc[0]
            pix = ref_page.get_pixmap()
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

            # -----------------------------
            # APPLY SIGNATURE
            # -----------------------------
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

                        preview_images = []

                        for page_index in pages_to_sign:

                            page = doc[page_index - 1]

                            page_width = page.rect.width
                            page_height = page.rect.height

                            scale_x = page_width / img.width
                            scale_y = page_height / img.height

                            rect = fitz.Rect(
                                x * scale_x,
                                y * scale_y,
                                (x + w) * scale_x,
                                (y + h) * scale_y
                            )

                            page.insert_image(rect, filename=sig_path)

                            # 👉 LIVE PREVIEW
                            pix = page.get_pixmap()
                            preview_img = Image.frombytes(
                                "RGB",
                                [pix.width, pix.height],
                                pix.samples
                            )
                            preview_images.append((page_index, preview_img))

                        out = os.path.join(OUTPUT_DIR, "signed_multi.pdf")
                        doc.save(out)

                        st.success("✅ Signature applied")

                        st.markdown("## 👀 Preview with Signature")

                        for page_index, p_img in preview_images:
                            st.markdown(f"Page {page_index}")
                            st.image(p_img, use_column_width=True)

                        with open(out, "rb") as f:
                            st.download_button("⬇️ Download Signed PDF", f)
