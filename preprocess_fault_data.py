#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障案例信息抽取数据预处理脚本
将原始故障案例数据转换为UIE训练格式
"""

import json
import os
import argparse
from typing import List, Dict, Any
from utils import convert_ext_examples, logger


def load_fault_data(file_path: str) -> List[Dict[str, Any]]:
    """
    加载故障案例数据
    
    Args:
        file_path: 数据文件路径
        
    Returns:
        数据列表
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def convert_fault_data_to_doccano_format(fault_data: List[Dict[str, Any]]) -> List[str]:
    """
    将故障案例数据转换为doccano格式
    
    Args:
        fault_data: 原始故障案例数据
        
    Returns:
        doccano格式的数据列表
    """
    doccano_data = []
    
    for item in fault_data:
        text = item['text']
        spo_list = item.get('spo_list', [])
        
        # 提取实体和关系
        entities = []
        relations = []
        entity_id = 0
        
        # 实体映射
        entity_map = {}
        
        # 处理每个三元组
        for spo in spo_list:
            head = spo['h']
            tail = spo['t']
            relation = spo['relation']
            
            # 添加头实体
            head_entity = {
                "id": entity_id,
                "start_offset": head['pos'][0],
                "end_offset": head['pos'][1],
                "label": get_entity_type(head['name'])
            }
            entities.append(head_entity)
            entity_map[entity_id] = {
                "name": head['name'],
                "start": head['pos'][0],
                "end": head['pos'][1]
            }
            head_id = entity_id
            entity_id += 1
            
            # 添加尾实体
            tail_entity = {
                "id": entity_id,
                "start_offset": tail['pos'][0],
                "end_offset": tail['pos'][1],
                "label": get_entity_type(tail['name'])
            }
            entities.append(tail_entity)
            entity_map[entity_id] = {
                "name": tail['name'],
                "start": tail['pos'][0],
                "end": tail['pos'][1]
            }
            tail_id = entity_id
            entity_id += 1
            
            # 添加关系
            relation_item = {
                "id": len(relations),
                "from_id": head_id,
                "to_id": tail_id,
                "type": relation
            }
            relations.append(relation_item)
        
        # 去重实体
        unique_entities = []
        seen_entities = set()
        for entity in entities:
            entity_key = (entity['start_offset'], entity['end_offset'], entity['label'])
            if entity_key not in seen_entities:
                unique_entities.append(entity)
                seen_entities.add(entity_key)
        
        # 构建doccano格式
        doccano_item = {
            "text": text,
            "entities": unique_entities,
            "relations": relations
        }
        
        doccano_data.append(json.dumps(doccano_item, ensure_ascii=False))
    
    return doccano_data


def get_entity_type(entity_name: str) -> str:
    """
    根据实体名称判断实体类型
    
    Args:
        entity_name: 实体名称
        
    Returns:
        实体类型
    """
    # 这里可以根据实际需求调整实体类型判断逻辑
    # 目前简单返回一个通用类型，实际使用时可以根据实体名称特征进行更精确的分类
    
    # 部件单元特征词
    component_keywords = ['泵', '器', '机', '阀', '管', '盖', '锁', '铰链', '变压器', '分离器']
    # 性能表征特征词
    performance_keywords = ['压力', '转速', '温度', '液面', '电流', '电压', '功率']
    # 故障状态特征词
    fault_keywords = ['抖动', '松旷', '损坏', '漏油', '断裂', '变形', '卡滞', '变低', '不良', '无法起动']
    # 检测工具特征词
    tool_keywords = ['互感器', '保护器', '测试仪', '检测器', '传感器']
    
    for keyword in component_keywords:
        if keyword in entity_name:
            return "部件单元"
    
    for keyword in performance_keywords:
        if keyword in entity_name:
            return "性能表征"
    
    for keyword in fault_keywords:
        if keyword in entity_name:
            return "故障状态"
    
    for keyword in tool_keywords:
        if keyword in entity_name:
            return "检测工具"
    
    # 默认返回部件单元
    return "部件单元"


def main():
    parser = argparse.ArgumentParser(description="故障案例数据预处理")
    parser.add_argument("--input_file", type=str, required=True, help="输入数据文件路径")
    parser.add_argument("--output_dir", type=str, default="./data", help="输出目录")
    parser.add_argument("--negative_ratio", type=int, default=3, help="负样本比例")
    parser.add_argument("--splits", type=float, nargs=3, default=[0.8, 0.1, 0.1], 
                       help="训练/验证/测试集比例")
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 加载数据
    logger.info(f"Loading data from {args.input_file}")
    fault_data = load_fault_data(args.input_file)
    logger.info(f"Loaded {len(fault_data)} samples")
    
    # 转换为doccano格式
    logger.info("Converting to doccano format")
    doccano_data = convert_fault_data_to_doccano_format(fault_data)
    
    # 保存doccano格式数据
    doccano_file = os.path.join(args.output_dir, "doccano.json")
    with open(doccano_file, 'w', encoding='utf-8') as f:
        for line in doccano_data:
            f.write(line + '\n')
    logger.info(f"Saved doccano format data to {doccano_file}")
    
    # 转换为UIE训练格式
    logger.info("Converting to UIE training format")
    
    # 定义实体类型和关系类型
    entity_types = ["部件单元", "性能表征", "故障状态", "检测工具"]
    relation_types = ["部件故障", "性能故障", "检测工具", "组成"]
    
    # 使用convert_ext_examples函数转换数据
    examples = convert_ext_examples(
        doccano_data,
        negative_ratio=args.negative_ratio,
        prompt_prefix="故障信息",
        options=entity_types,
        separator="##",
        is_train=True
    )
    
    # 划分数据集
    total_samples = len(examples)
    train_size = int(total_samples * args.splits[0])
    dev_size = int(total_samples * args.splits[1])
    
    train_examples = examples[:train_size]
    dev_examples = examples[train_size:train_size + dev_size]
    test_examples = examples[train_size + dev_size:]
    
    # 保存训练数据
    train_file = os.path.join(args.output_dir, "train.txt")
    with open(train_file, 'w', encoding='utf-8') as f:
        for example in train_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # 保存验证数据
    dev_file = os.path.join(args.output_dir, "dev.txt")
    with open(dev_file, 'w', encoding='utf-8') as f:
        for example in dev_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # 保存测试数据
    test_file = os.path.join(args.output_dir, "test.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        for example in test_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved training data: {len(train_examples)} samples to {train_file}")
    logger.info(f"Saved validation data: {len(dev_examples)} samples to {dev_file}")
    logger.info(f"Saved test data: {len(test_examples)} samples to {test_file}")
    
    # 保存配置信息
    config = {
        "entity_types": entity_types,
        "relation_types": relation_types,
        "total_samples": total_samples,
        "train_samples": len(train_examples),
        "dev_samples": len(dev_examples),
        "test_samples": len(test_examples)
    }
    
    config_file = os.path.join(args.output_dir, "config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved config to {config_file}")
    logger.info("Data preprocessing completed!")


if __name__ == "__main__":
    main()