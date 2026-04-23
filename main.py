import streamlit as st
import fitz
import base64
import io
from PIL import Image

st.set_page_config(layout="wide")

st.title("🚀 Sign PRO – Full Version")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    total_pages = len(doc)

    page_num = st.number_input("Page", 1, total_pages, 1)
    page = doc[page_num - 1]

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_bytes = pix.tobytes("png")
    img_base64 = base64.b64encode(img_bytes).decode()

    st.subheader("📄 Drag Signature on PDF")

    sig_file = st.file_uploader("Upload Signature", type=["png"])

    if sig_file:

        sig_bytes = sig_file.read()
        sig_base64 = base64.b64encode(sig_bytes).decode()

        # Hidden input to send coords back
        coord = st.text_input("coords", "", key="coords")

        html = f"""
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
            resize: both;
            overflow: auto;
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

            // Save position
            const rect = sig.getBoundingClientRect();

            const data = {{
                x: rect.left,
                y: rect.top,
                w: rect.width,
                h: rect.height
            }}

            window.parent.postMessage({{type: "streamlit:setComponentValue", value: JSON.stringify(data)}}, "*");
        }});

        document.addEventListener("mousemove", (e) => {{
            if (!isDown) return;

            sig.style.left = (e.pageX - offsetX) + "px";
            sig.style.top = (e.pageY - offsetY) + "px";
        }});
        </script>
        """

        st.components.v1.html(html, height=800)

        # 👉 Position verarbeiten
        if coord:

            import json
            pos = json.loads(coord)

            st.write("📍 Position:", pos)

            if st.button("💾 Apply Signature to PDF"):

                page_height = page.rect.height

                x = pos["x"]
                y = pos["y"]
                w = pos["w"]
                h = pos["h"]

                # Korrektur für PDF Koordinaten
                rect = fitz.Rect(
                    x,
                    page_height - y - h,
                    x + w,
                    page_height - y
                )

                page.insert_image(rect, stream=sig_bytes)

                output = io.BytesIO()
                doc.save(output)

                st.success("✅ Signed!")

                st.download_button(
                    "Download PDF",
                    data=output.getvalue(),
                    file_name="signed.pdf"
                )
