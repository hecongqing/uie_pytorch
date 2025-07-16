#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的工业制造领域故障案例信息抽取
修复关系抽取问题，提供更准确的结果
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pprint import pprint


class ImprovedFaultExtractor:
    """改进的工业故障信息抽取器"""
    
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
        
        # 改进的关系模式
        self.relation_patterns = {
            '部件故障': [
                # 直接匹配模式
                r'([^，。；\s]+?)(抖动|损坏|断裂|变形|卡滞|松旷|漏油|加速不良|无法起动|发卡)',
                # 包含模式
                r'([^，。；\s]+?)(出现|发生|导致)([^，。；]*?)(故障|问题|异常)',
                # 描述模式
                r'([^，。；\s]+?)(后部|后)([^，。；]*?)(抖动|损坏|断裂|变形|卡滞|松旷|漏油)',
                r'([^，。；\s]+?)(后)([^，。；]*?)([^，。；]*?)(抖动|损坏|断裂|变形|卡滞|松旷|漏油)'
            ],
            '性能故障': [
                r'([^，。；\s]+?)(变低|变高|异常|不稳定|下降|上升|阻力过大)',
                r'([^，。；\s]+?)(出现|发生)([^，。；]*?)(异常|问题)'
            ],
            '检测工具': [
                r'([^，。；\s]+?)(检测|测量|监控)([^，。；]*?)([^，。；]+)',
                r'([^，。；\s]+?)(用于|用来)([^，。；]*?)([^，。；]+)'
            ],
            '组成关系': [
                r'([^，。；\s]+?)(包含|包括|由)([^，。；]*?)([^，。；]+)',
                r'([^，。；\s]+?)(和|与)([^，。；]+)',
                r'([^，。；\s]+?)(连接|连接着)([^，。；]+)'
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
                        if len(match.groups()) == 2:
                            # 直接匹配模式
                            subject = match.group(1).strip()
                            object_entity = match.group(2).strip()
                        elif len(match.groups()) == 4:
                            # 包含模式
                            subject = match.group(1).strip()
                            object_entity = match.group(4).strip()
                        elif len(match.groups()) == 4:
                            # 描述模式
                            subject = match.group(1).strip()
                            object_entity = match.group(4).strip()
                        else:
                            continue
                    elif relation_type == '性能故障':
                        if len(match.groups()) == 2:
                            subject = match.group(1).strip()
                            object_entity = match.group(2).strip()
                        elif len(match.groups()) == 4:
                            subject = match.group(1).strip()
                            object_entity = match.group(4).strip()
                        else:
                            continue
                    elif relation_type == '检测工具':
                        if len(match.groups()) == 4:
                            subject = match.group(1).strip()
                            object_entity = match.group(4).strip()
                        else:
                            continue
                    elif relation_type == '组成关系':
                        if len(match.groups()) == 4:
                            subject = match.group(1).strip()
                            object_entity = match.group(4).strip()
                        elif len(match.groups()) == 2:
                            subject = match.group(1).strip()
                            object_entity = match.group(2).strip()
                        else:
                            continue
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
        
        # 如果没有从关系抽取中得到结果，尝试从实体抽取中构建关系
        if not spo_list:
            spo_list = self._build_spo_from_entities(entities, text)
        
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
        composition_keywords = ['包含', '包括', '由', '组成', '构成', '连接', '连接着', '与', '和']
        
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
        output_file = f"improved_result_{sample_id}.json"
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
    extractor = ImprovedFaultExtractor()
    
    # 处理示例文本
    for example in example_texts:
        print(f"\n{'='*60}")
        extractor.process_single_text(example['text'], example['ID'])
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()