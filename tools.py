from pathlib import Path


# tools.py 所在的项目文件夹
PROJECT_DIR = Path(__file__).resolve().parent

# 待整理文档所在的文件夹
DOCUMENTS_DIR = PROJECT_DIR / "documents"
OUTPUT_DIR = PROJECT_DIR / "output"


def get_documents_dir(folder_path=None):
    """解析用户选择的文档文件夹；未指定时使用项目内的 documents。"""

    if folder_path is None:
        return DOCUMENTS_DIR.resolve()

    return Path(folder_path).expanduser().resolve()


def list_documents(folder_path=None):
    """递归列出指定文件夹及其子文件夹中的 TXT 和 Markdown 文档。"""

    documents_dir = get_documents_dir(folder_path)

    if not documents_dir.exists() or not documents_dir.is_dir():
        return {
            "success": False,
            "error": f"文件夹不存在：{documents_dir}",
            "files": [],
        }

    files = []

    for file_path in documents_dir.rglob("*"):
        relative_path = file_path.relative_to(documents_dir)

        # 跳过 .git、.venv 等隐藏目录及其中的文件。
        if any(part.startswith(".") for part in relative_path.parts):
            continue

        if file_path.is_file() and file_path.suffix.lower() in {".txt", ".md"}:
            files.append(relative_path.as_posix())

    files.sort()

    return {
        "success": True,
        "folder": str(documents_dir),
        "count": len(files),
        "files": files,
    }


def read_document(file_name, folder_path=None):
    """读取指定文件夹中的一份 TXT 或 Markdown 文档。"""

    documents_dir = get_documents_dir(folder_path)

    # 允许读取子文件夹中的相对路径，但禁止越出用户选择的文件夹。
    file_path = (documents_dir / file_name).resolve()

    try:
        file_path.relative_to(documents_dir)
    except ValueError:
        return {
            "success": False,
            "error": "文件路径超出所选文件夹",
        }

    if file_path.suffix.lower() not in {".txt", ".md"}:
        return {
            "success": False,
            "error": "只允许读取 TXT 和 Markdown 文件",
        }

    if not file_path.exists() or not file_path.is_file():
        return {
            "success": False,
            "error": f"找不到文件：{file_name}",
        }

    try:
        content = file_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "file_name": Path(file_name).as_posix(),
            "character_count": len(content),
            "content": content,
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"无法使用 UTF-8 读取：{file_name}",
        }


def save_report(content, file_name="report.md"):
    """把整理报告保存到 output 文件夹。"""

    # 防止文件被保存到 output 以外的位置
    if Path(file_name).name != file_name:
        return {
            "success": False,
            "error": "文件名不合法",
        }

    if not file_name.lower().endswith(".md"):
        return {
            "success": False,
            "error": "报告必须使用 .md 格式",
        }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / file_name

    try:
        report_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "file_name": file_name,
            "saved_path": str(report_path),
            "character_count": len(content),
        }

    except OSError as error:
        return {
            "success": False,
            "error": f"保存失败：{error}",
        }


if __name__ == "__main__":
    test_report = """# 文档整理报告

## 测试结果

已经成功读取项目会议文档。

- 文档类型：会议记录
- 状态：等待智能体生成正式摘要
"""

    result = save_report(test_report)
    print("保存报告：")
    print(result)
