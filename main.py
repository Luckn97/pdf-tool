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

    st.markdown("## ✍️ Sign PRO (Click Position Version)")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf is not None:

        # =========================
        # 📄 LOAD PDF
        # =========================
        try:
            pdf_bytes = uploaded_pdf.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except:
            st.error("❌ PDF konnte nicht geladen werden")
            st.stop()

        if doc is None or len(doc) == 0:
            st.error("❌ PDF hat keine Seiten")
            st.stop()

        total_pages = len(doc)

        # =========================
        # 📄 PAGE SELECT (SAFE)
        # =========================
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
        # 📍 CLICK POSITION
        # =========================
        st.markdown("### 🎯 Click on PDF to place signature")

        click_canvas = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=1,
            stroke_color="#FF0000",
            background_image=img,
            height=img.height,
            width=img.width,
            drawing_mode="point",
            key="position"
        )

        x, y = None, None

        if click_canvas.json_data is not None:
            objects = click_canvas.json_data["objects"]
            if len(objects) > 0:
                last = objects[-1]
                x = int(last["left"])
                y = int(last["top"])

                st.success(f"📍 Position: X={x}, Y={y}")

        # =========================
        # 📄 EXPORT PDF
        # =========================
        if st.button("📄 Generate Signed PDF"):

            if sig.image_data is None:
                st.warning("Bitte unterschreiben")
                st.stop()

            if x is None or y is None:
                st.warning("Bitte Position wählen")
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

            # =========================
            # 🎯 SCALE POSITION
            # =========================
            pdf_width = page.rect.width
            pdf_height = page.rect.height

            scale_x = pdf_width / img.width
            scale_y = pdf_height / img.height

            pdf_x = x * scale_x
            pdf_y = y * scale_y

            rect = fitz.Rect(
                pdf_x,
                pdf_y,
                pdf_x + 150,
                pdf_y + 50
            )

            page.insert_image(rect, stream=buffer.getvalue())

            output = io.BytesIO()
            doc.save(output)
            output.seek(0)

            st.success("✅ Perfekt positioniert!")

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
