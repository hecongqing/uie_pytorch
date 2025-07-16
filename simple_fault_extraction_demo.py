#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的工业制造领域故障案例信息抽取演示
不依赖外部库，展示核心逻辑和算法
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pprint import pprint


class SimpleFaultExtractor:
    """简化的工业故障信息抽取器"""
    
    def __init__(self):
        """初始化抽取器"""
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
        
        # 实体词典（实际应用中可以从训练数据中学习）
        self.entity_dict = {
            '部件单元': [
                '发动机盖', '发动机盖锁', '发动机盖铰链', '燃油泵', '喷油器', 
                '发动机气缸', '发动机', '减振器', '活塞', '缸体', '换流变压器',
                '分离器', '断路器', '燃油', '车速', '液面', '压力', '转速', '温度'
            ],
            '性能表征': [
                '车速', '液面', '压力', '转速', '温度', '电流', '电压', '功率',
                '效率', '流量', '阻力', '振动', '噪声'
            ],
            '故障状态': [
                '抖动', '松旷', '损坏', '断裂', '变形', '卡滞', '漏油', '加速不良',
                '无法起动', '发卡', '阻力过大', '异常', '不稳定', '下降', '上升',
                '变低', '变高'
            ],
            '检测工具': [
                '零序互感器', '保护器', '漏电测试仪', '万用表', '示波器',
                '压力表', '温度计', '转速表', '振动仪'
            ]
        }
        
        # 关系模式（实际应用中可以从训练数据中学习）
        self.relation_patterns = {
            '部件故障': [
                r'([^，。；]+?)(抖动|损坏|断裂|变形|卡滞|松旷|漏油|加速不良|无法起动|发卡)',
                r'([^，。；]+?)(出现|发生|导致)([^，。；]*?)(故障|问题|异常)'
            ],
            '性能故障': [
                r'([^，。；]+?)(变低|变高|异常|不稳定|下降|上升|阻力过大)',
                r'([^，。；]+?)(出现|发生)([^，。；]*?)(异常|问题)'
            ],
            '检测工具': [
                r'([^，。；]+?)(检测|测量|监控)([^，。；]*?)([^，。；]+)',
                r'([^，。；]+?)(用于|用来)([^，。；]*?)([^，。；]+)'
            ],
            '组成关系': [
                r'([^，。；]+?)(包含|包括|由)([^，。；]*?)([^，。；]+)',
                r'([^，。；]+?)(和|与)([^，。；]+)',
                r'([^，。；]+?)(连接|连接着)([^，。；]+)'
            ]
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        抽取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体抽取结果
        """
        entities = {}
        
        for entity_type, entity_list in self.entity_dict.items():
            entities[entity_type] = []
            
            for entity in entity_list:
                # 查找实体在文本中的所有位置
                positions = []
                start = 0
                while True:
                    pos = text.find(entity, start)
                    if pos == -1:
                        break
                    positions.append((pos, pos + len(entity)))
                    start = pos + 1
                
                # 添加到结果中
                for start_pos, end_pos in positions:
                    entities[entity_type].append({
                        'text': entity,
                        'start': start_pos,
                        'end': end_pos,
                        'probability': 0.95  # 模拟概率
                    })
        
        return entities
    
    def extract_relations(self, text: str) -> Dict[str, List[Dict]]:
        """
        抽取关系
        
        Args:
            text: 输入文本
            
        Returns:
            关系抽取结果
        """
        relations = {}
        
        for relation_type, patterns in self.relation_patterns.items():
            relations[relation_type] = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if relation_type == '部件故障':
                        subject = match.group(1).strip()
                        object_entity = match.group(2).strip()
                    elif relation_type == '性能故障':
                        subject = match.group(1).strip()
                        object_entity = match.group(2).strip()
                    elif relation_type == '检测工具':
                        subject = match.group(1).strip()
                        object_entity = match.group(4).strip()
                    elif relation_type == '组成关系':
                        subject = match.group(1).strip()
                        object_entity = match.group(3).strip()
                    else:
                        continue
                    
                    # 检查主体和客体是否在实体词典中
                    if self._is_valid_entity(subject, relation_type) and self._is_valid_entity(object_entity, relation_type):
                        relations[relation_type].append({
                            'text': f"{subject}{object_entity}",
                            'start': match.start(),
                            'end': match.end(),
                            'probability': 0.88,  # 模拟概率
                            'subject': subject,
                            'object': object_entity
                        })
        
        return relations
    
    def _is_valid_entity(self, entity: str, relation_type: str) -> bool:
        """
        检查实体是否有效
        
        Args:
            entity: 实体文本
            relation_type: 关系类型
            
        Returns:
            是否有效
        """
        # 根据关系类型确定主体和客体的实体类型
        entity_type_mapping = {
            '部件故障': ['部件单元', '故障状态'],
            '性能故障': ['性能表征', '故障状态'],
            '检测工具': ['检测工具', '性能表征'],
            '组成关系': ['部件单元', '部件单元']
        }
        
        valid_types = entity_type_mapping.get(relation_type, [])
        
        for entity_type in valid_types:
            if entity in self.entity_dict.get(entity_type, []):
                return True
        
        return False
    
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
        
        # 从关系抽取结果构建SPO三元组
        for relation_type, relation_items in relations.items():
            for item in relation_items:
                if 'subject' in item and 'object' in item:
                    # 找到主体和客体在文本中的位置
                    subject_pos = self._find_entity_position(item['subject'], entities)
                    object_pos = self._find_entity_position(item['object'], entities)
                    
                    if subject_pos and object_pos:
                        spo = {
                            'h': {
                                'name': item['subject'],
                                'pos': subject_pos
                            },
                            't': {
                                'name': item['object'],
                                'pos': object_pos
                            },
                            'relation': relation_type
                        }
                        spo_list.append(spo)
        
        return spo_list
    
    def _find_entity_position(self, entity: str, entities: Dict) -> Optional[List[int]]:
        """
        在实体抽取结果中查找实体的位置
        
        Args:
            entity: 实体文本
            entities: 实体抽取结果
            
        Returns:
            实体位置 [start, end]
        """
        for entity_type, entity_list in entities.items():
            for item in entity_list:
                if item['text'] == entity:
                    return [item['start'], item['end']]
        
        return None
    
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
    extractor = SimpleFaultExtractor()
    
    # 处理示例文本
    for example in example_texts:
        print(f"\n{'='*60}")
        extractor.process_single_text(example['text'], example['ID'])
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()