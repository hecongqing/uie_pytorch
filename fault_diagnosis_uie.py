#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业制造领域故障诊断信息抽取系统
基于UIE（Universal Information Extraction）实现
"""

import json
import argparse
from typing import List, Dict, Any
from uie_predictor import UIEPredictor


class FaultDiagnosisUIE:
    """
    工业制造领域故障诊断信息抽取器
    """
    
    def __init__(self, model_path: str = "uie-base", device: str = "cpu"):
        """
        初始化故障诊断抽取器
        
        Args:
            model_path: 模型路径，默认使用预训练的uie-base
            device: 运行设备，cpu或gpu
        """
        self.device = device
        self.predictor = UIEPredictor(
            model=model_path,
            device=device,
            position_prob=0.4,  # 降低阈值以提高召回率
            max_seq_len=512
        )
        
        # 定义抽取schema
        self.entity_schema = [
            "部件单元",      # 高端装备制造领域中的各种单元、零件、设备
            "性能表征",      # 部件的特征或者性能描述
            "故障状态",      # 系统或部件的故障状态描述，多为故障类型
            "检测工具"       # 用于检测某些故障的专用仪器
        ]
        
        # 定义关系抽取schema - 使用嵌套结构
        self.relation_schema = [
            {
                "部件故障": ["部件单元", "故障状态"]  # 部件单元 -> 故障状态
            },
            {
                "性能故障": ["性能表征", "故障状态"]  # 性能表征 -> 故障状态
            },
            {
                "检测工具": ["检测工具", "性能表征"]  # 检测工具 -> 性能表征
            },
            {
                "组成": ["部件单元", "部件单元"]      # 部件单元 -> 部件单元（组成关系）
            }
        ]
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        抽取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体抽取结果
        """
        self.predictor.set_schema(self.entity_schema)
        results = self.predictor(text)
        return results[0] if results else {}
    
    def extract_relations(self, text: str, entities: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        抽取关系
        
        Args:
            text: 输入文本
            entities: 已抽取的实体
            
        Returns:
            关系抽取结果
        """
        relations = {}
        
        # 为每种关系类型设置schema并抽取
        for relation_dict in self.relation_schema:
            for relation_name, entity_types in relation_dict.items():
                # 构建关系抽取的schema
                if len(entity_types) == 2:
                    subject_type, object_type = entity_types
                    
                    # 对于每个主体实体，寻找与之相关的客体实体
                    if subject_type in entities and object_type in entities:
                        subjects = entities[subject_type]
                        objects = entities[object_type]
                        
                        # 使用关系模式进行抽取
                        relation_schema = {relation_name: [subject_type, object_type]}
                        self.predictor.set_schema([relation_schema])
                        relation_results = self.predictor(text)
                        
                        if relation_results and relation_results[0]:
                            if relation_name not in relations:
                                relations[relation_name] = []
                            relations[relation_name].extend(relation_results[0].get(relation_name, []))
        
        return relations
    
    def extract_comprehensive(self, text: str) -> Dict[str, Any]:
        """
        综合抽取实体和关系
        
        Args:
            text: 输入文本
            
        Returns:
            完整的抽取结果
        """
        # 首先抽取实体
        entities = self.extract_entities(text)
        
        # 然后基于实体抽取关系
        relations = self.extract_relations(text, entities)
        
        return {
            "text": text,
            "entities": entities,
            "relations": relations
        }
    
    def extract_with_spo_format(self, text: str) -> List[Dict]:
        """
        使用SPO三元组格式进行抽取，模拟训练数据格式
        
        Args:
            text: 输入文本
            
        Returns:
            SPO三元组列表
        """
        spo_list = []
        
        # 首先抽取所有实体
        entities = self.extract_entities(text)
        
        # 针对每种关系类型进行抽取
        relation_mappings = {
            "部件故障": ("部件单元", "故障状态"),
            "性能故障": ("性能表征", "故障状态"),
            "检测工具": ("检测工具", "性能表征"),
            "组成": ("部件单元", "部件单元")
        }
        
        for relation_name, (subject_type, object_type) in relation_mappings.items():
            if subject_type in entities and object_type in entities:
                # 使用简化的关系抽取方法
                for subject in entities[subject_type]:
                    for obj in entities[object_type]:
                        # 检查文本中是否存在这种关系的语义线索
                        if self._check_relation_clues(text, subject["text"], obj["text"], relation_name):
                            spo_list.append({
                                "h": {
                                    "name": subject["text"],
                                    "pos": [subject["start"], subject["end"]]
                                },
                                "t": {
                                    "name": obj["text"],
                                    "pos": [obj["start"], obj["end"]]
                                },
                                "relation": relation_name
                            })
        
        return spo_list
    
    def _check_relation_clues(self, text: str, subject: str, obj: str, relation: str) -> bool:
        """
        检查文本中是否存在关系的语义线索
        
        Args:
            text: 原文本
            subject: 主体实体
            obj: 客体实体
            relation: 关系类型
            
        Returns:
            是否存在关系
        """
        # 简化的关系判断逻辑，实际应用中可以更复杂
        subject_pos = text.find(subject)
        obj_pos = text.find(obj)
        
        if subject_pos == -1 or obj_pos == -1:
            return False
        
        # 检查实体间的距离
        distance = abs(subject_pos - obj_pos)
        
        # 根据关系类型定义不同的判断规则
        if relation == "部件故障":
            # 部件和故障状态通常在附近出现
            return distance < 50
        elif relation == "性能故障":
            # 性能表征和故障状态通常在附近出现
            return distance < 30
        elif relation == "检测工具":
            # 检测工具和性能表征的关系
            keywords = ["检测", "测试", "测量", "监测"]
            nearby_text = text[max(0, min(subject_pos, obj_pos)-20):max(subject_pos, obj_pos)+len(max(subject, obj))+20]
            return any(keyword in nearby_text for keyword in keywords)
        elif relation == "组成":
            # 组成关系的判断
            keywords = ["组成", "包含", "由", "的", "中的"]
            nearby_text = text[max(0, min(subject_pos, obj_pos)-10):max(subject_pos, obj_pos)+len(max(subject, obj))+10]
            return any(keyword in nearby_text for keyword in keywords)
        
        return False


def process_single_text(extractor: FaultDiagnosisUIE, text: str, output_format: str = "comprehensive"):
    """
    处理单个文本
    
    Args:
        extractor: 抽取器实例
        text: 输入文本
        output_format: 输出格式，可选 "comprehensive", "spo", "entities", "relations"
    """
    if output_format == "comprehensive":
        return extractor.extract_comprehensive(text)
    elif output_format == "spo":
        return extractor.extract_with_spo_format(text)
    elif output_format == "entities":
        return extractor.extract_entities(text)
    elif output_format == "relations":
        entities = extractor.extract_entities(text)
        return extractor.extract_relations(text, entities)
    else:
        raise ValueError(f"不支持的输出格式: {output_format}")


def process_test_data(input_file: str, output_file: str, model_path: str = "uie-base", device: str = "cpu"):
    """
    处理测试数据文件
    
    Args:
        input_file: 输入文件路径（JSON格式）
        output_file: 输出文件路径
        model_path: 模型路径
        device: 运行设备
    """
    extractor = FaultDiagnosisUIE(model_path, device)
    
    results = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            data = json.loads(line)
            text = data["text"]
            
            # 抽取信息
            extracted_result = extractor.extract_with_spo_format(text)
            
            # 构建输出格式
            result = {
                "ID": data["ID"],
                "text": text,
                "spo_list": extracted_result
            }
            
            results.append(result)
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print(f"处理完成，结果保存到: {output_file}")


def demo():
    """
    演示功能
    """
    # 测试文本
    test_cases = [
        "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。",
        "燃油泵的作用是将燃油加压输送到喷油器，当燃油泵损坏后，燃油将不能正常喷入发动机气缸，因此将影响发动机的正常运转，使得发动机出现加速不良的症状，情况严重时将导致发动机无法起动。",
        "减振器活塞与缸体发卡，工作阻力过大诊断排除。"
    ]
    
    extractor = FaultDiagnosisUIE()
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i} ===")
        print(f"原文: {text}")
        
        # 抽取实体
        entities = extractor.extract_entities(text)
        print(f"\n实体抽取结果:")
        for entity_type, entity_list in entities.items():
            print(f"  {entity_type}: {[e['text'] for e in entity_list]}")
        
        # 抽取SPO三元组
        spo_list = extractor.extract_with_spo_format(text)
        print(f"\nSPO三元组:")
        for spo in spo_list:
            print(f"  ({spo['h']['name']}, {spo['relation']}, {spo['t']['name']})")


def main():
    parser = argparse.ArgumentParser(description="工业制造领域故障诊断信息抽取")
    parser.add_argument("--mode", choices=["demo", "process", "interactive"], 
                       default="demo", help="运行模式")
    parser.add_argument("--input_file", type=str, help="输入文件路径")
    parser.add_argument("--output_file", type=str, help="输出文件路径")
    parser.add_argument("--model_path", type=str, default="uie-base", help="模型路径")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu", help="运行设备")
    parser.add_argument("--output_format", choices=["comprehensive", "spo", "entities", "relations"],
                       default="spo", help="输出格式")
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        demo()
    elif args.mode == "process":
        if not args.input_file or not args.output_file:
            print("处理模式需要指定输入和输出文件")
            return
        process_test_data(args.input_file, args.output_file, args.model_path, args.device)
    elif args.mode == "interactive":
        extractor = FaultDiagnosisUIE(args.model_path, args.device)
        print("交互式故障诊断信息抽取模式（输入'quit'退出）")
        while True:
            text = input("\n请输入故障文本: ").strip()
            if text.lower() == 'quit':
                break
            if text:
                result = process_single_text(extractor, text, args.output_format)
                print(f"\n抽取结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()