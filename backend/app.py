import os
import json
import requests
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pdfplumber

# -------------------------
# 环境变量
# -------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ❗ 删除本地代理（Render 上不能用）
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10809"

# -------------------------
# Flask 初始化
# -------------------------
app = Flask(__name__)
CORS(app)

# -------------------------
# 全局向量数据库（lazy-load）
# -------------------------
embeddings = None
chunks = None
dimension = 768


# -------------------------
# PDF → 文本
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
# Gemini Embedding（带 timeout）
# -------------------------
def get_embedding(text):
    url = "https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent"

    payload = {
        "model": "models/embedding-001",
        "content": {"parts": [{"text": text}]}
    }

    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10   # ❗ 避免卡死
        )
        data = response.json()
        return np.array(data["embedding"]["values"], dtype="float32")
    except Exception as e:
        print("Embedding Error:", e)
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
# 检索
# -------------------------
def search_similar(query_emb, top_k=3):
    if embeddings is None:
        return []

    valid = [(i, emb) for i, emb in enumerate(embeddings) if np.linalg.norm(emb) > 0]
    if not valid:
        return []

    scores = [(i, cosine_similarity(query_emb, emb)) for i, emb in valid]
    scores.sort(key=lambda x: x[1], reverse=True)

    return [i for i, s in scores[:top_k]]


# -------------------------
# Gemini 回答（带 timeout）
# -------------------------
def ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10   # ❗ 避免卡死
        )
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini API Error: {e}"


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

    text = extract_text_from_pdf(pdf_path)
    chunks = [c for c in chunk_text(text) if c.strip() != ""]

    embeddings = [get_embedding(c) for c in chunks]

    return jsonify({"message": "PDF processed", "chunks": len(chunks)})


# -------------------------
# /ask
# -------------------------
@app.route("/ask", methods=["POST"])
def ask():
    global embeddings, chunks

    if embeddings is None or chunks is None:
        return jsonify({"error": "PDF not processed yet"}), 400

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

    return jsonify({"answer": answer, "related_chunks": related})


# -------------------------
# 主程序（Render 不会用到）
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)

