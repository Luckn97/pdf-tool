import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np

from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")

# =========================
# 🚀 HEADER
# =========================
st.markdown("""
# 🚀 PDF Toolkit PRO
### Compare • AI Compare • Convert • Sign
---
""")

mode = st.radio(
    "Select Feature",
    ["Sign PRO", "Compare", "AI Compare", "Convert"],
    horizontal=True
)

# =========================
# ✍️ SIGN PRO
# =========================
if mode == "Sign PRO":

    st.markdown("## ✍️ Sign PRO (Stable Version)")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf is not None:

        try:
            pdf_bytes = uploaded_pdf.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        except Exception as e:
            st.error("❌ PDF konnte nicht geladen werden")
            st.stop()

        # 🛑 HARDCHECK → verhindert Slider Crash
        if doc is None or len(doc) == 0:
            st.error("❌ PDF hat keine Seiten oder ist beschädigt")
            st.stop()

        total_pages = len(doc)

        # ✅ SAFE SLIDER (CRASH FIX)
        page_num = st.number_input(
            "Select Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1
        )

        page = doc[page_num - 1]

        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        st.image(img, caption=f"Page {page_num}", use_container_width=True)

        # =========================
        # ✍️ SIGNATURE DRAW
        # =========================
        st.markdown("### ✍️ Draw Signature")

        sig = st_canvas(
            stroke_width=3,
            stroke_color="#FFFFFF",
            background_color="#000000",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="sig"
        )

        # =========================
        # 📄 SIGN EXPORT
        # =========================
        if st.button("📄 Generate Signed PDF"):

            if sig.image_data is None:
                st.warning("Bitte unterschreiben")
                st.stop()

            # Convert signature
            sig_img = Image.fromarray(
                (sig.image_data[:, :, :3]).astype(np.uint8)
            ).convert("RGBA")

            datas = sig_img.getdata()
            new_data = []

            for item in datas:
                if item[0] < 50 and item[1] < 50 and item[2] < 50:
                    new_data.append((0, 0, 0, 0))
                else:
                    new_data.append((0, 0, 0, 255))

            sig_img.putdata(new_data)

            buffer = io.BytesIO()
            sig_img.save(buffer, format="PNG")

            # 👉 FIXED POSITION (center)
            rect = fitz.Rect(100, 100, 300, 180)

            page.insert_image(rect, stream=buffer.getvalue())

            output = io.BytesIO()
            doc.save(output)
            output.seek(0)

            st.success("✅ PDF erstellt!")

            st.download_button(
                "⬇️ Download Signed PDF",
                data=output,
                file_name="signed.pdf",
                mime="application/pdf"
            )

# =========================
# 📊 COMPARE
# =========================
elif mode == "Compare":
    st.markdown("## 📊 Compare")
    st.info("Coming soon")

# =========================
# 🤖 AI COMPARE
# =========================
elif mode == "AI Compare":
    st.markdown("## 🤖 AI Compare")
    st.info("Next step")

# =========================
# 🔄 CONVERT
# =========================
elif mode == "Convert":
    st.markdown("## 🔄 Convert")
    st.info("Coming soon")
