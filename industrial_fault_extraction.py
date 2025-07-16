#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业制造领域故障案例信息抽取
使用UIE模型进行实体和关系抽取

实体类型：
- 部件单元：高端装备制造领域中的各种单元、零件、设备
- 性能表征：部件的特征或者性能描述
- 故障状态：系统或部件的故障状态描述，多为故障类型
- 检测工具：用于检测某些故障的专用仪器

关系类型：
- 部件故障：部件单元 -> 故障状态
- 性能故障：性能表征 -> 故障状态
- 检测工具：检测工具 -> 性能表征
- 组成关系：部件单元 -> 部件单元
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
from pprint import pprint

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uie_predictor import UIEPredictor


class IndustrialFaultExtractor:
    """工业制造领域故障案例信息抽取器"""
    
    def __init__(self, model_name: str = 'uie-base', device: str = 'cpu'):
        """
        初始化抽取器
        
        Args:
            model_name: UIE模型名称
            device: 设备类型 ('cpu' 或 'gpu')
        """
        self.model_name = model_name
        self.device = device
        
        # 定义实体类型
        self.entity_types = [
            '部件单元',      # 高端装备制造领域中的各种单元、零件、设备
            '性能表征',      # 部件的特征或者性能描述
            '故障状态',      # 系统或部件的故障状态描述，多为故障类型
            '检测工具'       # 用于检测某些故障的专用仪器
        ]
        
        # 定义关系类型
        self.relation_types = [
            '部件故障',      # 部件单元 -> 故障状态
            '性能故障',      # 性能表征 -> 故障状态
            '检测工具',      # 检测工具 -> 性能表征
            '组成关系'       # 部件单元 -> 部件单元
        ]
        
        # 初始化UIE预测器
        self._init_predictors()
    
    def _init_predictors(self):
        """初始化UIE预测器"""
        print("正在初始化UIE模型...")
        
        # 实体抽取预测器
        self.entity_predictor = UIEPredictor(
            model=self.model_name,
            schema=self.entity_types,
            device=self.device
        )
        
        # 关系抽取预测器
        self.relation_predictor = UIEPredictor(
            model=self.model_name,
            schema=self.relation_types,
            device=self.device
        )
        
        print("UIE模型初始化完成！")
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        抽取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体抽取结果
        """
        try:
            results = self.entity_predictor(text)
            return results[0] if results else {}
        except Exception as e:
            print(f"实体抽取出错: {e}")
            return {}
    
    def extract_relations(self, text: str) -> Dict[str, List[Dict]]:
        """
        抽取关系
        
        Args:
            text: 输入文本
            
        Returns:
            关系抽取结果
        """
        try:
            results = self.relation_predictor(text)
            return results[0] if results else {}
        except Exception as e:
            print(f"关系抽取出错: {e}")
            return {}
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        同时抽取实体和关系
        
        Args:
            text: 输入文本
            
        Returns:
            包含实体和关系的完整抽取结果
        """
        print(f"正在处理文本: {text[:50]}...")
        
        # 抽取实体
        entities = self.extract_entities(text)
        print("实体抽取结果:")
        pprint(entities)
        
        # 抽取关系
        relations = self.extract_relations(text)
        print("关系抽取结果:")
        pprint(relations)
        
        # 构建标准格式的结果
        result = {
            'text': text,
            'entities': entities,
            'relations': relations,
            'spo_list': self._build_spo_list(entities, relations, text)
        }
        
        return result
    
    def _build_spo_list(self, entities: Dict, relations: Dict, text: str) -> List[Dict]:
        """
        构建SPO三元组列表
        
        Args:
            entities: 实体抽取结果
            relations: 关系抽取结果
            text: 原始文本
            
        Returns:
            SPO三元组列表
        """
        spo_list = []
        
        # 处理关系抽取结果，构建三元组
        for relation_type, relation_items in relations.items():
            for item in relation_items:
                if 'text' in item and 'start' in item and 'end' in item:
                    # 这里需要根据关系类型来确定主体和客体
                    # 由于UIE的关系抽取结果可能包含主体和客体信息
                    # 我们需要进一步处理
                    spo = {
                        'h': {
                            'name': item.get('text', ''),
                            'pos': [item.get('start', 0), item.get('end', 0)]
                        },
                        't': {
                            'name': '',  # 需要根据具体关系类型确定
                            'pos': [0, 0]
                        },
                        'relation': relation_type
                    }
                    spo_list.append(spo)
        
        return spo_list
    
    def process_training_data(self, data_file: str, output_file: str):
        """
        处理训练数据文件
        
        Args:
            data_file: 训练数据文件路径
            output_file: 输出文件路径
        """
        print(f"正在处理训练数据文件: {data_file}")
        
        results = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    text = data.get('text', '')
                    sample_id = data.get('ID', f'LINE_{line_num}')
                    
                    if text:
                        result = self.extract_all(text)
                        result['ID'] = sample_id
                        results.append(result)
                        
                        print(f"处理完成样本 {sample_id}")
                        
                except json.JSONDecodeError as e:
                    print(f"第{line_num}行JSON解析错误: {e}")
                except Exception as e:
                    print(f"第{line_num}行处理错误: {e}")
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"处理完成，结果已保存到: {output_file}")
        print(f"共处理 {len(results)} 个样本")
    
    def process_single_text(self, text: str, sample_id: str = "SAMPLE_001"):
        """
        处理单个文本
        
        Args:
            text: 输入文本
            sample_id: 样本ID
        """
        print(f"正在处理样本 {sample_id}")
        print(f"文本内容: {text}")
        print("-" * 50)
        
        result = self.extract_all(text)
        result['ID'] = sample_id
        
        # 保存结果
        output_file = f"result_{sample_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_file}")
        return result


def main():
    """主函数"""
    # 示例文本
    example_texts = [
        {
            "ID": "AT0001",
            "text": "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。"
        },
        {
            "ID": "AE0001", 
            "text": "燃油泵的作用是将燃油加压输送到喷油器，当燃油泵损坏后，燃油将不能正常喷入发动机气缸，因此将影响发动机的正常运转，使得发动机出现加速不良的症状，情况严重时将导致发动机无法起动。"
        },
        {
            "ID": "BE0001",
            "text": "减振器活塞与缸体发卡，工作阻力过大诊断排除。"
        }
    ]
    
    # 初始化抽取器
    extractor = IndustrialFaultExtractor(model_name='uie-base', device='cpu')
    
    # 处理示例文本
    for example in example_texts:
        print(f"\n{'='*60}")
        extractor.process_single_text(example['text'], example['ID'])
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()