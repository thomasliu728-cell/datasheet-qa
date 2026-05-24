import os
import json
import requests
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pdfplumber

# -------------------------
# 环境变量 & 代理
# -------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10809"

# -------------------------
# Flask 初始化
# -------------------------
app = Flask(__name__)
CORS(app)  # 允许前端跨域访问

# -------------------------
# 全局向量数据库
# -------------------------
embeddings = []
chunks = []
dimension = 768

# -------------------------
# PDF → 文本（使用 pdfplumber，最稳定）
# -------------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text

# -------------------------
# 文本分块
# -------------------------
def chunk_text(text, chunk_size=500):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# -------------------------
# Gemini Embedding（embedding-001）
# -------------------------
def get_embedding(text):
    url = "https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent"

    payload = {
        "model": "models/embedding-001",
        "content": {"parts": [{"text": text}]}
    }

    response = requests.post(
        url,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json=payload
    )

    data = response.json()

    try:
        return np.array(data["embedding"]["values"], dtype="float32")
    except:
        print("Embedding Error:", data)
        return np.zeros(dimension, dtype="float32")

# -------------------------
# 余弦相似度
# -------------------------
def cosine_similarity(a, b):
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0
    return float(np.dot(a, b) / (na * nb))

# -------------------------
# 检索（永远返回 top_k，不会空）
# -------------------------
def search_similar(query_emb, top_k=3):
    valid = [(i, emb) for i, emb in enumerate(embeddings) if np.linalg.norm(emb) > 0]

    if not valid:
        return []

    scores = [(i, cosine_similarity(query_emb, emb)) for i, emb in valid]
    scores.sort(key=lambda x: x[1], reverse=True)

    return [i for i, s in scores[:top_k]]

# -------------------------
# Gemini 回答
# -------------------------
def ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(
        url,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json=payload
    )

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return f"Gemini API Error: {data}"

# -------------------------
# /process_pdf
# -------------------------
@app.route("/process_pdf", methods=["POST"])
def process_pdf():
    global embeddings, chunks

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    pdf_path = "uploaded.pdf"
    file.save(pdf_path)

    print("PDF received")

    text = extract_text_from_pdf(pdf_path)
    print("PDF text length:", len(text))

    chunks = chunk_text(text)
    chunks = [c for c in chunks if c.strip() != ""]
    print("Chunks:", len(chunks))

    embeddings = [get_embedding(c) for c in chunks]

    print("First embedding sample:", embeddings[0][:10] if embeddings else "None")

    return jsonify({"message": "PDF processed", "chunks": len(chunks)})

# -------------------------
# /ask
# -------------------------
@app.route("/ask", methods=["POST"])
def ask():
    global embeddings, chunks

    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    q_emb = get_embedding(question)
    top_indices = search_similar(q_emb, top_k=3)

    related = [chunks[i] for i in top_indices]
    context = "\n\n".join(related)

    prompt = f"你是一个专业的电子工程师，请根据以下 datasheet 内容回答问题：\n\n{context}\n\n问题：{question}"

    answer = ask_gemini(prompt)

    return jsonify({
        "answer": answer,
        "related_chunks": related
    })

# -------------------------
# 主程序
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
