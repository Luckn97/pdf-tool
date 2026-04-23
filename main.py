import streamlit as st
import fitz
import base64
from PIL import Image
import io

st.set_page_config(layout="wide")

st.title("🚀 Sign PRO – Drag & Drop")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page = doc[0]

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_bytes = pix.tobytes("png")

    img_base64 = base64.b64encode(img_bytes).decode()

    st.subheader("📄 Drag your signature onto the PDF")

    sig_file = st.file_uploader("Upload Signature (PNG)", type=["png"])

    if sig_file:

        sig_bytes = sig_file.read()
        sig_base64 = base64.b64encode(sig_bytes).decode()

        # HTML DRAG UI
        html_code = f"""
        <style>
        .container {{
            position: relative;
            width: 100%;
        }}
        .pdf {{
            width: 100%;
        }}
        .sig {{
            position: absolute;
            top: 50px;
            left: 50px;
            width: 150px;
            cursor: move;
        }}
        </style>

        <div class="container">
            <img src="data:image/png;base64,{img_base64}" class="pdf"/>

            <img id="sig" src="data:image/png;base64,{sig_base64}" class="sig"/>
        </div>

        <script>
        const sig = document.getElementById("sig");

        let offsetX, offsetY, isDown = false;

        sig.addEventListener("mousedown", (e) => {{
            isDown = true;
            offsetX = e.offsetX;
            offsetY = e.offsetY;
        }});

        document.addEventListener("mouseup", () => {{
            isDown = false;
        }});

        document.addEventListener("mousemove", (e) => {{
            if (!isDown) return;

            sig.style.left = (e.pageX - offsetX) + "px";
            sig.style.top = (e.pageY - offsetY) + "px";
        }});
        </script>
        """

        st.components.v1.html(html_code, height=800)

        st.info("👉 Drag the signature visually (backend save comes next step)")
