import os
import json
import argparse
from tqdm import tqdm
import re

# =========================
# Judge Prompt
# =========================

JUDGE_PROMPT = """
你是一个专业的QA任务评判专家，需要分析两个模型对同一个问题的处理结果，判断错误模型的问题出在哪个环节。
错误可能的环节有两个：
1. 问题分解能力：错误模型的子问题分解不合理、不完整，或者与正确分解存在明显偏差
2. 上下文抽取能力：错误模型的子问题分解与正确模型相近，但最终答案错误，原因是上下文信息抽取或推理错误

请根据以下信息进行评判：
问题：{question}

正确模型的问题分解结果：
{decomposed_right_str}

错误模型的问题分解结果：
{decomposed_wrong_str}

正确模型的最终答案：
{final_answer_right}

错误模型的最终答案：
{final_answer_wrong}

评判要求：
1. 首先对比两个模型的问题分解结果，判断是否存在显著差异
2. 然后结合最终答案的正确性，分析错误根源
3. 输出评判结论，格式为：
   - 错误环节：[问题分解能力/上下文抽取能力/两个能力均差]
   - 错误原因：[详细描述错误原因，100字以内]
   - 评判标签：[DECOMPOSE_ERROR/CONTEXT_EXTRACT_ERROR/ALL_ERROR]
"""


# =========================
# Model Wrapper
# =========================

class APIModel:
    def __init__(self, base_url, api_key, model_name):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name

    def generate(self, prompt):
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content


# =========================
# Data Loader
# =========================

def load_data(path):
    data = []
    if path.endswith(".json"):
        with open(path) as f:
            data = json.load(f)
    elif path.endswith(".jsonl"):
        with open(path) as f:
            for line in f:
                data.append(json.loads(line))
    return data


# =========================
# Prompt Builder（关键）
# =========================

def build_prompt(ex):
    return JUDGE_PROMPT.format(
        question=ex["question"],
        decomposed_right_str=ex["decomposed_right"],
        decomposed_wrong_str=ex["decomposed_wrong"],
        final_answer_right=ex["answer_right"],
        final_answer_wrong=ex["answer_wrong"]
    )


# =========================
# 解析模型输出（结构化）
# =========================

def parse_output(text):
    label = "UNKNOWN"
    reason = ""
    error_stage = ""

    # -------- 优先解析错误环节 --------
    stage_match = re.search(r"错误环节[:：]\s*([^\n]+)", text)
    if stage_match:
        error_stage = stage_match.group(1).strip()

        if "问题分解" in error_stage:
            label = "DECOMPOSE_ERROR"
        elif "上下文抽取" in error_stage:
            label = "CONTEXT_EXTRACT_ERROR"
        elif "两个能力均差" in error_stage:
            label = "ALL_ERROR"

    # -------- 兜底 label --------
    if label == "UNKNOWN":
        if "ALL_ERROR" in text:
            label = "ALL_ERROR"
        elif "DECOMPOSE_ERROR" in text:
            label = "DECOMPOSE_ERROR"
        elif "CONTEXT_EXTRACT_ERROR" in text:
            label = "CONTEXT_EXTRACT_ERROR"

    # -------- 错误原因 --------
    match = re.search(r"错误原因[:：](.*)", text)
    if match:
        reason = match.group(1).strip()

    return label, reason, error_stage
# =========================
# Evaluation
# =========================

def evaluate(model, data, output_path):
    results = []
    stat = {
        "DECOMPOSE_ERROR": 0,
        "CONTEXT_EXTRACT_ERROR": 0,
        "ALL_ERROR": 0,
        "UNKNOWN": 0
    }

    for ex in tqdm(data):
        prompt = build_prompt(ex)

        try:
            output = model.generate(prompt)
        except Exception as e:
            output = f"[ERROR] {e}"

        label, reason = parse_output(output)
        stat[label] += 1


        results.append({
    "id": ex.get("id"),
    "label": label,
    "error_stage": error_stage,   # ⭐ 新增
    "reason": reason,
    "raw_output": output
})

    # 保存结果
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 打印统计
    total = len(data)
    print("\n===== Error Distribution =====")
    for k, v in stat.items():
        print(f"{k}: {v} ({v/total:.2%})")


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, default="judge_result.json")

    parser.add_argument("--api_base", type=str, required=True)
    parser.add_argument("--api_key", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)

    args = parser.parse_args()

    model = APIModel(
        base_url=args.api_base,
        api_key=args.api_key,
        model_name=args.model_name
    )

    data = load_data(args.data_path)
    evaluate(model, data, args.output_path)


if __name__ == "__main__":
    main()