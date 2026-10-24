import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def ask_local_ai(prompt, json_mode=False):
    payload = {
        "model": "qwen3:4b-instruct-2507-q4_K_M",
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是电商运营分析助手，请用中文直接回答，默认不超过150字。"
                    "根据提供的数据回答，不编造数据。"
                    "区分已知事实与待验证原因。"
                ),
            },
                {"role": "user", "content": prompt},
        ],
        "stream": False,
        
        "options": {"temperature": 0.2, "num_predict": 2048},
    }
    if json_mode:
        payload["format"] = "json"
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(
            f"Ollama 返回错误，状态码：{exc.code}。"
            "请确认 qwen3:4b 已下载。"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            "无法连接本地模型，请确认 Ollama 应用正在运行。"
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            "模型响应超时，请稍后重试。"
        ) from exc

    if result.get("done_reason") == "length":
        raise RuntimeError(
        "回答达到生成长度上限，内容不完整。请缩短问题后重试。"
    )

    answer = result.get("message", {}).get("content", "").strip()

    # 只保留思考结束标记后的最终回答
    if "</think>" in answer:
        answer = answer.rsplit("</think>", 1)[1].strip()
    elif "<think>" in answer:
        raise RuntimeError("模型尚未生成完整回答，请重试。")

    if not answer:
        raise RuntimeError("模型没有返回正文，请重试。")

    return answer


if __name__ == "__main__":
    print("正在调用本地模型，请稍候……")
    try:
        answer = ask_local_ai(
            "已知：保温杯本期87笔订单，退款21笔，"
            "Python已计算退款率为24.14%。"
            "请用两句话解释结果，并说明能否确定退款原因。"
        )
        print(answer)
    except RuntimeError as exc:
        print(f"调用失败：{exc}")