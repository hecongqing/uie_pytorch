#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级工业制造领域故障案例信息抽取
使用UIE模型进行实体和关系抽取，针对关系抽取进行优化

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
import re
from typing import List, Dict, Any, Optional, Tuple
from pprint import pprint

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uie_predictor import UIEPredictor


class AdvancedFaultExtractor:
    """高级工业制造领域故障案例信息抽取器"""
    
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
        
        # 定义关系抽取的schema（UIE关系抽取需要特殊格式）
        self.relation_schemas = [
            {
                '部件单元': {
                    '故障状态': '部件故障'
                }
            },
            {
                '性能表征': {
                    '故障状态': '性能故障'
                }
            },
            {
                '检测工具': {
                    '性能表征': '检测工具'
                }
            },
            {
                '部件单元': {
                    '部件单元': '组成关系'
                }
            }
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
        
        # 关系抽取预测器（使用嵌套schema）
        self.relation_predictor = UIEPredictor(
            model=self.model_name,
            schema=self.relation_schemas,
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
                if isinstance(item, dict) and 'text' in item:
                    # 处理UIE关系抽取的结果格式
                    spo = self._parse_relation_item(item, relation_type, text)
                    if spo:
                        spo_list.append(spo)
        
        return spo_list
    
    def _parse_relation_item(self, item: Dict, relation_type: str, text: str) -> Optional[Dict]:
        """
        解析关系抽取结果项
        
        Args:
            item: 关系抽取结果项
            relation_type: 关系类型
            text: 原始文本
            
        Returns:
            SPO三元组字典
        """
        try:
            # UIE关系抽取结果可能包含主体和客体信息
            if 'text' in item and 'start' in item and 'end' in item:
                # 简单处理：假设text包含主体和客体信息
                text_content = item['text']
                
                # 根据关系类型确定主体和客体的实体类型
                subject_type, object_type = self._get_entity_types_for_relation(relation_type)
                
                # 尝试从文本中提取主体和客体
                subject, object_entity = self._extract_subject_object(text_content, subject_type, object_type)
                
                if subject and object_entity:
                    spo = {
                        'h': {
                            'name': subject,
                            'pos': [item.get('start', 0), item.get('end', 0)]
                        },
                        't': {
                            'name': object_entity,
                            'pos': [item.get('start', 0), item.get('end', 0)]
                        },
                        'relation': relation_type
                    }
                    return spo
            
            return None
        except Exception as e:
            print(f"解析关系项出错: {e}")
            return None
    
    def _get_entity_types_for_relation(self, relation_type: str) -> Tuple[str, str]:
        """
        根据关系类型获取主体和客体的实体类型
        
        Args:
            relation_type: 关系类型
            
        Returns:
            (主体实体类型, 客体实体类型)
        """
        relation_mapping = {
            '部件故障': ('部件单元', '故障状态'),
            '性能故障': ('性能表征', '故障状态'),
            '检测工具': ('检测工具', '性能表征'),
            '组成关系': ('部件单元', '部件单元')
        }
        
        return relation_mapping.get(relation_type, ('', ''))
    
    def _extract_subject_object(self, text: str, subject_type: str, object_type: str) -> Tuple[str, str]:
        """
        从文本中提取主体和客体
        
        Args:
            text: 文本内容
            subject_type: 主体实体类型
            object_type: 客体实体类型
            
        Returns:
            (主体, 客体)
        """
        # 这里使用简单的规则来提取主体和客体
        # 在实际应用中，可能需要更复杂的NLP技术
        
        # 对于部件故障关系，通常格式为"部件+故障状态"
        if subject_type == '部件单元' and object_type == '故障状态':
            # 尝试匹配常见的部件故障模式
            patterns = [
                r'([^，。；]+?)(抖动|损坏|断裂|变形|卡滞|松旷|漏油)',
                r'([^，。；]+?)(出现|发生|导致)([^，。；]*?)(故障|问题|异常)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(2).strip()
        
        # 对于性能故障关系
        elif subject_type == '性能表征' and object_type == '故障状态':
            patterns = [
                r'([^，。；]+?)(变低|变高|异常|不稳定|下降|上升)',
                r'([^，。；]+?)(出现|发生)([^，。；]*?)(异常|问题)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(2).strip()
        
        # 对于检测工具关系
        elif subject_type == '检测工具' and object_type == '性能表征':
            patterns = [
                r'([^，。；]+?)(检测|测量|监控)([^，。；]*?)([^，。；]+)',
                r'([^，。；]+?)(用于|用来)([^，。；]*?)([^，。；]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(4).strip()
        
        # 对于组成关系
        elif subject_type == '部件单元' and object_type == '部件单元':
            patterns = [
                r'([^，。；]+?)(包含|包括|由)([^，。；]*?)([^，。；]+)',
                r'([^，。；]+?)(和|与)([^，。；]+)',
                r'([^，。；]+?)(连接|连接着)([^，。；]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(3).strip()
        
        return '', ''
    
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
    
    def evaluate_with_gold_standard(self, prediction_file: str, gold_file: str):
        """
        与标准答案进行对比评估
        
        Args:
            prediction_file: 预测结果文件
            gold_file: 标准答案文件
        """
        print(f"正在评估预测结果...")
        
        # 读取预测结果
        predictions = {}
        with open(prediction_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                predictions[data['ID']] = data
        
        # 读取标准答案
        gold_standards = {}
        with open(gold_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                gold_standards[data['ID']] = data
        
        # 计算评估指标
        total_samples = len(gold_standards)
        correct_entities = 0
        correct_relations = 0
        total_entities = 0
        total_relations = 0
        
        for sample_id, gold_data in gold_standards.items():
            if sample_id in predictions:
                pred_data = predictions[sample_id]
                
                # 评估实体抽取
                gold_entities = set()
                pred_entities = set()
                
                # 处理标准答案中的实体
                for spo in gold_data.get('spo_list', []):
                    gold_entities.add((spo['h']['name'], spo['h']['pos']))
                    gold_entities.add((spo['t']['name'], spo['t']['pos']))
                
                # 处理预测结果中的实体
                for entity_type, entities in pred_data.get('entities', {}).items():
                    for entity in entities:
                        pred_entities.add((entity['text'], [entity['start'], entity['end']]))
                
                # 计算实体准确率
                correct_entities += len(gold_entities.intersection(pred_entities))
                total_entities += len(gold_entities)
                
                # 评估关系抽取
                gold_relations = set()
                pred_relations = set()
                
                # 处理标准答案中的关系
                for spo in gold_data.get('spo_list', []):
                    gold_relations.add((spo['h']['name'], spo['relation'], spo['t']['name']))
                
                # 处理预测结果中的关系
                for spo in pred_data.get('spo_list', []):
                    pred_relations.add((spo['h']['name'], spo['relation'], spo['t']['name']))
                
                # 计算关系准确率
                correct_relations += len(gold_relations.intersection(pred_relations))
                total_relations += len(gold_relations)
        
        # 计算最终指标
        entity_accuracy = correct_entities / total_entities if total_entities > 0 else 0
        relation_accuracy = correct_relations / total_relations if total_relations > 0 else 0
        
        print(f"评估结果:")
        print(f"总样本数: {total_samples}")
        print(f"实体抽取准确率: {entity_accuracy:.4f} ({correct_entities}/{total_entities})")
        print(f"关系抽取准确率: {relation_accuracy:.4f} ({correct_relations}/{total_relations})")
        
        return {
            'entity_accuracy': entity_accuracy,
            'relation_accuracy': relation_accuracy,
            'total_samples': total_samples
        }


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
    extractor = AdvancedFaultExtractor(model_name='uie-base', device='cpu')
    
    # 处理示例文本
    for example in example_texts:
        print(f"\n{'='*60}")
        extractor.process_single_text(example['text'], example['ID'])
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()