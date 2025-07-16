#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业制造领域故障案例信息抽取演示
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
import re
from typing import List, Dict, Any, Optional, Tuple
from pprint import pprint

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uie_predictor import UIEPredictor


class FaultExtractionDemo:
    """工业故障信息抽取演示类"""
    
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
        
        # 首先从实体抽取结果中构建一些基本的三元组
        spo_list.extend(self._build_spo_from_entities(entities, text))
        
        # 然后处理关系抽取结果
        spo_list.extend(self._build_spo_from_relations(relations, text))
        
        return spo_list
    
    def _build_spo_from_entities(self, entities: Dict, text: str) -> List[Dict]:
        """
        从实体抽取结果构建SPO三元组
        
        Args:
            entities: 实体抽取结果
            text: 原始文本
            
        Returns:
            SPO三元组列表
        """
        spo_list = []
        
        # 获取所有实体及其位置
        entity_positions = {}
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if 'text' in entity and 'start' in entity and 'end' in entity:
                    entity_text = entity['text']
                    start_pos = entity['start']
                    end_pos = entity['end']
                    
                    if entity_type not in entity_positions:
                        entity_positions[entity_type] = []
                    entity_positions[entity_type].append({
                        'text': entity_text,
                        'start': start_pos,
                        'end': end_pos
                    })
        
        # 尝试构建关系
        # 部件故障：部件单元 -> 故障状态
        if '部件单元' in entity_positions and '故障状态' in entity_positions:
            spo_list.extend(self._build_component_fault_relations(
                entity_positions['部件单元'], 
                entity_positions['故障状态'], 
                text
            ))
        
        # 性能故障：性能表征 -> 故障状态
        if '性能表征' in entity_positions and '故障状态' in entity_positions:
            spo_list.extend(self._build_performance_fault_relations(
                entity_positions['性能表征'], 
                entity_positions['故障状态'], 
                text
            ))
        
        # 检测工具：检测工具 -> 性能表征
        if '检测工具' in entity_positions and '性能表征' in entity_positions:
            spo_list.extend(self._build_detection_tool_relations(
                entity_positions['检测工具'], 
                entity_positions['性能表征'], 
                text
            ))
        
        # 组成关系：部件单元 -> 部件单元
        if '部件单元' in entity_positions and len(entity_positions['部件单元']) > 1:
            spo_list.extend(self._build_composition_relations(
                entity_positions['部件单元'], 
                text
            ))
        
        return spo_list
    
    def _build_component_fault_relations(self, components: List[Dict], faults: List[Dict], text: str) -> List[Dict]:
        """构建部件故障关系"""
        spo_list = []
        
        for component in components:
            for fault in faults:
                # 检查部件和故障是否在文本中相邻或相关
                if self._are_entities_related(component, fault, text, max_distance=50):
                    spo = {
                        'h': {
                            'name': component['text'],
                            'pos': [component['start'], component['end']]
                        },
                        't': {
                            'name': fault['text'],
                            'pos': [fault['start'], fault['end']]
                        },
                        'relation': '部件故障'
                    }
                    spo_list.append(spo)
        
        return spo_list
    
    def _build_performance_fault_relations(self, performances: List[Dict], faults: List[Dict], text: str) -> List[Dict]:
        """构建性能故障关系"""
        spo_list = []
        
        for performance in performances:
            for fault in faults:
                if self._are_entities_related(performance, fault, text, max_distance=50):
                    spo = {
                        'h': {
                            'name': performance['text'],
                            'pos': [performance['start'], performance['end']]
                        },
                        't': {
                            'name': fault['text'],
                            'pos': [fault['start'], fault['end']]
                        },
                        'relation': '性能故障'
                    }
                    spo_list.append(spo)
        
        return spo_list
    
    def _build_detection_tool_relations(self, tools: List[Dict], performances: List[Dict], text: str) -> List[Dict]:
        """构建检测工具关系"""
        spo_list = []
        
        for tool in tools:
            for performance in performances:
                if self._are_entities_related(tool, performance, text, max_distance=50):
                    spo = {
                        'h': {
                            'name': tool['text'],
                            'pos': [tool['start'], tool['end']]
                        },
                        't': {
                            'name': performance['text'],
                            'pos': [performance['start'], performance['end']]
                        },
                        'relation': '检测工具'
                    }
                    spo_list.append(spo)
        
        return spo_list
    
    def _build_composition_relations(self, components: List[Dict], text: str) -> List[Dict]:
        """构建组成关系"""
        spo_list = []
        
        # 查找包含、包括、由等表示组成关系的词汇
        composition_keywords = ['包含', '包括', '由', '组成', '构成', '连接', '连接着']
        
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i != j:  # 不与自己建立关系
                    # 检查两个部件之间是否有组成关系的关键词
                    if self._has_composition_keyword(comp1, comp2, text, composition_keywords):
                        spo = {
                            'h': {
                                'name': comp1['text'],
                                'pos': [comp1['start'], comp1['end']]
                            },
                            't': {
                                'name': comp2['text'],
                                'pos': [comp2['start'], comp2['end']]
                            },
                            'relation': '组成关系'
                        }
                        spo_list.append(spo)
        
        return spo_list
    
    def _are_entities_related(self, entity1: Dict, entity2: Dict, text: str, max_distance: int = 50) -> bool:
        """
        检查两个实体是否相关（在文本中距离较近）
        
        Args:
            entity1: 第一个实体
            entity2: 第二个实体
            text: 原始文本
            max_distance: 最大距离
            
        Returns:
            是否相关
        """
        # 计算两个实体之间的距离
        distance = abs(entity1['start'] - entity2['end'])
        if distance <= max_distance:
            return True
        
        # 检查是否在同一个句子中
        sentence_pattern = r'[^。！？]*[。！？]'
        sentences = re.findall(sentence_pattern, text)
        
        for sentence in sentences:
            if entity1['text'] in sentence and entity2['text'] in sentence:
                return True
        
        return False
    
    def _has_composition_keyword(self, entity1: Dict, entity2: Dict, text: str, keywords: List[str]) -> bool:
        """
        检查两个实体之间是否有组成关系的关键词
        
        Args:
            entity1: 第一个实体
            entity2: 第二个实体
            text: 原始文本
            keywords: 组成关系关键词
            
        Returns:
            是否有组成关系
        """
        # 获取两个实体之间的文本
        start = min(entity1['end'], entity2['end'])
        end = max(entity1['start'], entity2['start'])
        
        if start < end:
            between_text = text[start:end]
        else:
            # 如果实体重叠，检查周围的文本
            context_start = max(0, min(entity1['start'], entity2['start']) - 20)
            context_end = min(len(text), max(entity1['end'], entity2['end']) + 20)
            between_text = text[context_start:context_end]
        
        # 检查是否包含组成关系关键词
        for keyword in keywords:
            if keyword in between_text:
                return True
        
        return False
    
    def _build_spo_from_relations(self, relations: Dict, text: str) -> List[Dict]:
        """
        从关系抽取结果构建SPO三元组
        
        Args:
            relations: 关系抽取结果
            text: 原始文本
            
        Returns:
            SPO三元组列表
        """
        spo_list = []
        
        # 处理UIE关系抽取的结果
        for relation_type, relation_items in relations.items():
            for item in relation_items:
                if isinstance(item, dict) and 'text' in item:
                    # 这里需要根据UIE关系抽取的具体结果格式来处理
                    # 由于UIE的关系抽取结果可能比较复杂，这里提供一个基本框架
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
            # 这里需要根据UIE关系抽取的具体结果格式来实现
            # 由于UIE的关系抽取结果格式可能比较复杂，这里提供一个基本实现
            if 'text' in item and 'start' in item and 'end' in item:
                # 简单处理：假设text包含关系信息
                text_content = item['text']
                
                # 尝试从文本中提取主体和客体
                subject, object_entity = self._extract_subject_object_from_text(text_content, relation_type)
                
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
    
    def _extract_subject_object_from_text(self, text: str, relation_type: str) -> Tuple[str, str]:
        """
        从文本中提取主体和客体
        
        Args:
            text: 文本内容
            relation_type: 关系类型
            
        Returns:
            (主体, 客体)
        """
        # 这里使用简单的规则来提取主体和客体
        # 在实际应用中，可能需要更复杂的NLP技术
        
        # 对于部件故障关系
        if relation_type == '部件故障':
            patterns = [
                r'([^，。；]+?)(抖动|损坏|断裂|变形|卡滞|松旷|漏油)',
                r'([^，。；]+?)(出现|发生|导致)([^，。；]*?)(故障|问题|异常)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(2).strip()
        
        # 对于性能故障关系
        elif relation_type == '性能故障':
            patterns = [
                r'([^，。；]+?)(变低|变高|异常|不稳定|下降|上升)',
                r'([^，。；]+?)(出现|发生)([^，。；]*?)(异常|问题)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(2).strip()
        
        # 对于检测工具关系
        elif relation_type == '检测工具':
            patterns = [
                r'([^，。；]+?)(检测|测量|监控)([^，。；]*?)([^，。；]+)',
                r'([^，。；]+?)(用于|用来)([^，。；]*?)([^，。；]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip(), match.group(4).strip()
        
        # 对于组成关系
        elif relation_type == '组成关系':
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
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 处理示例文本
    for example in example_texts:
        print(f"\n{'='*60}")
        extractor.process_single_text(example['text'], example['ID'])
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()