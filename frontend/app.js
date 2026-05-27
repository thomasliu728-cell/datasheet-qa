const isLocal = ["localhost", "127.0.0.1"].includes(location.hostname);

const API_BASE = isLocal
  ? "http://127.0.0.1:5000"
  : "https://datasheet-qa-backend.onrender.com";


// 上传 PDF
async function uploadPDF() {
    const fileInput = document.getElementById("pdfFile");
    if (!fileInput.files.length) {
        alert("请先选择 PDF 文件");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    document.getElementById("uploadStatus").innerText = "正在上传并处理 PDF...";

    const res = await fetch(`${API_BASE}/process_pdf`, {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    document.getElementById("uploadStatus").innerText =
        `PDF 处理完成，共 ${data.chunks} 个 chunks`;
}

// 提问
async function askQuestion() {
    const question = document.getElementById("questionInput").value;
    if (!question) {
        alert("请输入问题");
        return;
    }

    document.getElementById("answerBox").innerText = "正在生成回答...";
    document.getElementById("chunkBox").innerText = "";

    const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question})
    });

    const data = await res.json();

    document.getElementById("answerBox").innerText = data.answer || "无回答";

    let chunksText = "";
    data.related_chunks.forEach((c, i) => {
        chunksText += `--- Chunk ${i} ---\n${c}\n\n`;
    });

    document.getElementById("chunkBox").innerText = chunksText || "无相关内容";
}
