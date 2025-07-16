#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障案例信息抽取预测脚本
使用训练好的UIE模型进行故障案例的实体和关系抽取
"""

import json
import argparse
import os
from typing import List, Dict, Any
from pprint import pprint

from uie_predictor import UIEPredictor


def load_config(config_file: str) -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_test_data(file_path: str) -> List[Dict[str, Any]]:
    """加载测试数据"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def extract_fault_info(text: str, predictor: UIEPredictor, config: dict) -> Dict[str, Any]:
    """
    从故障文本中抽取信息
    
    Args:
        text: 故障文本
        predictor: UIE预测器
        config: 配置信息
        
    Returns:
        抽取结果
    """
    entity_types = config.get("entity_types", ["部件单元", "性能表征", "故障状态", "检测工具"])
    relation_types = config.get("relation_types", ["部件故障", "性能故障", "检测工具", "组成"])
    
    result = {
        "text": text,
        "entities": {},
        "relations": []
    }
    
    # 抽取实体
    for entity_type in entity_types:
        entities = predictor(text, schema=[entity_type])
        if entities and len(entities) > 0:
            result["entities"][entity_type] = entities[0].get(entity_type, [])
    
    # 抽取关系
    for relation_type in relation_types:
        relations = predictor(text, schema=[relation_type])
        if relations and len(relations) > 0:
            result["relations"].extend(relations[0].get(relation_type, []))
    
    return result


def format_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """格式化输出结果"""
    formatted_result = {
        "text": result["text"],
        "spo_list": []
    }
    
    # 构建三元组列表
    entities = result["entities"]
    relations = result["relations"]
    
    # 这里可以根据实际需求构建更复杂的关系抽取逻辑
    # 目前简单返回实体和关系信息
    
    return formatted_result


def predict_fault_extraction():
    """主预测函数"""
    
    # 加载配置
    config = load_config(args.config_file)
    logger.info(f"Loaded config: {config}")
    
    # 初始化预测器
    entity_types = config.get("entity_types", ["部件单元", "性能表征", "故障状态", "检测工具"])
    schema = entity_types  # 可以根据需要调整schema
    
    logger.info(f"Initializing predictor with model: {args.model}")
    predictor = UIEPredictor(
        model=args.model,
        schema=schema,
        task_path=args.model_path,
        device=args.device,
        position_prob=args.position_prob,
        max_seq_len=args.max_seq_len
    )
    
    # 加载测试数据
    if args.test_file:
        logger.info(f"Loading test data from {args.test_file}")
        test_data = load_test_data(args.test_file)
    else:
        # 使用示例数据
        test_data = [
            {
                "ID": "AE0001",
                "text": "燃油泵的作用是将燃油加压输送到喷油器，当燃油泵损坏后，燃油将不能正常喷入发动机气缸，因此将影响发动机的正常运转，使得发动机出现加速不良的症状，情况严重时将导致发动机无法起动。"
            },
            {
                "ID": "BE0001", 
                "text": "减振器活塞与缸体发卡，工作阻力过大诊断排除。"
            }
        ]
    
    logger.info(f"Processing {len(test_data)} test samples")
    
    # 预测结果
    all_results = []
    
    for i, item in enumerate(test_data):
        text = item["text"]
        item_id = item.get("ID", f"sample_{i}")
        
        logger.info(f"Processing {item_id}: {text[:50]}...")
        
        # 抽取信息
        result = extract_fault_info(text, predictor, config)
        
        # 格式化输出
        formatted_result = format_output(result)
        formatted_result["ID"] = item_id
        
        all_results.append(formatted_result)
        
        # 打印结果
        if args.verbose:
            print(f"\n=== {item_id} ===")
            print(f"Text: {text}")
            print("Entities:")
            for entity_type, entities in result["entities"].items():
                if entities:
                    print(f"  {entity_type}: {[e['text'] for e in entities]}")
            print("Relations:")
            for relation in result["relations"]:
                print(f"  {relation['text']}")
            print()
    
    # 保存结果
    if args.output_file:
        logger.info(f"Saving results to {args.output_file}")
        with open(args.output_file, 'w', encoding='utf-8') as f:
            for result in all_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    # 打印统计信息
    total_entities = sum(len(result["entities"].get(et, [])) for result in all_results for et in entity_types)
    total_relations = sum(len(result["relations"]) for result in all_results)
    
    logger.info(f"Extraction completed!")
    logger.info(f"Total samples: {len(all_results)}")
    logger.info(f"Total entities: {total_entities}")
    logger.info(f"Total relations: {total_relations}")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(description="故障案例信息抽取预测")
    
    # 数据相关参数
    parser.add_argument("--test_file", type=str, help="测试数据文件路径")
    parser.add_argument("--config_file", type=str, required=True, help="配置文件路径")
    parser.add_argument("--output_file", type=str, help="输出文件路径")
    
    # 模型相关参数
    parser.add_argument("--model", type=str, default="uie-base", help="模型名称")
    parser.add_argument("--model_path", type=str, help="模型路径")
    parser.add_argument("--max_seq_len", type=int, default=512, help="最大序列长度")
    parser.add_argument("--position_prob", type=float, default=0.5, help="位置概率阈值")
    
    # 设备相关参数
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "gpu"], help="设备类型")
    
    # 输出相关参数
    parser.add_argument("--verbose", action="store_true", help="是否详细输出")
    
    global args
    args = parser.parse_args()
    
    # 开始预测
    results = predict_fault_extraction()
    
    # 如果没有指定输出文件，打印结果
    if not args.output_file and args.verbose:
        print("\n=== Final Results ===")
        for result in results:
            print(f"ID: {result['ID']}")
            print(f"Text: {result['text']}")
            print("---")


if __name__ == "__main__":
    main()