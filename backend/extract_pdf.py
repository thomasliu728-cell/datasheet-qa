import pdfplumber
from pathlib import Path

def extract_pdf_text(pdf_path):
    """
    功能：从 PDF 文件中提取纯文本
    参数：
        pdf_path (str): PDF 文件路径
    返回：
        text_list (list[str]): 每一页的文本组成的列表
    """

    text_list = []  # 用来存储每一页的文本

    # 打开 PDF 文件
    with pdfplumber.open(pdf_path) as pdf:
        # 遍历每一页
        for page_number, page in enumerate(pdf.pages):
            # 提取当前页的文本
            text = page.extract_text()

            # 有些页可能没有文本（比如纯图片页），需要判断
            if text:
                text_list.append(text)
            else:
                text_list.append("")  # 保持页数一致

            print(f"已提取第 {page_number + 1} 页")

    return text_list


if __name__ == "__main__":
    # 根据脚本位置找到 samples 目录
    script_dir = Path(__file__).parent
    pdf_path = script_dir.parent / "samples" / "HC4407.pdf"

    # 调用函数
    pages = extract_pdf_text(pdf_path)

    # 打印前 500 字作为预览
    print("\n===== PDF 文本预览（前 500 字） =====")
    preview = "\n".join(pages)[:500]
    print(preview)
