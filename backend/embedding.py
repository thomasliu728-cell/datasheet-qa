from sentence_transformers import SentenceTransformer
import numpy as np

# 1. 加载 embedding 模型（MiniLM 是轻量且效果不错的模型）
# 第一次运行会自动下载模型
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_text(text):
    """
    功能：将一段文本转成 embedding 向量
    参数：
        text (str): 输入文本
    返回：
        numpy.ndarray: embedding 向量（长度 384）
    """
    embedding = model.encode(text)
    return np.array(embedding)


def embed_chunks(chunk_list):
    """
    功能：将多个 chunk 批量向量化
    参数：
        chunk_list (list[str]): 文本段落列表
    返回：
        list[numpy.ndarray]: 每个 chunk 的向量
    """
    vectors = model.encode(chunk_list)
    return [np.array(v) for v in vectors]


def cosine_similarity(vec1, vec2):
    """
    功能：计算两个向量的余弦相似度（用于检索最相关 chunk）
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def find_most_similar(query, chunks, vectors, top_k=3):
    """
    功能：根据用户问题，找到最相关的 chunk
    参数：
        query (str): 用户问题
        chunks (list[str]): 所有 chunk 文本
        vectors (list[np.ndarray]): 所有 chunk 的向量
        top_k (int): 返回前 k 个最相关段落
    返回：
        list[(chunk, score)]
    """

    # 1. 对问题向量化
    query_vec = embed_text(query)

    # 2. 计算与每个 chunk 的相似度
    scores = []
    for chunk, vec in zip(chunks, vectors):
        score = cosine_similarity(query_vec, vec)
        scores.append((chunk, score))

    # 3. 按相似度排序
    scores.sort(key=lambda x: x[1], reverse=True)

    # 4. 返回前 top_k 个
    return scores[:top_k]


if __name__ == "__main__":
    # 测试用
    chunks = [
        "RDS(on) at VGS=10V is 15mΩ",
        "This MOSFET uses trench technology",
        "Gate charge is 6.3nC"
    ]

    vectors = embed_chunks(chunks)

    result = find_most_similar("这个 MOS 的 RDS(on) 是多少？", chunks, vectors)

    print("===== 最相关的 chunk =====")
    for c, s in result:
        print(f"相似度: {s:.4f} | 内容: {c}")
