from PyPDF2 import PdfReader

pdf_path = "HC4407.pdf"

reader = PdfReader(pdf_path)
text = ""

for i, page in enumerate(reader.pages):
    page_text = page.extract_text() or ""
    print(f"\n===== Page {i+1} =====")
    print(page_text)
    text += page_text

# 分块（和你 app.py 一样）
def chunk_text(text, chunk_size=500):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

chunks = chunk_text(text)

print("\n\n===== CHUNKS =====")
for idx, c in enumerate(chunks):
    print(f"\n--- Chunk {idx} ---")
    print(repr(c))  # 用 repr 可以看到空字符串
