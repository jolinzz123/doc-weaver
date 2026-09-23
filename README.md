# DocWeaver — 本地文档整理智能体

一个使用 Python、Ollama 和 Qwen 3.5 构建的最小文档整理智能体。

智能体能够整理用户在启动时选择的任意文件夹，递归读取该文件夹及其所有子文件夹中的 Markdown 和 TXT 文档，按照主题进行分类，提取摘要、重点和待办事项，并将结果保存为 Markdown 报告。同时，它会把工具调用过程记录为 JSON，方便观察智能体如何完成任务。

## 工作流程

1. 调用 `list_documents` 获取文档列表。
2. 调用 `read_document` 逐份读取文档。
3. 使用本地大模型分析、分类和总结内容。
4. 调用 `save_report` 生成 `output/report.md`。
5. 将工具调用轨迹保存到 `output/trace.json`。

## 项目结构

```text
document-agent/
├── agent.py
├── tools.py
├── requirements.txt
├── documents/
└── output/
```

## 环境要求

- Python 3.9 或更高版本
- Ollama
- `qwen3.5:4b` 模型

## 安装

首先安装并启动 [Ollama](https://ollama.com/)，然后下载模型：

```bash
ollama run qwen3.5:4b
```

创建并启用 Python 虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

## 使用方法

直接运行程序，并按提示输入需要整理的文件夹路径：

```bash
python agent.py
```

直接按回车会使用项目内的 `documents` 文件夹。也可以在命令中指定其他文件夹，路径包含空格时请加引号：

```bash
python agent.py "/Users/你的用户名/Documents/学习资料"
```

运行完成后查看：

- `output/report.md`：文档整理报告
- `output/trace.json`：工具调用轨迹

## 内置工具

- `list_documents(folder_path)`：递归列出所选文件夹及子文件夹内支持的文档。
- `read_document(file_name, folder_path)`：根据相对路径安全读取所选文件夹内的指定文档。
- `save_report(content)`：保存 Markdown 报告。

## 隐私说明

模型通过 Ollama 在本机运行，文档内容不会为了模型推理而发送到第三方 API。上传 GitHub 前，请确认 `documents` 中只包含可公开的示例文件，不要提交私人或机密资料。

智能体每次只读取用户启动时明确选择的文件夹及其子文件夹，不会越出该目录浏览电脑中的其他位置。`.git`、`.venv` 等隐藏目录会自动跳过。

## 当前限制

- 仅支持 UTF-8 编码的 `.txt` 和 `.md` 文件。
- 本地小模型可能生成不准确的信息，重要内容需要人工检查。
- 当前版本不会移动、重命名或删除原始文档。
