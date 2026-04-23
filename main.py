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
# TEXT EXTRACTION
# -----------------------------
def extract_text_per_page(pdf_path):
    doc = fitz.open(pdf_path)
    return [page.get_text() for page in doc]

# -----------------------------
# TEXT DIFF
# -----------------------------
def compare_texts(t1, t2):
    diff = list(difflib.ndiff(t1.split(), t2.split()))
    added = [w[2:] for w in diff if w.startswith("+ ")]
    removed = [w[2:] for w in diff if w.startswith("- ")]
    return added, removed

def highlight_diff(t1, t2):
    return difflib.HtmlDiff().make_file(
        t1.splitlines(),
        t2.splitlines()
    )

# -----------------------------
# IMAGE DIFF
# -----------------------------
def detect_diff(img1, img2, sensitivity):
    img1 = img1.resize(img2.size)

    g1 = np.array(img1.convert("L"))
    g2 = np.array(img2.convert("L"))

    score, diff = ssim(g1, g2, full=True)

    diff = (1 - diff) * 255
    diff = diff.astype("uint8")

    heatmap = Image.fromarray(diff)

    threshold = diff > sensitivity
    coords = np.column_stack(np.where(threshold))

    output = img2.copy()
    draw = ImageDraw.Draw(output)

    for y, x in coords[::300]:
        draw.rectangle((x, y, x + 20, y + 20), outline="red", width=1)

    return output, heatmap, score

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

            texts1 = extract_text_per_page(path1)
            texts2 = extract_text_per_page(path2)

            for i in range(min(len(imgs1), len(imgs2))):
                st.markdown(f"### Page {i+1}")

                res, heat, score = detect_diff(imgs1[i], imgs2[i], 50)

                st.metric("Similarity", f"{score:.3f}")
                st.image(res)

                added, removed = compare_texts(texts1[i], texts2[i])
                st.write("Added:", added[:20])
                st.write("Removed:", removed[:20])

# -----------------------------
# SIGN TAB (PRO VERSION)
# -----------------------------
with menu[1]:
    st.subheader("✍️ Sign PDF (Pro Mode)")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file:
        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        # 👉 Page selection
        page_num = st.slider("Select Page", 1, total_pages, 1)

        page = doc[page_num - 1]
        pix = page.get_pixmap()

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Resize for UI
        MAX_WIDTH = 800
        scale = 1
        if img.width > MAX_WIDTH:
            scale = MAX_WIDTH / img.width
            img = img.resize((int(img.width * scale), int(img.height * scale)))

        st.markdown("### 1. Draw Signature")

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

            # 👉 CLEAN SIGNATURE (transparent + black)
            new_data = []
            for r, g, b, a in sig_img.getdata():
                if r < 60 and g < 60 and b < 60:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((0, 0, 0, 255))
            sig_img.putdata(new_data)

            st.markdown("### 2. Drag & Resize Signature")

            st.image(img, use_column_width=True)

            canvas = st_canvas(
                height=img.height,
                width=img.width,
                drawing_mode="transform",
                background_color="rgba(0,0,0,0)",
                key="pdf"
            )

            st.info("👉 Drag & resize the signature box")

            if st.button("Apply Signature"):

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

                        page = doc[page_num - 1]
                        rect = fitz.Rect(x, y, x + w, y + h)
                        page.insert_image(rect, filename=sig_path)

                        out = os.path.join(OUTPUT_DIR, "signed.pdf")
                        doc.save(out)

                        with open(out, "rb") as f:
                            st.download_button("Download Signed PDF", f)
