import streamlit as st
import os
import fitz
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO

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
# COMPARE
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
# SIGN (FIXED VERSION)
# -----------------------------
with menu[1]:
    st.subheader("✍️ Sign PDF")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file:

        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        st.success(f"📄 {total_pages} pages detected")

        pages_to_sign = st.multiselect(
            "Select pages",
            list(range(1, total_pages + 1)),
            default=[1]
        )

        # -----------------------------
        # SIGNATURE
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

            sig_img = Image.fromarray(canvas_sig.image_data.astype("uint8")).convert("RGBA")

            # 👉 Clean signature
            new_data = []
            for r, g, b, a in sig_img.getdata():
                if r < 60 and g < 60 and b < 60:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((0, 0, 0, 255))
            sig_img.putdata(new_data)

            # -----------------------------
            # PREVIEW PAGE
            # -----------------------------
            st.markdown("### 🎯 Place Signature")

            ref_page = doc[0]
            pix = ref_page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            MAX_WIDTH = 700
            scale = 1
            if img.width > MAX_WIDTH:
                scale = MAX_WIDTH / img.width
                img = img.resize((int(img.width * scale), int(img.height * scale)))

            # 👉 Wichtig: Bild anzeigen (separat!)
            st.image(img)

            st.info("👉 Drag the box → position your signature")

            # 👉 Canvas OHNE background_image (FIX)
            canvas = st_canvas(
                height=img.height,
                width=img.width,
                drawing_mode="rect",
                fill_color="rgba(255,255,255,0.2)",
                stroke_width=2,
                stroke_color="red",
                background_color="rgba(0,0,0,0)",
                key="pdf"
            )

            # -----------------------------
            # APPLY
            # -----------------------------
            if st.button("🚀 Apply Signature"):

                if canvas.json_data and len(canvas.json_data["objects"]) > 0:

                    rect_obj = canvas.json_data["objects"][0]

                    x = rect_obj["left"] / scale
                    y = rect_obj["top"] / scale
                    w = rect_obj["width"] / scale
                    h = rect_obj["height"] / scale

                    sig_resized = sig_img.resize((int(w), int(h)))

                    sig_path = os.path.join(OUTPUT_DIR, "sig.png")
                    sig_resized.save(sig_path)

                    doc = fitz.open(pdf_path)
                    previews = []

                    for page_index in pages_to_sign:
                        page = doc[page_index - 1]

                        rect = fitz.Rect(x, y, x + w, y + h)
                        page.insert_image(rect, filename=sig_path)

                        pix = page.get_pixmap()
                        previews.append((page_index, Image.frombytes("RGB", [pix.width, pix.height], pix.samples)))

                    out_path = os.path.join(OUTPUT_DIR, "signed.pdf")
                    doc.save(out_path)

                    st.success("✅ Signature applied")

                    st.markdown("## 👀 Preview")

                    for p, im in previews:
                        st.markdown(f"Page {p}")
                        st.image(im)

                    with open(out_path, "rb") as f:
                        st.download_button("⬇️ Download PDF", f)
