import json
import argparse
from collections import defaultdict


# =========================
# Load
# =========================

def load_data(path):
    with open(path) as f:
        return json.load(f)


# =========================
# 1️⃣ 总体统计
# =========================

def overall_stats(results):
    stat = defaultdict(int)

    for r in results:
        stat[r.get("label", "UNKNOWN")] += 1

    total = len(results)

    print("\n===== Overall Error Distribution =====")
    for k in ["DECOMPOSE_ERROR", "CONTEXT_EXTRACT_ERROR", "ALL_ERROR", "UNKNOWN"]:
        v = stat.get(k, 0)
        print(f"{k}: {v} ({v/total:.2%})")

    return stat


# =========================
# 2️⃣ 错误环节统计（更细粒度）
# =========================

def stage_stats(results):
    stage_stat = defaultdict(int)

    for r in results:
        stage = r.get("error_stage", "UNKNOWN")
        stage_stat[stage] += 1

    print("\n===== Error Stage Breakdown =====")
    for k, v in stage_stat.items():
        print(f"{k}: {v}")

    return stage_stat


# =========================
# 3️⃣ Hard Cases（论文很有用）
# =========================

def find_hard_cases(results, top_k=20):
    hard_cases = [r for r in results if r["label"] != "UNKNOWN"]

    print(f"\n===== Hard Cases (Top {top_k}) =====")

    for r in hard_cases[:top_k]:
        print("\n------------------")
        print(f"ID: {r.get('id')}")
        print(f"Label: {r.get('label')}")
        print(f"Stage: {r.get('error_stage')}")
        print(f"Reason: {r.get('reason')[:100]}")


# =========================
# 4️⃣ 可选：skill维度分析（如果你有字段）
# =========================

def skill_stats(results):
    skill_stat = defaultdict(lambda: defaultdict(int))

    for r in results:
        skill = r.get("skill", None)
        if skill is None:
            continue

        label = r.get("label", "UNKNOWN")
        skill_stat[skill][label] += 1

    if len(skill_stat) == 0:
        print("\n(No skill field found, skip skill analysis)")
        return

    print("\n===== Skill-wise Analysis =====")
    for skill, d in skill_stat.items():
        total = sum(d.values())
        print(f"\n[{skill}] total={total}")
        for k, v in d.items():
            print(f"  {k}: {v} ({v/total:.2%})")


# =========================
# 5️⃣ 导出统计（画图用）
# =========================

def export_stat(stat, output_path):
    with open(output_path, "w") as f:
        json.dump(stat, f, indent=2)


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--top_k", type=int, default=20)
    parser.add_argument("--export_path", type=str, default=None)

    args = parser.parse_args()

    results = load_data(args.input_path)

    # 1. 总体
    stat = overall_stats(results)

    # 2. 错误环节
    stage_stats(results)

    # 3. hardest case
    find_hard_cases(results, args.top_k)

    # 4. skill分析
    skill_stats(results)

    # 5. 导出
    if args.export_path:
        export_stat(stat, args.export_path)
        print(f"\nSaved stat to {args.export_path}")


if __name__ == "__main__":
    main()