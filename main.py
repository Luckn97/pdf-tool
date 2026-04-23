import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pdfplumber
from difflib import ndiff

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# MENU
# -----------------------------
menu = st.tabs(["📊 Compare", "✍️ Sign", "📄 Convert"])

# =========================================================
# 📊 COMPARE
# =========================================================
with menu[0]:
    st.header("📊 PDF Compare")

    file1 = st.file_uploader("Upload first PDF", type=["pdf"], key="c1")
    file2 = st.file_uploader("Upload second PDF", type=["pdf"], key="c2")

    if file1 and file2:

        path1 = os.path.join(UPLOAD_DIR, file1.name)
        path2 = os.path.join(UPLOAD_DIR, file2.name)

        with open(path1, "wb") as f:
            f.write(file1.read())

        with open(path2, "wb") as f:
            f.write(file2.read())

        if st.button("Compare PDFs"):

            text1 = ""
            text2 = ""

            with pdfplumber.open(path1) as pdf:
                for p in pdf.pages:
                    text1 += p.extract_text() or ""

            with pdfplumber.open(path2) as pdf:
                for p in pdf.pages:
                    text2 += p.extract_text() or ""

            diff = list(ndiff(text1.split(), text2.split()))

            added = [d[2:] for d in diff if d.startswith("+")]
            removed = [d[2:] for d in diff if d.startswith("-")]

            st.subheader("🟢 Added")
            st.write(added[:100])

            st.subheader("🔴 Removed")
            st.write(removed[:100])

# =========================================================
# ✍️ SIGN (DRAG UI)
# =========================================================
with menu[1]:
    st.header("✍️ Sign PDF (Drag & Resize)")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file:

        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        st.success(f"{total_pages} pages detected")

        # -----------------------------
        # DRAW SIGNATURE
        # -----------------------------
        st.subheader("Draw Signature")

        sig_canvas = st_canvas(
            height=200,
            width=400,
            drawing_mode="freedraw",
            stroke_color="white",
            background_color="#0e1117",
            stroke_width=4,
            key="sig"
        )

        if sig_canvas.image_data is not None:

            sig_img = Image.fromarray(sig_canvas.image_data.astype("uint8")).convert("RGBA")

            # 👉 transparent + black
            new_data = []
            for r, g, b, a in sig_img.getdata():
                if r < 50 and g < 50 and b < 50:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((0, 0, 0, 255))
            sig_img.putdata(new_data)

            # -----------------------------
            # PAGE
            # -----------------------------
            page_num = st.slider("Page", 1, total_pages, 1)
            page = doc[page_num - 1]

            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            MAX_WIDTH = 700
            scale = 1
            if img.width > MAX_WIDTH:
                scale = MAX_WIDTH / img.width
                img = img.resize((int(img.width * scale), int(img.height * scale)))

            st.subheader("Drag box on PDF")

            canvas = st_canvas(
                background_image=img,
                height=img.height,
                width=img.width,
                drawing_mode="rect",
                stroke_color="#00ff88",
                fill_color="rgba(0,255,136,0.2)",
                stroke_width=2,
                key="pdf"
            )

            if canvas.json_data and len(canvas.json_data["objects"]) > 0:

                obj = canvas.json_data["objects"][-1]

                x = obj["left"]
                y = obj["top"]
                w = obj["width"] * obj["scaleX"]
                h = obj["height"] * obj["scaleY"]

                preview = img.copy()
                sig_resized = sig_img.resize((int(w), int(h)))
                preview.paste(sig_resized, (int(x), int(y)), sig_resized)

                st.subheader("Preview")
                st.image(preview)

                if st.button("Apply Signature"):

                    sig_path = os.path.join(OUTPUT_DIR, "sig.png")
                    sig_resized.save(sig_path)

                    doc = fitz.open(pdf_path)
                    page = doc[page_num - 1]

                    rect = fitz.Rect(
                        x / scale,
                        y / scale,
                        (x + w) / scale,
                        (y + h) / scale
                    )

                    page.insert_image(rect, filename=sig_path)

                    out_path = os.path.join(OUTPUT_DIR, "signed.pdf")
                    doc.save(out_path)

                    st.success("Signed!")

                    with open(out_path, "rb") as f:
                        st.download_button("Download PDF", f)

# =========================================================
# 📄 CONVERT
# =========================================================
with menu[2]:
    st.header("📄 Convert")

    uploaded = st.file_uploader("Upload file", type=["txt"])

    if uploaded:
        text = uploaded.read().decode("utf-8")

        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), text)

        out_path = os.path.join(OUTPUT_DIR, "converted.pdf")
        pdf.save(out_path)

        with open(out_path, "rb") as f:
            st.download_button("Download PDF", f)
