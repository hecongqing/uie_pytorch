#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工业故障信息抽取功能
"""

import json
import os
import sys
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fault_extraction_demo import FaultExtractionDemo


def test_basic_extraction():
    """测试基础抽取功能"""
    print("=" * 60)
    print("测试基础抽取功能")
    print("=" * 60)
    
    # 初始化抽取器
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 测试文本
    test_text = "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。"
    
    # 执行抽取
    result = extractor.extract_all(test_text)
    
    # 打印结果
    print("抽取结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


def test_entity_extraction():
    """测试实体抽取功能"""
    print("\n" + "=" * 60)
    print("测试实体抽取功能")
    print("=" * 60)
    
    # 初始化抽取器
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 测试文本
    test_text = "燃油泵的作用是将燃油加压输送到喷油器，当燃油泵损坏后，燃油将不能正常喷入发动机气缸，因此将影响发动机的正常运转，使得发动机出现加速不良的症状，情况严重时将导致发动机无法起动。"
    
    # 执行实体抽取
    entities = extractor.extract_entities(test_text)
    
    # 打印结果
    print("实体抽取结果:")
    for entity_type, entity_list in entities.items():
        print(f"\n{entity_type}:")
        for entity in entity_list:
            print(f"  - {entity['text']} (位置: {entity['start']}-{entity['end']}, 概率: {entity.get('probability', 'N/A'):.3f})")
    
    return entities


def test_relation_extraction():
    """测试关系抽取功能"""
    print("\n" + "=" * 60)
    print("测试关系抽取功能")
    print("=" * 60)
    
    # 初始化抽取器
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 测试文本
    test_text = "减振器活塞与缸体发卡，工作阻力过大诊断排除。"
    
    # 执行关系抽取
    relations = extractor.extract_relations(test_text)
    
    # 打印结果
    print("关系抽取结果:")
    for relation_type, relation_list in relations.items():
        print(f"\n{relation_type}:")
        for relation in relation_list:
            print(f"  - {relation['text']} (位置: {relation['start']}-{relation['end']}, 概率: {relation.get('probability', 'N/A'):.3f})")
    
    return relations


def test_spo_construction():
    """测试SPO三元组构建功能"""
    print("\n" + "=" * 60)
    print("测试SPO三元组构建功能")
    print("=" * 60)
    
    # 初始化抽取器
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 测试文本
    test_text = "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。"
    
    # 执行完整抽取
    result = extractor.extract_all(test_text)
    
    # 打印SPO列表
    print("SPO三元组列表:")
    for i, spo in enumerate(result['spo_list'], 1):
        print(f"\n三元组 {i}:")
        print(f"  主体: {spo['h']['name']} (位置: {spo['h']['pos']})")
        print(f"  关系: {spo['relation']}")
        print(f"  客体: {spo['t']['name']} (位置: {spo['t']['pos']})")
    
    return result['spo_list']


def test_multiple_samples():
    """测试多个样本的处理"""
    print("\n" + "=" * 60)
    print("测试多个样本的处理")
    print("=" * 60)
    
    # 初始化抽取器
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 测试样本
    test_samples = [
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
    
    # 处理每个样本
    results = []
    for sample in test_samples:
        print(f"\n处理样本 {sample['ID']}:")
        print(f"文本: {sample['text'][:50]}...")
        
        result = extractor.extract_all(sample['text'])
        result['ID'] = sample['ID']
        results.append(result)
        
        # 打印简要结果
        entity_count = sum(len(entities) for entities in result['entities'].values())
        relation_count = sum(len(relations) for relations in result['relations'].values())
        spo_count = len(result['spo_list'])
        
        print(f"抽取到 {entity_count} 个实体, {relation_count} 个关系, {spo_count} 个三元组")
    
    return results


def test_performance():
    """测试性能"""
    print("\n" + "=" * 60)
    print("测试性能")
    print("=" * 60)
    
    import time
    
    # 初始化抽取器
    extractor = FaultExtractionDemo(model_name='uie-base', device='cpu')
    
    # 测试文本
    test_text = "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。"
    
    # 预热
    print("预热模型...")
    for _ in range(3):
        extractor.extract_all(test_text)
    
    # 性能测试
    print("开始性能测试...")
    start_time = time.time()
    
    for i in range(10):
        result = extractor.extract_all(test_text)
        if i == 0:  # 只打印第一次的结果
            print(f"样本处理时间: {time.time() - start_time:.3f}秒")
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10
    
    print(f"平均处理时间: {avg_time:.3f}秒")
    print(f"处理速度: {1/avg_time:.2f} 样本/秒")


def save_test_results(results: Dict[str, Any], filename: str = "test_results.json"):
    """保存测试结果"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n测试结果已保存到: {filename}")


def main():
    """主测试函数"""
    print("开始工业故障信息抽取测试")
    print("=" * 60)
    
    # 存储所有测试结果
    all_results = {}
    
    try:
        # 测试基础抽取
        all_results['basic_extraction'] = test_basic_extraction()
        
        # 测试实体抽取
        all_results['entity_extraction'] = test_entity_extraction()
        
        # 测试关系抽取
        all_results['relation_extraction'] = test_relation_extraction()
        
        # 测试SPO构建
        all_results['spo_construction'] = test_spo_construction()
        
        # 测试多个样本
        all_results['multiple_samples'] = test_multiple_samples()
        
        # 测试性能
        test_performance()
        
        # 保存测试结果
        save_test_results(all_results)
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()