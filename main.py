import streamlit as st
import streamlit.components.v1 as components
import fitz
from PIL import Image
import io
import base64

st.set_page_config(layout="wide")

st.title("🚀 Sign PDF – REAL PRO")

pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

def make_transparent(img):
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    return img

if pdf_file:
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    pdf_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

    # Resize
    MAX_WIDTH = 900
    scale = MAX_WIDTH / pdf_image.width
    new_w = int(pdf_image.width * scale)
    new_h = int(pdf_image.height * scale)
    pdf_image = pdf_image.resize((new_w, new_h))

    # Convert PDF image to base64
    buffered = io.BytesIO()
    pdf_image.save(buffered, format="PNG")
    pdf_base64 = base64.b64encode(buffered.getvalue()).decode()

    st.subheader("✍️ Draw Signature")

    sig_canvas = st.canvas(
        stroke_width=3,
        stroke_color="black",
        background_color="white",
        height=150,
        width=400,
    )

    if sig_canvas.image_data is not None:
        signature = Image.fromarray(sig_canvas.image_data.astype("uint8"))
        signature = make_transparent(signature)

        buffered = io.BytesIO()
        signature.save(buffered, format="PNG")
        sig_base64 = base64.b64encode(buffered.getvalue()).decode()

        st.subheader("👉 Drag & Resize direkt auf PDF")

        components.html(f"""
        <html>
        <head>
        <style>
        body {{
            margin:0;
            overflow:hidden;
        }}
        #container {{
            position: relative;
            width: {new_w}px;
            height: {new_h}px;
        }}
        #pdf {{
            position:absolute;
            top:0;
            left:0;
            width:100%;
        }}
        #sig {{
            position:absolute;
            top:100px;
            left:100px;
            width:150px;
            cursor:move;
        }}
        </style>
        </head>

        <body>
        <div id="container">
            <img id="pdf" src="data:image/png;base64,{pdf_base64}" />
            <img id="sig" src="data:image/png;base64,{sig_base64}" />
        </div>

        <script>
        let sig = document.getElementById("sig");

        let offsetX = 0;
        let offsetY = 0;
        let isDragging = false;

        sig.onmousedown = function(e) {{
            isDragging = true;
            offsetX = e.clientX - sig.offsetLeft;
            offsetY = e.clientY - sig.offsetTop;
        }}

        document.onmouseup = function() {{
            isDragging = false;
        }}

        document.onmousemove = function(e) {{
            if (isDragging) {{
                sig.style.left = (e.clientX - offsetX) + "px";
                sig.style.top = (e.clientY - offsetY) + "px";
            }}
        }}

        // Resize via scroll
        sig.onwheel = function(e) {{
            e.preventDefault();
            let scale = e.deltaY < 0 ? 1.05 : 0.95;
            sig.style.width = sig.offsetWidth * scale + "px";
        }}
        </script>
        </body>
        </html>
        """, height=new_h+50)
