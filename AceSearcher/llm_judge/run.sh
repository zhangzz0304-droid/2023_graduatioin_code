#!/bin/bash

# ========================
# 基本配置
# ========================

API_BASE="https://api.openai.com/v1"
API_KEY="YOUR_KEY"
MODEL_NAME="gpt-4o"

DATA_PATH="data/judge_input.json"
OUTPUT_PATH="output/judge_result.json"

# ========================
# Step 1: Error Attribution
# ========================

echo "Running judge..."

python judge.py \
  --data_path $DATA_PATH \
  --output_path $OUTPUT_PATH \
  --api_base $API_BASE \
  --api_key $API_KEY \
  --model_name $MODEL_NAME

# ========================
# Step 2: Analysis
# ========================

echo "Running analysis..."

python analysis.py \
  --input_path $OUTPUT_PATH \
  --top_k 20 \
  --export_path stat.json

echo "Done."