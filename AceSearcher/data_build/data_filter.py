import json
import argparse


def load_json(path):
    with open(path) as f:
        return json.load(f)


def is_valid(ex):
    """
    子任务感知 + 蒸馏有效性过滤
    完全对齐论文第四章
    """

    # =========================
    # 1️⃣ 必须是有效错误（核心）
    # =========================
    if ex["label"] == "UNKNOWN":
        return False

    # =========================
    # 2️⃣ teacher 必须正确（关键）
    # =========================
    # 如果你有 answer_gt，可以这样：
    if "answer_gt" in ex:
        if ex["chosen"].strip() != ex["answer_gt"].strip():
            return False

    # =========================
    # 3️⃣ student 必须错误（关键）
    # =========================
    if "answer_gt" in ex:
        if ex["rejected"].strip() == ex["answer_gt"].strip():
            return False

    # =========================
    # 4️⃣ 必须有学习信号（核心）
    # =========================
    if ex["chosen"].strip() == ex["rejected"].strip():
        return False

    # =========================
    # 5️⃣ 子任务有效性（论文关键）
    # =========================
    # ALL_ERROR 可以保留（高价值样本）
    if ex["label"] not in [
        "DECOMPOSE_ERROR",
        "CONTEXT_EXTRACT_ERROR",
        "ALL_ERROR"
    ]:
        return False

    # =========================
    # 6️⃣ 去掉无效短文本（弱约束）
    # =========================
    if len(ex["chosen"]) < 3 or len(ex["rejected"]) < 3:
        return False

    return True


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)

    args = parser.parse_args()

    data = load_json(args.input_path)

    filtered = []
    drop_stat = {
        "unknown": 0,
        "no_signal": 0,
        "teacher_wrong": 0,
        "student_correct": 0,
        "invalid_label": 0,
    }

    for ex in data:
        keep = True

        if ex["label"] == "UNKNOWN":
            drop_stat["unknown"] += 1
            keep = False

        elif ex["chosen"].strip() == ex["rejected"].strip():
            drop_stat["no_signal"] += 1
            keep = False

        elif "answer_gt" in ex:
            if ex["chosen"].strip() != ex["answer_gt"].strip():
                drop_stat["teacher_wrong"] += 1
                keep = False
            elif ex["rejected"].strip() == ex["answer_gt"].strip():
                drop_stat["student_correct"] += 1
                keep = False

        elif ex["label"] not in [
            "DECOMPOSE_ERROR",
            "CONTEXT_EXTRACT_ERROR",
            "ALL_ERROR"
        ]:
            drop_stat["invalid_label"] += 1
            keep = False

        if keep:
            filtered.append(ex)

    with open(args.output_path, "w") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)

    print(f"\n===== Filter Result =====")
    print(f"Remain: {len(filtered)} / {len(data)}")

    print("\nDrop stats:")
    for k, v in drop_stat.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()