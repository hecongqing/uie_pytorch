#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prepare_dataset.py
~~~~~~~~~~~~~~~~~~
Convert the original fault-case JSONL dataset (with SPO triples) into the
Doccano-style JSONL format expected by the UIE training pipeline that already
exists in this workspace (see `doccano.py`, `finetune.py`, etc.).

Usage
-----
python prepare_dataset.py \
    --input data/raw/train.jsonl \
    --output_doccano data/mid_data/doccano_train.jsonl

The generated file can be fed directly into `doccano.py` to construct the final
train/dev/test splits and create positive/negative samples for UIE fine-tuning,
for example:

python doccano.py \
    --doccano_file data/mid_data/doccano_train.jsonl \
    --task_type "ext" \
    --splits 0.8 0.1 0.1 \
    --save_dir data/final_data \
    --negative_ratio 3

Entity/Relation Type Mapping
----------------------------
The script infers the head & tail entity types from the relation label using
the mapping below (extend if new relations appear):
    "部件故障" -> ("部件单元", "故障状态")
    "性能故障" -> ("性能表征", "故障状态")
    "检测工具" -> ("检测工具", "性能表征")
    "组成"     -> ("部件单元", "部件单元")
"""
import argparse
import json
import os
from collections import OrderedDict

REL2_TYPES = {
    "部件故障": ("部件单元", "故障状态"),
    "性能故障": ("性能表征", "故障状态"),
    "检测工具": ("检测工具", "性能表征"),
    "组成": "部件单元",
}


def convert_line(raw_obj):
    """Convert one raw json object to doccano-style object."""
    text = raw_obj["text"]
    spo_list = raw_obj.get("spo_list", [])

    entities = OrderedDict()  # span -> id
    entities_out = []
    relations_out = []

    def _add_entity(name, start, end, label):
        span_key = (start, end, label)
        if span_key in entities:
            return entities[span_key]
        idx = len(entities)
        entities[span_key] = idx
        entities_out.append({
            "id": idx,
            "start_offset": start,
            "end_offset": end,
            "label": label
        })
        return idx

    for spo in spo_list:
        rel = spo["relation"]
        head = spo["h"]
        tail = spo["t"]
        if rel not in REL2_TYPES:
            raise ValueError(f"Unknown relation label: {rel}")
        head_type, tail_type = REL2_TYPES[rel] if isinstance(REL2_TYPES[rel], tuple) else (REL2_TYPES[rel], REL2_TYPES[rel])

        h_id = _add_entity(head["name"], head["pos"][0], head["pos"][1], head_type)
        t_id = _add_entity(tail["name"], tail["pos"][0], tail["pos"][1], tail_type)
        relations_out.append({
            "id": len(relations_out),
            "from_id": h_id,
            "to_id": t_id,
            "type": rel
        })

    return {
        "text": text,
        "entities": entities_out,
        "relations": relations_out
    }


def main(args):
    os.makedirs(os.path.dirname(args.output_doccano), exist_ok=True)

    with open(args.input, "r", encoding="utf-8") as fin, \
            open(args.output_doccano, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            raw_obj = json.loads(line)
            doccano_obj = convert_line(raw_obj)
            fout.write(json.dumps(doccano_obj, ensure_ascii=False) + "\n")

    print(f"Converted file saved to {args.output_doccano}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to raw train.jsonl (one json per line).")
    parser.add_argument("--output_doccano", required=True, help="Path to output doccano style jsonl.")
    args = parser.parse_args()
    main(args)