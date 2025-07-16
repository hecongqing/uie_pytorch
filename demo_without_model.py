#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障诊断信息抽取系统演示脚本（不依赖实际模型）
展示系统的核心逻辑和数据处理流程
"""

import json
import re
from typing import List, Dict, Any


class MockFaultDiagnosisUIE:
    """
    模拟的故障诊断信息抽取器（不依赖实际模型）
    用于演示系统逻辑
    """
    
    def __init__(self):
        # 定义实体类型和关键词
        self.entity_keywords = {
            "部件单元": [
                "发动机", "燃油泵", "变速箱", "制动器", "减振器", "缸体", "缸盖", "活塞",
                "轴承", "齿轮", "离合器", "散热器", "密封件", "电机", "泵", "阀", "管路",
                "传动系统", "液压系统", "冷却系统", "制动盘", "制动片", "液压缸",
                "发动机盖", "发动机盖锁", "发动机盖铰链", "变速箱齿轮", "减振器活塞",
                "管路密封件", "电机轴承", "齿轮箱", "联轴器", "密封圈", "探伤设备"
            ],
            "性能表征": [
                "温度", "压力", "转速", "振动", "流量", "液面", "阻力", "效果",
                "频率", "深度", "水温", "润滑油", "工作阻力", "系统压力", 
                "振动频率", "制动效果", "冷却液流量", "轴承温度", "裂纹深度",
                "换挡", "压力不稳定", "温度过高"
            ],
            "故障状态": [
                "损坏", "磨损", "老化", "堵塞", "泄漏", "断裂", "变形", "卡滞",
                "松旷", "抖动", "异响", "渗油", "破损", "裂纹", "发卡", "过大",
                "升高", "下降", "不足", "加速不良", "无法起动", "无法启动"
            ],
            "检测工具": [
                "测试仪", "检测仪", "测量仪", "传感器", "监测器", "仪表",
                "振动测试仪", "红外测温仪", "压力表", "流量计", "探伤设备",
                "测温仪", "漏电测试仪", "零序互感器", "保护器"
            ]
        }
        
        # 关系类型映射
        self.relation_mappings = {
            "部件故障": ("部件单元", "故障状态"),
            "性能故障": ("性能表征", "故障状态"),
            "检测工具": ("检测工具", "性能表征"),
            "组成": ("部件单元", "部件单元")
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        使用关键词匹配进行实体抽取
        """
        entities = {}
        
        for entity_type, keywords in self.entity_keywords.items():
            entity_list = []
            for keyword in keywords:
                start = 0
                while True:
                    pos = text.find(keyword, start)
                    if pos == -1:
                        break
                    
                    entity_list.append({
                        "text": keyword,
                        "start": pos,
                        "end": pos + len(keyword)
                    })
                    start = pos + 1
            
            if entity_list:
                # 去重
                unique_entities = []
                seen = set()
                for entity in entity_list:
                    key = (entity["text"], entity["start"], entity["end"])
                    if key not in seen:
                        seen.add(key)
                        unique_entities.append(entity)
                
                entities[entity_type] = unique_entities
        
        return entities
    
    def extract_with_spo_format(self, text: str) -> List[Dict]:
        """
        使用简单规则进行关系抽取
        """
        spo_list = []
        
        # 首先抽取实体
        entities = self.extract_entities(text)
        
        # 根据距离和关键词判断关系
        for relation_name, (subject_type, object_type) in self.relation_mappings.items():
            if subject_type in entities and object_type in entities:
                for subject in entities[subject_type]:
                    for obj in entities[object_type]:
                        if self._check_relation_simple(text, subject, obj, relation_name):
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
    
    def _check_relation_simple(self, text: str, subject: Dict, obj: Dict, relation: str) -> bool:
        """
        简单的关系判断逻辑
        """
        # 检查实体间的距离
        distance = abs(subject["start"] - obj["start"])
        
        # 根据关系类型定义不同的判断规则
        if relation == "部件故障":
            # 部件和故障状态通常在附近出现
            return distance < 80
        elif relation == "性能故障":
            # 性能表征和故障状态通常在附近出现
            return distance < 50
        elif relation == "检测工具":
            # 检测工具和性能表征的关系
            keywords = ["检测", "测试", "测量", "监测", "用", "采用"]
            nearby_text = text[max(0, min(subject["start"], obj["start"])-30):
                             max(subject["end"], obj["end"])+30]
            return any(keyword in nearby_text for keyword in keywords) and distance < 100
        elif relation == "组成":
            # 组成关系的判断
            keywords = ["组成", "包含", "由", "的", "中的", "包括"]
            nearby_text = text[max(0, min(subject["start"], obj["start"])-20):
                             max(subject["end"], obj["end"])+20]
            return any(keyword in nearby_text for keyword in keywords) and distance < 50
        
        return False


def demo():
    """
    演示功能
    """
    print("🎉 故障诊断信息抽取系统演示")
    print("="*60)
    print("注意：这是一个模拟演示，使用简单的关键词匹配和规则")
    print("实际的UIE模型会有更好的性能\n")
    
    # 测试文本
    test_cases = [
        "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。",
        "燃油泵的作用是将燃油加压输送到喷油器，当燃油泵损坏后，燃油将不能正常喷入发动机气缸，因此将影响发动机的正常运转，使得发动机出现加速不良的症状，情况严重时将导致发动机无法起动。",
        "减振器活塞与缸体发卡，工作阻力过大诊断排除。",
        "变速箱齿轮磨损严重，导致换挡时出现异响。使用振动测试仪检测变速箱的振动频率。",
        "发动机由缸体、缸盖、活塞等部件组成。缸体出现裂纹，需要使用探伤设备检测裂纹深度。"
    ]
    
    extractor = MockFaultDiagnosisUIE()
    
    for i, text in enumerate(test_cases, 1):
        print(f"=== 测试案例 {i} ===")
        print(f"原文: {text}\n")
        
        # 抽取实体
        entities = extractor.extract_entities(text)
        print("📋 实体抽取结果:")
        for entity_type, entity_list in entities.items():
            if entity_list:
                entity_texts = [e['text'] for e in entity_list]
                print(f"  {entity_type}: {entity_texts}")
        
        # 抽取SPO三元组
        spo_list = extractor.extract_with_spo_format(text)
        print(f"\n🔗 关系抽取结果:")
        if spo_list:
            for spo in spo_list:
                print(f"  ({spo['h']['name']}, {spo['relation']}, {spo['t']['name']})")
        else:
            print("  未发现关系")
        
        print("-" * 60 + "\n")


def process_sample_data():
    """
    处理示例数据文件
    """
    print("📊 处理示例数据文件...")
    
    try:
        with open('sample_data.json', 'r', encoding='utf-8') as f:
            data_list = []
            for line in f:
                line = line.strip()
                if line:
                    data_list.append(json.loads(line))
        
        extractor = MockFaultDiagnosisUIE()
        results = []
        
        for data in data_list:
            text = data["text"]
            
            # 使用模拟抽取器处理
            spo_list = extractor.extract_with_spo_format(text)
            
            result = {
                "ID": data["ID"],
                "text": text,
                "predicted_spo_list": spo_list,
                "original_spo_list": data.get("spo_list", [])
            }
            results.append(result)
        
        # 保存结果
        with open('demo_results.json', 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"✅ 处理完成！共处理 {len(results)} 条数据")
        print("结果保存在 demo_results.json")
        
        # 显示简单的统计
        total_predicted = sum(len(r["predicted_spo_list"]) for r in results)
        total_original = sum(len(r["original_spo_list"]) for r in results)
        
        print(f"\n📈 统计信息:")
        print(f"原始标注关系数: {total_original}")
        print(f"预测关系数: {total_predicted}")
        
    except FileNotFoundError:
        print("❌ sample_data.json 文件不存在")
    except Exception as e:
        print(f"❌ 处理出错: {e}")


def show_data_format():
    """
    展示数据格式
    """
    print("📄 数据格式说明")
    print("="*50)
    
    sample_input = {
        "ID": "AT0001",
        "text": "发动机轴承温度过高，可能是润滑油不足导致的。",
        "spo_list": [
            {
                "h": {"name": "发动机轴承", "pos": [0, 5]},
                "t": {"name": "温度过高", "pos": [5, 9]},
                "relation": "性能故障"
            }
        ]
    }
    
    print("输入格式示例:")
    print(json.dumps(sample_input, ensure_ascii=False, indent=2))
    
    print("\n字段说明:")
    print("- ID: 样本唯一标识符")
    print("- text: 故障案例文本内容")
    print("- spo_list: SPO三元组列表")
    print("  - h: 头实体（主体）")
    print("  - t: 尾实体（客体）") 
    print("  - relation: 关系类型")
    print("  - pos: 实体在文本中的位置 [开始位置, 结束位置]")


def main():
    print("🎉 欢迎使用故障诊断信息抽取系统演示!")
    print("="*60)
    
    while True:
        print("\n选择操作:")
        print("1. 运行演示")
        print("2. 处理示例数据")
        print("3. 查看数据格式")
        print("4. 退出")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            demo()
        elif choice == "2":
            process_sample_data()
        elif choice == "3":
            show_data_format()
        elif choice == "4":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()