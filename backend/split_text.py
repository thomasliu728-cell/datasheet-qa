import re

def clean_text(text):
    """
    功能：清洗文本，去掉多余空格、空行等
    参数：
        text (str): 原始文本
    返回：
        cleaned (str): 清洗后的文本
    """

    # 去掉 Windows/Mac/Linux 的各种换行符
    text = text.replace("\r", "").replace("\n", "\n")

    # 去掉连续多个空行（只保留一个）
    text = re.sub(r"\n\s*\n", "\n", text)

    # 去掉行首行尾空格
    text = text.strip()

    return text


def split_into_chunks(text, max_length=400):
    """
    功能：把长文本切成小段（chunk），每段不超过 max_length 字
    参数：
        text (str): 清洗后的整段文本
        max_length (int): 每段最大长度（默认 400 字）
    返回：
        chunks (list[str]): 切好的文本段落列表
    """

    chunks = []
    current = ""

    # 按句号、分号、换行等切分
    sentences = re.split(r"(?<=[。；;.!?])", text)

    for sentence in sentences:
        # 如果当前段落加上新句子还不超过 max_length，就继续累积
        if len(current) + len(sentence) <= max_length:
            current += sentence
        else:
            # 否则把当前段落存起来，重新开始
            if current.strip():
                chunks.append(current.strip())
            current = sentence

    # 最后一段也要加入
    if current.strip():
        chunks.append(current.strip())

    return chunks


if __name__ == "__main__":
    # 测试用：从 extract_pdf.py 复制一段文本来试试
    sample_text = """
    The AO3400A uses advanced trench MOSFET technology.
    It provides excellent RDS(on) performance.
    Suitable for high efficiency applications.
    """

    cleaned = clean_text(sample_text)
    chunks = split_into_chunks(cleaned, max_length=50)

    print("===== 清洗后的文本 =====")
    print(cleaned)

    print("\n===== 切分后的段落 =====")
    for i, c in enumerate(chunks):
        print(f"[段落 {i+1}] {c}")
