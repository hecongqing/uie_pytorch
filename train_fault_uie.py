#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""train_fault_uie.py
======================
A convenience wrapper that ties together the whole pipeline for the
高端装备制造故障案例数据集 using UIE (PyTorch version already in this repo).

Steps executed:
1. Convert the provided raw *fault case* JSONL (`ID`, `text`, `spo_list` ...)
   into Doccano-style JSONL via `prepare_dataset.py`.
2. Split the Doccano file into train / dev / test and construct negative
   samples with `doccano.py`.
3. Fine-tune the `uie_base_pytorch` (or other) model with `finetune.py`.

Example
-------
python train_fault_uie.py \
    --raw data/raw/train.jsonl \
    --work_dir data/fault_extraction \
    --model uie_base_pytorch \
    --device gpu \
    --batch_size 8 \
    --epochs 10

All intermediate artefacts are stored inside `work_dir`:
* mid_data/doccano_train.jsonl       – converted Doccano annotations
* final_data/train.txt / dev.txt ... – UIE finetune files
* checkpoint/                        – model checkpoints (best model in `model_best/`)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: str):
    """Utility: run shell command, stream output, exit on error."""
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"Command failed with code {res.returncode}")
        sys.exit(res.returncode)


def main(args):
    work_dir = Path(args.work_dir)
    mid_dir = work_dir / "mid_data"
    final_dir = work_dir / "final_data"
    checkpoint_dir = work_dir / "checkpoint"

    mid_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # 1. raw -> doccano
    doccano_file = mid_dir / "doccano_train.jsonl"
    convert_cmd = (
        f"python prepare_dataset.py --input {args.raw} --output_doccano {doccano_file}"
    )
    run(convert_cmd)

    # 2. doccano -> UIE train/dev/test (negative sampling etc.)
    doccano_cmd = (
        "python doccano.py "
        f"--doccano_file {doccano_file} "
        "--task_type ext "
        f"--splits {args.split_train} {args.split_dev} {args.split_test} "
        f"--save_dir {final_dir} "
        f"--negative_ratio {args.negative_ratio} "
        "--is_shuffle True"
    )
    run(doccano_cmd)

    # 3. Finetune UIE
    train_txt = final_dir / "train.txt"
    dev_txt = final_dir / "dev.txt"

    finetune_cmd = (
        "python finetune.py "
        f"--train_path {train_txt} "
        f"--dev_path {dev_txt} "
        f"--save_dir {checkpoint_dir} "
        f"--learning_rate {args.lr} "
        f"--batch_size {args.batch_size} "
        f"--max_seq_len {args.max_seq_len} "
        f"--num_epochs {args.epochs} "
        f"--model {args.model} "
        f"--seed {args.seed} "
        f"--logging_steps {args.logging_steps} "
        f"--valid_steps {args.valid_steps} "
        f"--device {args.device} "
        f"--max_model_num {args.keep_last} "
        "--early_stopping"
    )
    run(finetune_cmd)

    print("\n✅ Training complete. Best model saved to:", checkpoint_dir / "model_best")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="Path to raw train.jsonl with spo_list.")
    parser.add_argument("--work_dir", default="./experiments/fault_uie", help="Working directory for outputs.")
    parser.add_argument("--model", default="uie_base_pytorch", help="Pre-trained UIE model name or path.")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="gpu")

    # training hyper-params
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--max_seq_len", type=int, default=512)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--logging_steps", type=int, default=10)
    parser.add_argument("--valid_steps", type=int, default=100)
    parser.add_argument("--keep_last", type=int, default=3, help="Keep last N checkpoints besides best.")

    # dataset splitting / sampling
    parser.add_argument("--split_train", type=float, default=0.8)
    parser.add_argument("--split_dev", type=float, default=0.1)
    parser.add_argument("--split_test", type=float, default=0.1)
    parser.add_argument("--negative_ratio", type=int, default=3)

    args = parser.parse_args()
    main(args)