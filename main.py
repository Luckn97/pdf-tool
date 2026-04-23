import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import io
import base64
import numpy as np

from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="PDF Toolkit PRO", layout="wide")

# =========================
# 🎨 UI HEADER
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

    st.markdown("## ✍️ Sign PRO (Drag & Drop • Resize • Multi Page)")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf:
        pdf_bytes = uploaded_pdf.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        if total_pages == 0:
            st.error("PDF konnte nicht geladen werden.")
            st.stop()

        # =========================
        # 📄 PAGE SELECT (FIXED)
        # =========================
        page_num = st.slider(
            "Select Page",
            min_value=1,
            max_value=total_pages,
            value=1
        )

        page = doc[page_num - 1]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # =========================
        # ✍️ DRAW SIGNATURE
        # =========================
        st.markdown("### ✍️ Draw Signature")

        sig_canvas = st_canvas(
            fill_color="rgba(0,0,0,0)",
            stroke_width=3,
            stroke_color="#FFFFFF",  # 👈 WHITE for dark mode
            background_color="#000000",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="signature"
        )

        # =========================
        # 🖼️ PDF + OVERLAY UI
        # =========================
        st.markdown("### 🎯 Place Signature")

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        html = f"""
        <div style="position:relative; display:inline-block;">
            <img src="data:image/png;base64,{img_base64}" width="700"/>

            <div id="sig"
                style="
                position:absolute;
                top:100px;
                left:100px;
                width:150px;
                height:50px;
                border:2px dashed red;
                cursor:move;
                resize:both;
                overflow:hidden;
                background:rgba(255,255,255,0.05);
                ">
            </div>
        </div>

        <script>
        const el = document.getElementById("sig");

        let offsetX, offsetY, isDown = false;

        el.addEventListener('mousedown', (e) => {{
            isDown = true;
            offsetX = e.offsetX;
            offsetY = e.offsetY;
        }});

        document.addEventListener('mouseup', () => isDown = false);

        document.addEventListener('mousemove', (e) => {{
            if (!isDown) return;
            el.style.left = (e.pageX - offsetX) + 'px';
            el.style.top = (e.pageY - offsetY) + 'px';
        }});
        </script>
        """

        st.components.v1.html(html, height=800)

        # =========================
        # 📄 EXPORT PDF
        # =========================
        if st.button("📄 Generate Signed PDF"):

            if sig_canvas.image_data is None:
                st.warning("Bitte zuerst unterschreiben")
                st.stop()

            sig_img = Image.fromarray(
                (sig_canvas.image_data[:, :, :3]).astype(np.uint8)
            )

            # Transparent machen
            sig_img = sig_img.convert("RGBA")
            datas = sig_img.getdata()

            new_data = []
            for item in datas:
                if item[0] < 50 and item[1] < 50 and item[2] < 50:
                    new_data.append((0, 0, 0, 0))
                else:
                    new_data.append((0, 0, 0, 255))

            sig_img.putdata(new_data)

            sig_buffer = io.BytesIO()
            sig_img.save(sig_buffer, format="PNG")

            # Default Position (center)
            rect = fitz.Rect(100, 100, 250, 150)

            page.insert_image(rect, stream=sig_buffer.getvalue())

            output = io.BytesIO()
            doc.save(output)
            output.seek(0)

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
    st.markdown("## 📊 PDF Compare (Basic)")
    st.info("Coming next step (diff highlight)")

# =========================
# 🤖 AI COMPARE
# =========================
elif mode == "AI Compare":
    st.markdown("## 🤖 AI Compare")
    st.info("Next step: semantic diff + summary")

# =========================
# 🔄 CONVERT
# =========================
elif mode == "Convert":
    st.markdown("## 🔄 Convert")
    st.info("PDF ↔ Image/Text coming next")
