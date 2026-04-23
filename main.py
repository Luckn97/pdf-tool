# =========================================================
# 🤖 AI COMPARE (SMART)
# =========================================================
with menu[0]:
    st.header("🤖 AI PDF Compare")

    file1 = st.file_uploader("PDF 1", type=["pdf"], key="ai1")
    file2 = st.file_uploader("PDF 2", type=["pdf"], key="ai2")

    if file1 and file2:

        path1 = os.path.join(UPLOAD_DIR, file1.name)
        path2 = os.path.join(UPLOAD_DIR, file2.name)

        with open(path1, "wb") as f:
            f.write(file1.read())

        with open(path2, "wb") as f:
            f.write(file2.read())

        if st.button("🚀 Run AI Compare"):

            def extract_text(path):
                text = ""
                with pdfplumber.open(path) as pdf:
                    for p in pdf.pages:
                        text += p.extract_text() or ""
                return text

            text1 = extract_text(path1)
            text2 = extract_text(path2)

            # SPLIT INTO SENTENCES
            import re
            s1 = re.split(r'(?<=[.!?]) +', text1)
            s2 = re.split(r'(?<=[.!?]) +', text2)

            from difflib import SequenceMatcher

            changes = []

            for line1 in s1:
                best_ratio = 0
                best_match = ""

                for line2 in s2:
                    ratio = SequenceMatcher(None, line1, line2).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = line2

                if best_ratio < 0.75:
                    changes.append({
                        "type": "removed",
                        "text": line1
                    })
                else:
                    if line1 != best_match:
                        changes.append({
                            "type": "modified",
                            "old": line1,
                            "new": best_match
                        })

            # FIND ADDED
            for line2 in s2:
                if not any(line2 in c.get("new", "") for c in changes):
                    if line2 not in s1:
                        changes.append({
                            "type": "added",
                            "text": line2
                        })

            # -----------------------------
            # OUTPUT
            # -----------------------------
            st.subheader("🧠 Smart Differences")

            for c in changes[:50]:

                if c["type"] == "added":
                    st.success(f"➕ Added: {c['text']}")

                elif c["type"] == "removed":
                    st.error(f"➖ Removed: {c['text']}")

                elif c["type"] == "modified":
                    st.warning("✏️ Modified:")
                    st.write("OLD:", c["old"])
                    st.write("NEW:", c["new"])
                    st.markdown("---")
