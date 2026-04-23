# PDF Toolkit PRO (No OpenCV Version - Cloud Ready)

import streamlit as st
import os
from docx2pdf import convert
import fitz
import numpy as np
from PIL import Image, ImageDraw
from skimage.metrics import structural_similarity as ssim
from streamlit_drawable_canvas import st_canvas

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")
st.title("🚀 PDF Toolkit PRO")
st.caption("Compare, convert & sign PDFs instantly")

menu = st.tabs(["📊 Compare", "📄 Convert", "✍️ Sign"])

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
# DIFFERENCE DETECTION (NO CV2)
# -----------------------------

def detect_diff(img1, img2):
    img1 = img1.resize(img2.size)

    gray1 = np.array(img1.convert("L"))
    gray2 = np.array(img2.convert("L"))

    score, diff = ssim(gray1, gray2, full=True)

    diff = (1 - diff) * 255
    diff = diff.astype("uint8")

    heatmap = Image.fromarray(diff)

    # Create bounding boxes manually
    threshold = diff > 50
    coords = np.column_stack(np.where(threshold))

    output = img2.copy()
    draw = ImageDraw.Draw(output)

    if len(coords) > 0:
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0)
        draw.rectangle([x0, y0, x1, y1], outline="red", width=3)

    return output, heatmap, score

# -----------------------------
# COMPARE
# -----------------------------

with menu[0]:
    file1 = st.file_uploader("Upload PDF A", type=["pdf"])
    file2 = st.file_uploader("Upload PDF B", type=["pdf"])

    if file1 and file2:
        path1 = os.path.join(UPLOAD_DIR, file1.name)
        path2 = os.path.join(UPLOAD_DIR, file2.name)

        with open(path1, "wb") as f:
            f.write(file1.read())
        with open(path2, "wb") as f:
            f.write(file2.read())

        if st.button("Run Comparison"):
            imgs1 = pdf_to_images(path1)
            imgs2 = pdf_to_images(path2)

            for i in range(min(len(imgs1), len(imgs2))):
                res, heat, score = detect_diff(imgs1[i], imgs2[i])

                st.write(f"Page {i+1} Similarity: {score:.3f}")
                c1, c2 = st.columns(2)
                c1.image(res)
                c2.image(heat)

# -----------------------------
# CONVERT
# -----------------------------

with menu[1]:
    file = st.file_uploader("Upload DOCX", type=["docx"])

    if file:
        in_path = os.path.join(UPLOAD_DIR, file.name)
        out_path = os.path.join(OUTPUT_DIR, "converted.pdf")

        with open(in_path, "wb") as f:
            f.write(file.read())

        if st.button("Convert"):
            convert(in_path, out_path)
            with open(out_path, "rb") as f:
                st.download_button("Download PDF", f)

# -----------------------------
# SIGN
# -----------------------------

with menu[2]:
    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    canvas = st_canvas(height=200, width=400, drawing_mode="freedraw")

    if pdf_file and canvas.image_data is not None:
        sig_path = os.path.join(OUTPUT_DIR, "sig.png")
        Image.fromarray(canvas.image_data.astype("uint8")).save(sig_path)

        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        if st.button("Sign PDF"):
            doc = fitz.open(pdf_path)
            sig = fitz.Pixmap(sig_path)

            for page in doc:
                rect = fitz.Rect(50, page.rect.height - 150, 250, page.rect.height - 50)
                page.insert_image(rect, pixmap=sig)

            out_path = os.path.join(OUTPUT_DIR, "signed.pdf")
            doc.save(out_path)

            with open(out_path, "rb") as f:
                st.download_button("Download Signed PDF", f)
