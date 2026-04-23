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
st.caption("Compare & sign PDFs — visual + text intelligence")

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
    texts = []
    for page in doc:
        texts.append(page.get_text())
    return texts

# -----------------------------
# TEXT DIFF
# -----------------------------
def compare_texts(text1, text2):
    diff = list(difflib.ndiff(text1.split(), text2.split()))
    added = [w[2:] for w in diff if w.startswith("+ ")]
    removed = [w[2:] for w in diff if w.startswith("- ")]
    return added, removed

def highlight_diff(text1, text2):
    return difflib.HtmlDiff().make_file(
        text1.splitlines(),
        text2.splitlines()
    )

# -----------------------------
# IMAGE DIFF
# -----------------------------
def detect_diff(img1, img2, sensitivity=50):
    img1 = img1.resize(img2.size)

    gray1 = np.array(img1.convert("L"))
    gray2 = np.array(img2.convert("L"))

    score, diff = ssim(gray1, gray2, full=True)

    diff = (1 - diff) * 255
    diff = diff.astype("uint8")

    heatmap = Image.fromarray(diff)

    threshold = diff > sensitivity
    coords = np.column_stack(np.where(threshold))

    output = img2.copy()
    draw = ImageDraw.Draw(output)

    boxes = []
    for y, x in coords[::300]:
        box = (x, y, x+20, y+20)
        boxes.append(box)
        draw.rectangle(box, outline="red", width=1)

    return output, heatmap, score, boxes

# -----------------------------
# SLIDER VIEW
# -----------------------------
def compare_slider(img1, img2):
    slider = st.slider("Compare Slider", 0, 100, 50)
    width = img1.width
    split = int(width * slider / 100)

    combined = Image.new("RGB", img1.size)
    combined.paste(img1.crop((0, 0, split, img1.height)), (0, 0))
    combined.paste(img2.crop((split, 0, width, img2.height)), (split, 0))

    return combined

# -----------------------------
# MARKED PDF EXPORT
# -----------------------------
def create_marked_pdf(pdf_path, imgs1, imgs2, sensitivity):
    doc = fitz.open(pdf_path)

    for i, page in enumerate(doc):
        if i >= len(imgs1) or i >= len(imgs2):
            continue

        _, _, _, boxes = detect_diff(imgs1[i], imgs2[i], sensitivity)

        for (x0, y0, x1, y1) in boxes:
            rect = fitz.Rect(x0, y0, x1, y1)
            page.draw_rect(rect, color=(1, 0, 0), width=1)

    out_path = os.path.join(OUTPUT_DIR, "marked.pdf")
    doc.save(out_path)

    return out_path

# -----------------------------
# COMPARE TAB
# -----------------------------
with menu[0]:
    st.subheader("📊 Visual + Text PDF Comparison")

    col1, col2 = st.columns(2)

    with col1:
        file1 = st.file_uploader("Upload PDF A", type=["pdf"])
    with col2:
        file2 = st.file_uploader("Upload PDF B", type=["pdf"])

    sensitivity = st.slider("Sensitivity", 10, 100, 50)

    if file1 and file2:
        path1 = os.path.join(UPLOAD_DIR, file1.name)
        path2 = os.path.join(UPLOAD_DIR, file2.name)

        with open(path1, "wb") as f:
            f.write(file1.read())
        with open(path2, "wb") as f:
            f.write(file2.read())

        if st.button("🚀 Run Comparison"):
            imgs1 = pdf_to_images(path1)
            imgs2 = pdf_to_images(path2)

            texts1 = extract_text_per_page(path1)
            texts2 = extract_text_per_page(path2)

            for i in range(min(len(imgs1), len(imgs2))):
                st.markdown(f"## Page {i+1}")

                res, heat, score, _ = detect_diff(
                    imgs1[i], imgs2[i], sensitivity
                )

                st.metric("Similarity", f"{score:.3f}")

                view = st.radio(
                    "View Mode",
                    ["Before/After", "Differences", "Heatmap"],
                    horizontal=True,
                    key=f"view_{i}"
                )

                if view == "Before/After":
                    st.image(compare_slider(imgs1[i], res))
                elif view == "Differences":
                    st.image(res)
                else:
                    st.image(heat)

                # -----------------------------
                # TEXT DIFF
                # -----------------------------
                st.markdown("### 🧠 Text Differences")

                added, removed = compare_texts(texts1[i], texts2[i])

                colA, colB = st.columns(2)
                with colA:
                    st.markdown("#### ➕ Added")
                    st.write(added[:50])
                with colB:
                    st.markdown("#### ➖ Removed")
                    st.write(removed[:50])

                # HTML Diff
                with st.expander("🔍 Full Text Diff"):
                    html = highlight_diff(texts1[i], texts2[i])
                    st.components.v1.html(html, height=400)

                # -----------------------------
                # DOWNLOAD IMAGE
                # -----------------------------
                img_path = os.path.join(OUTPUT_DIR, f"result_{i}.png")
                res.save(img_path)

                with open(img_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download Image",
                        f,
                        file_name=f"comparison_{i+1}.png"
                    )

        # -----------------------------
        # DOWNLOAD MARKED PDF
        # -----------------------------
        if st.button("📄 Export Marked PDF"):
            with st.spinner("Generating PDF..."):
                imgs1 = pdf_to_images(path1)
                imgs2 = pdf_to_images(path2)

                pdf_out = create_marked_pdf(path2, imgs1, imgs2, sensitivity)

                with open(pdf_out, "rb") as f:
                    st.download_button(
                        "⬇️ Download Marked PDF",
                        f
                    )

# -----------------------------
# SIGN TAB
# -----------------------------
with menu[1]:
    st.subheader("✍️ Sign PDF")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    canvas = st_canvas(height=200, width=400, drawing_mode="freedraw")

    if pdf_file and canvas.image_data is not None:
        sig_path = os.path.join(OUTPUT_DIR, "sig.png")
        Image.fromarray(canvas.image_data.astype("uint8")).save(sig_path)

        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        if st.button("✍️ Apply Signature"):
            doc = fitz.open(pdf_path)
            sig = fitz.Pixmap(sig_path)

            for page in doc:
                rect = fitz.Rect(50, page.rect.height - 150, 250, page.rect.height - 50)
                page.insert_image(rect, pixmap=sig)

            out_path = os.path.join(OUTPUT_DIR, "signed.pdf")
            doc.save(out_path)

            with open(out_path, "rb") as f:
                st.download_button("⬇️ Download Signed PDF", f)
