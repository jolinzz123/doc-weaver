import json
import sys
from pathlib import Path

from ollama import Client

from tools import list_documents, read_document, save_report


MODEL_NAME = "qwen3.5:4b"
MAX_STEPS = 10

# 固定连接本机 Ollama，并忽略可能干扰 localhost 的系统代理。
client = Client(
    host="http://127.0.0.1:11434",
    trust_env=False,
)


# 告诉模型：它可以使用哪些工具
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "递归查看所选文件夹及其所有子文件夹中可以整理的文档。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "读取列表中的 TXT 或 Markdown 文档，包括子文件夹中的文档。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "文档相对于所选文件夹的路径，例如会议/项目会议.txt",
                    }
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_report",
            "description": "将最终文档整理报告保存到 output/report.md。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "完整的 Markdown 整理报告",
                    }
                },
                "required": ["content"],
            },
        },
    },
]


def run_agent(task, target_dir):
    """运行文档整理智能体。"""

    # 将工具限制在用户本次明确选择的文件夹中。
    available_functions = {
        "list_documents": lambda: list_documents(target_dir),
        "read_document": lambda file_name: read_document(file_name, target_dir),
        "save_report": save_report,
    }

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个文档整理智能体。"
                f"用户本次选择的文件夹是：{target_dir}。"
                "你必须先递归查看文档列表，再逐份读取列表中的所有文档。"
                "然后根据主题对文档分类，并为每份文档生成摘要、重点和待办事项。"
                "最后生成中文 Markdown 报告，并调用 save_report 保存报告。"
                "不得编造文档中不存在的信息。"
            ),
        },
        {
            "role": "user",
            "content": task,
        },
    ]

    trace = []

    for step in range(1, MAX_STEPS + 1):
        print(f"\n===== 第 {step} 步 =====")

        response = client.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            think=False,
        )

        # 保存模型本轮回复
        messages.append(response.message)

        tool_calls = response.message.tool_calls

        # 没有工具调用，说明模型认为任务已经完成
        if not tool_calls:
            final_answer = response.message.content

            print("\n===== 最终回答 =====")
            print(final_answer)

            save_trace(trace)
            return final_answer

        # 执行模型选择的工具
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = dict(tool_call.function.arguments)

            print(f"调用工具：{tool_name}")
            print(f"工具参数：{arguments}")

            function_to_call = available_functions.get(tool_name)

            if function_to_call is None:
                result = {
                    "success": False,
                    "error": f"未知工具：{tool_name}",
                }
            else:
                try:
                    result = function_to_call(**arguments)
                except Exception as error:
                    result = {
                        "success": False,
                        "error": str(error),
                    }

            print(f"工具结果：{result}")

            trace.append(
                {
                    "step": step,
                    "target_folder": str(target_dir),
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            # 把工具结果交回模型
            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    save_trace(trace)
    print("智能体达到最大执行步数，已经停止。")
    return None


def save_trace(trace):
    """保存智能体的工具调用轨迹。"""

    from tools import OUTPUT_DIR

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trace_path = OUTPUT_DIR / "trace.json"

    trace_path.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"执行轨迹已保存：{trace_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_input = sys.argv[1]
    else:
        folder_input = input(
            "请输入要整理的文件夹路径（直接回车使用项目内 documents）：\n> "
        ).strip()

    if folder_input:
        selected_folder = Path(folder_input).expanduser().resolve()
    else:
        selected_folder = Path(__file__).resolve().parent / "documents"

    if not selected_folder.exists() or not selected_folder.is_dir():
        raise SystemExit(f"文件夹不存在：{selected_folder}")

    print(f"本次整理文件夹：{selected_folder}")

    run_agent(
        "请整理我选择的文件夹中的所有文档，"
        "按照主题分类并生成摘要、重点和待办事项，"
        "最后把完整报告保存为 report.md。",
        selected_folder,
    )
