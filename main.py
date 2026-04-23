# -----------------------------
# SIGN (DRAG & RESIZE PRO UI)
# -----------------------------
with menu[1]:
    st.subheader("✍️ Sign PDF (Pro UI)")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf_file:

        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        st.success(f"📄 {total_pages} pages detected")

        # -----------------------------
        # SIGNATURE DRAW
        # -----------------------------
        st.markdown("### ✍️ Draw Signature")

        sig_canvas = st_canvas(
            height=200,
            width=400,
            drawing_mode="freedraw",
            stroke_color="white",
            background_color="#0e1117",
            stroke_width=4,
            key="sig_draw"
        )

        if sig_canvas.image_data is not None:

            sig_img = Image.fromarray(sig_canvas.image_data.astype("uint8")).convert("RGBA")

            # 👉 Transparent + black ink
            new_data = []
            for r, g, b, a in sig_img.getdata():
                if r < 50 and g < 50 and b < 50:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append((0, 0, 0, 255))
            sig_img.putdata(new_data)

            # -----------------------------
            # PAGE SELECT
            # -----------------------------
            page_num = st.slider("Select Page", 1, total_pages, 1)
            page = doc[page_num - 1]

            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            MAX_WIDTH = 700
            scale = 1
            if img.width > MAX_WIDTH:
                scale = MAX_WIDTH / img.width
                img = img.resize((int(img.width * scale), int(img.height * scale)))

            st.markdown("### 🎯 Drag & Resize Signature Box")

            # -----------------------------
            # DRAG UI (RECTANGLE)
            # -----------------------------
            canvas = st_canvas(
                background_image=img,
                height=img.height,
                width=img.width,
                drawing_mode="rect",
                stroke_color="#00ff88",
                fill_color="rgba(0,255,136,0.2)",
                stroke_width=2,
                key="pdf_canvas"
            )

            # -----------------------------
            # APPLY SIGNATURE
            # -----------------------------
            if canvas.json_data is not None and len(canvas.json_data["objects"]) > 0:

                obj = canvas.json_data["objects"][-1]

                x = obj["left"]
                y = obj["top"]
                w = obj["width"] * obj["scaleX"]
                h = obj["height"] * obj["scaleY"]

                st.success(f"📍 Position captured")

                # Live Preview
                preview = img.copy()
                sig_preview = sig_img.resize((int(w), int(h)))

                preview.paste(sig_preview, (int(x), int(y)), sig_preview)

                st.markdown("### 👀 Live Preview")
                st.image(preview)

                if st.button("🚀 Apply Signature"):

                    sig_path = os.path.join(OUTPUT_DIR, "sig.png")
                    sig_preview.save(sig_path)

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

                    st.success("✅ Signature applied!")

                    with open(out_path, "rb") as f:
                        st.download_button("⬇️ Download Signed PDF", f)
