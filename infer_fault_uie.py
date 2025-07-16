#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""infer_fault_uie.py
~~~~~~~~~~~~~~~~~~~~~~
Command-line prediction tool for the fault-case UIE model trained with
`train_fault_uie.py`.

Example
-------
# Single sample
python infer_fault_uie.py \
    --model_checkpoint experiments/fault_uie/checkpoint/model_best \
    --text "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。"

# Batch file (one sentence per line)
python infer_fault_uie.py --model_checkpoint ... --file test_samples.txt
"""
import argparse
import json
from pathlib import Path
from pprint import pprint

# Local UIE predictor implementation from the repo
from uie_predictor import UIEPredictor

# Define the schema for this task (subject -> relations)
SCHEMA = [
    {"部件单元": ["部件故障", "组成"]},
    {"性能表征": ["性能故障"]},
    {"检测工具": ["检测工具"]},
    # Also extract standalone entities if needed
    "故障状态",
]


def build_predictor(model_path: str):
    return UIEPredictor(model="uie_base_pytorch", task_path=model_path, schema=SCHEMA)


def predict(predictor, text_list):
    """Run prediction; pretty-print JSON lines."""
    results = predictor(text_list)  # UIEPredictor supports batch input list
    for inp, res in zip(text_list, results):
        print("=== Input ===")
        print(inp)
        print("--- Extraction Result ---")
        pprint(res, compact=True, width=120)
        print()


def main(args):
    predictor = build_predictor(args.model_checkpoint)

    if args.text:
        predict(predictor, [args.text])
    else:
        # read file lines
        samples = [l.strip() for l in Path(args.file).read_text(encoding="utf-8").splitlines() if l.strip()]
        batch = []
        for line in samples:
            batch.append(line)
            if len(batch) == args.batch_size:
                predict(predictor, batch)
                batch = []
        if batch:
            predict(predictor, batch)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_checkpoint", required=True, help="Path to fine-tuned model directory (contains pytorch_model.bin).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Single input sentence to extract information from.")
    group.add_argument("--file", help="Text file with one sentence per line for batch prediction.")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for file mode.")
    args = parser.parse_args()
    main(args)