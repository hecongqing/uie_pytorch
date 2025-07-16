#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障诊断数据处理脚本
将原始故障案例数据转换为UIE训练格式
"""

import json
import argparse
import os
from typing import List, Dict, Any


class FaultDataProcessor:
    """
    故障诊断数据处理器
    """
    
    def __init__(self):
        # 实体类型映射
        self.entity_types = {
            "部件单元": "部件单元",
            "性能表征": "性能表征", 
            "故障状态": "故障状态",
            "检测工具": "检测工具"
        }
        
        # 关系类型映射
        self.relation_types = {
            "部件故障": "部件故障",
            "性能故障": "性能故障", 
            "检测工具": "检测工具",
            "组成": "组成"
        }
    
    def load_original_data(self, file_path: str) -> List[Dict]:
        """
        加载原始故障案例数据
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            故障案例数据列表
        """
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    data_list.append(data)
        return data_list
    
    def extract_entities_from_spo(self, spo_list: List[Dict]) -> Dict[str, List[Dict]]:
        """
        从SPO列表中提取实体信息
        
        Args:
            spo_list: SPO三元组列表
            
        Returns:
            实体字典
        """
        entities = {}
        
        for spo in spo_list:
            h_entity = spo["h"]
            t_entity = spo["t"]
            relation = spo["relation"]
            
            # 根据关系类型推断实体类型
            if relation == "部件故障":
                h_type = "部件单元"
                t_type = "故障状态"
            elif relation == "性能故障":
                h_type = "性能表征"
                t_type = "故障状态"
            elif relation == "检测工具":
                h_type = "检测工具"
                t_type = "性能表征"
            elif relation == "组成":
                h_type = "部件单元"
                t_type = "部件单元"
            else:
                continue
            
            # 添加头实体
            if h_type not in entities:
                entities[h_type] = []
            entities[h_type].append({
                "text": h_entity["name"],
                "start": h_entity["pos"][0],
                "end": h_entity["pos"][1]
            })
            
            # 添加尾实体
            if t_type not in entities:
                entities[t_type] = []
            entities[t_type].append({
                "text": t_entity["name"],
                "start": t_entity["pos"][0],
                "end": t_entity["pos"][1]
            })
        
        # 去重
        for entity_type in entities:
            unique_entities = []
            seen = set()
            for entity in entities[entity_type]:
                key = (entity["text"], entity["start"], entity["end"])
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
            entities[entity_type] = unique_entities
        
        return entities
    
    def convert_to_uie_format(self, original_data: List[Dict], output_type: str = "entity") -> List[Dict]:
        """
        将原始数据转换为UIE训练格式
        
        Args:
            original_data: 原始故障案例数据
            output_type: 输出类型，"entity"表示实体抽取格式，"relation"表示关系抽取格式
            
        Returns:
            UIE格式的训练数据
        """
        uie_data = []
        
        for data in original_data:
            text = data["text"]
            spo_list = data.get("spo_list", [])
            
            if output_type == "entity":
                # 生成实体抽取的训练数据
                entities = self.extract_entities_from_spo(spo_list)
                
                for entity_type, entity_list in entities.items():
                    if entity_list:
                        uie_sample = {
                            "content": text,
                            "result_list": [{
                                "text": entity["text"],
                                "start": entity["start"],
                                "end": entity["end"]
                            } for entity in entity_list],
                            "prompt": entity_type
                        }
                        uie_data.append(uie_sample)
                
                # 添加负样本（没有对应实体类型的样本）
                all_entity_types = set(self.entity_types.keys())
                existing_types = set(entities.keys())
                for missing_type in all_entity_types - existing_types:
                    uie_sample = {
                        "content": text,
                        "result_list": [],
                        "prompt": missing_type
                    }
                    uie_data.append(uie_sample)
            
            elif output_type == "relation":
                # 生成关系抽取的训练数据
                entities = self.extract_entities_from_spo(spo_list)
                
                # 为每种关系类型生成训练样本
                for relation_name in self.relation_types.keys():
                    relation_results = []
                    
                    # 查找属于当前关系的SPO三元组
                    for spo in spo_list:
                        if spo["relation"] == relation_name:
                            h_entity = spo["h"]
                            t_entity = spo["t"]
                            
                            relation_result = {
                                h_entity["name"]: [{
                                    "text": t_entity["name"],
                                    "start": t_entity["pos"][0],
                                    "end": t_entity["pos"][1]
                                }]
                            }
                            relation_results.append(relation_result)
                    
                    # 构建关系抽取样本
                    if relation_results:
                        # 合并相同头实体的结果
                        merged_results = {}
                        for result in relation_results:
                            for head_entity, tail_entities in result.items():
                                if head_entity not in merged_results:
                                    merged_results[head_entity] = []
                                merged_results[head_entity].extend(tail_entities)
                        
                        uie_sample = {
                            "content": text,
                            "result_list": [merged_results],
                            "prompt": relation_name
                        }
                        uie_data.append(uie_sample)
                    else:
                        # 添加负样本
                        uie_sample = {
                            "content": text,
                            "result_list": [],
                            "prompt": relation_name
                        }
                        uie_data.append(uie_sample)
        
        return uie_data
    
    def save_uie_data(self, uie_data: List[Dict], output_file: str):
        """
        保存UIE格式的训练数据
        
        Args:
            uie_data: UIE格式数据
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in uie_data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        print(f"UIE训练数据已保存到: {output_file}")
    
    def split_train_dev(self, data: List[Dict], train_ratio: float = 0.8) -> tuple:
        """
        划分训练集和验证集
        
        Args:
            data: 数据列表
            train_ratio: 训练集比例
            
        Returns:
            (训练集, 验证集)
        """
        split_idx = int(len(data) * train_ratio)
        train_data = data[:split_idx]
        dev_data = data[split_idx:]
        return train_data, dev_data
    
    def create_doccano_format(self, original_data: List[Dict]) -> List[Dict]:
        """
        创建Doccano标注格式数据
        
        Args:
            original_data: 原始故障案例数据
            
        Returns:
            Doccano格式数据
        """
        doccano_data = []
        
        for i, data in enumerate(original_data):
            text = data["text"]
            spo_list = data.get("spo_list", [])
            
            # 提取实体标注
            entities = []
            entity_id = 0
            entity_map = {}  # 用于存储实体到ID的映射
            
            for spo in spo_list:
                h_entity = spo["h"]
                t_entity = spo["t"]
                relation = spo["relation"]
                
                # 确定实体类型
                if relation == "部件故障":
                    h_type = "部件单元"
                    t_type = "故障状态"
                elif relation == "性能故障":
                    h_type = "性能表征"
                    t_type = "故障状态"
                elif relation == "检测工具":
                    h_type = "检测工具"
                    t_type = "性能表征"
                elif relation == "组成":
                    h_type = "部件单元"
                    t_type = "部件单元"
                else:
                    continue
                
                # 添加头实体
                h_key = (h_entity["name"], h_entity["pos"][0], h_entity["pos"][1])
                if h_key not in entity_map:
                    entities.append([
                        h_entity["pos"][0],
                        h_entity["pos"][1],
                        h_type
                    ])
                    entity_map[h_key] = entity_id
                    entity_id += 1
                
                # 添加尾实体
                t_key = (t_entity["name"], t_entity["pos"][0], t_entity["pos"][1])
                if t_key not in entity_map:
                    entities.append([
                        t_entity["pos"][0],
                        t_entity["pos"][1],
                        t_type
                    ])
                    entity_map[t_key] = entity_id
                    entity_id += 1
            
            # 构建关系标注
            relations = []
            for spo in spo_list:
                h_entity = spo["h"]
                t_entity = spo["t"]
                relation = spo["relation"]
                
                h_key = (h_entity["name"], h_entity["pos"][0], h_entity["pos"][1])
                t_key = (t_entity["name"], t_entity["pos"][0], t_entity["pos"][1])
                
                if h_key in entity_map and t_key in entity_map:
                    relations.append([
                        entity_map[h_key],
                        entity_map[t_key],
                        relation
                    ])
            
            doccano_sample = {
                "id": i,
                "text": text,
                "entities": entities,
                "relations": relations
            }
            doccano_data.append(doccano_sample)
        
        return doccano_data


def main():
    parser = argparse.ArgumentParser(description="故障诊断数据处理工具")
    parser.add_argument("--input_file", type=str, required=True, help="输入文件路径")
    parser.add_argument("--output_dir", type=str, default="./processed_data", help="输出目录")
    parser.add_argument("--format", choices=["uie", "doccano", "both"], default="uie", 
                       help="输出格式")
    parser.add_argument("--split_ratio", type=float, default=0.8, help="训练集比例")
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    processor = FaultDataProcessor()
    
    # 加载原始数据
    print(f"加载数据从: {args.input_file}")
    original_data = processor.load_original_data(args.input_file)
    print(f"加载了 {len(original_data)} 条数据")
    
    if args.format in ["uie", "both"]:
        # 转换为UIE格式
        print("转换为UIE实体抽取格式...")
        entity_data = processor.convert_to_uie_format(original_data, "entity")
        train_entity, dev_entity = processor.split_train_dev(entity_data, args.split_ratio)
        
        processor.save_uie_data(train_entity, os.path.join(args.output_dir, "train_entity.txt"))
        processor.save_uie_data(dev_entity, os.path.join(args.output_dir, "dev_entity.txt"))
        
        print("转换为UIE关系抽取格式...")
        relation_data = processor.convert_to_uie_format(original_data, "relation")
        train_relation, dev_relation = processor.split_train_dev(relation_data, args.split_ratio)
        
        processor.save_uie_data(train_relation, os.path.join(args.output_dir, "train_relation.txt"))
        processor.save_uie_data(dev_relation, os.path.join(args.output_dir, "dev_relation.txt"))
    
    if args.format in ["doccano", "both"]:
        # 转换为Doccano格式
        print("转换为Doccano格式...")
        doccano_data = processor.create_doccano_format(original_data)
        
        doccano_file = os.path.join(args.output_dir, "doccano_format.jsonl")
        with open(doccano_file, 'w', encoding='utf-8') as f:
            for sample in doccano_data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        print(f"Doccano格式数据已保存到: {doccano_file}")
    
    print("数据处理完成！")


if __name__ == "__main__":
    main()