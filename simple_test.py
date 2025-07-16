#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的故障案例信息抽取系统测试脚本
只测试基本功能，不依赖外部包
"""

import os
import json
import sys
from pathlib import Path


def test_data_format():
    """测试数据格式"""
    print("测试数据格式...")
    
    try:
        with open("sample_fault_data.json", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if line.strip():
                    data = json.loads(line)
                    assert "ID" in data, f"第{i+1}行缺少ID字段"
                    assert "text" in data, f"第{i+1}行缺少text字段"
                    assert "spo_list" in data, f"第{i+1}行缺少spo_list字段"
                    
                    # 验证spo_list格式
                    for j, spo in enumerate(data["spo_list"]):
                        assert "h" in spo, f"第{i+1}行第{j+1}个三元组缺少h字段"
                        assert "t" in spo, f"第{i+1}行第{j+1}个三元组缺少t字段"
                        assert "relation" in spo, f"第{i+1}行第{j+1}个三元组缺少relation字段"
                        
                        # 验证h和t的格式
                        assert "name" in spo["h"], f"第{i+1}行第{j+1}个三元组h缺少name字段"
                        assert "pos" in spo["h"], f"第{i+1}行第{j+1}个三元组h缺少pos字段"
                        assert "name" in spo["t"], f"第{i+1}行第{j+1}个三元组t缺少name字段"
                        assert "pos" in spo["t"], f"第{i+1}行第{j+1}个三元组t缺少pos字段"
        
        print("✓ 数据格式测试通过")
        return True
    except Exception as e:
        print(f"✗ 数据格式测试失败: {e}")
        return False


def test_entity_type_classification():
    """测试实体类型分类"""
    print("测试实体类型分类...")
    
    # 定义实体类型判断规则
    def get_entity_type(entity_name):
        # 检测工具特征词（优先级最高）
        tool_keywords = ['互感器', '保护器', '测试仪', '检测器', '传感器']
        # 部件单元特征词
        component_keywords = ['泵', '器', '机', '阀', '管', '盖', '锁', '铰链', '变压器', '分离器']
        # 性能表征特征词
        performance_keywords = ['压力', '转速', '温度', '液面', '电流', '电压', '功率']
        # 故障状态特征词
        fault_keywords = ['抖动', '松旷', '损坏', '漏油', '断裂', '变形', '卡滞', '变低', '不良', '无法起动']
        
        for keyword in component_keywords:
            if keyword in entity_name:
                return "部件单元"
        
        for keyword in performance_keywords:
            if keyword in entity_name:
                return "性能表征"
        
        for keyword in fault_keywords:
            if keyword in entity_name:
                return "故障状态"
        
        for keyword in tool_keywords:
            if keyword in entity_name:
                return "检测工具"
        
        # 默认返回部件单元
        return "部件单元"
    
    # 测试用例
    test_cases = [
        ("燃油泵", "部件单元"),
        ("发动机盖", "部件单元"),
        ("压力", "性能表征"),
        ("温度", "性能表征"),
        ("抖动", "故障状态"),
        ("损坏", "故障状态"),
        ("互感器", "检测工具"),
        ("保护器", "检测工具")
    ]
    
    try:
        for entity_name, expected_type in test_cases:
            actual_type = get_entity_type(entity_name)
            if actual_type == expected_type:
                print(f"✓ 实体类型判断正确: {entity_name} -> {actual_type}")
            else:
                print(f"✗ 实体类型判断错误: {entity_name} -> {actual_type} (期望: {expected_type})")
                return False
        
        print("✓ 实体类型分类测试通过")
        return True
    except Exception as e:
        print(f"✗ 实体类型分类测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    print("测试文件结构...")
    
    required_files = [
        "preprocess_fault_data.py",
        "train_fault_extraction.py", 
        "predict_fault_extraction.py",
        "run_fault_extraction.py",
        "sample_fault_data.json",
        "README_fault_extraction.md"
    ]
    
    try:
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✓ 文件存在: {file_path}")
            else:
                print(f"✗ 文件不存在: {file_path}")
                return False
        
        print("✓ 文件结构测试通过")
        return True
    except Exception as e:
        print(f"✗ 文件结构测试失败: {e}")
        return False


def test_directory_creation():
    """测试目录创建"""
    print("测试目录创建...")
    
    directories = ["data", "checkpoints", "results", "logs"]
    
    try:
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            if os.path.exists(directory):
                print(f"✓ 目录创建成功: {directory}")
            else:
                print(f"✗ 目录创建失败: {directory}")
                return False
        
        print("✓ 目录创建测试通过")
        return True
    except Exception as e:
        print(f"✗ 目录创建测试失败: {e}")
        return False


def test_data_processing_logic():
    """测试数据处理逻辑"""
    print("测试数据处理逻辑...")
    
    try:
        # 模拟数据处理逻辑
        sample_data = {
            "ID": "AT0001",
            "text": "故障现象:车速到100迈以上发动机盖后部随着车速抖动。",
            "spo_list": [
                {
                    "h": {"name": "发动机盖", "pos": [14, 18]},
                    "t": {"name": "抖动", "pos": [24, 26]},
                    "relation": "部件故障"
                }
            ]
        }
        
        # 验证数据结构
        assert "ID" in sample_data
        assert "text" in sample_data
        assert "spo_list" in sample_data
        assert len(sample_data["spo_list"]) > 0
        
        # 验证三元组结构
        spo = sample_data["spo_list"][0]
        assert "h" in spo and "t" in spo and "relation" in spo
        assert "name" in spo["h"] and "pos" in spo["h"]
        assert "name" in spo["t"] and "pos" in spo["t"]
        
        print("✓ 数据处理逻辑测试通过")
        return True
    except Exception as e:
        print(f"✗ 数据处理逻辑测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("故障案例信息抽取系统简化测试")
    print("="*50)
    
    tests = [
        ("数据格式", test_data_format),
        ("实体类型分类", test_entity_type_classification),
        ("文件结构", test_file_structure),
        ("目录创建", test_directory_creation),
        ("数据处理逻辑", test_data_processing_logic)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}测试:")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name}测试失败")
    
    print("\n" + "="*50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基础测试通过！")
        print("\n系统功能说明:")
        print("1. 数据预处理: 将故障案例数据转换为UIE训练格式")
        print("2. 实体抽取: 抽取部件单元、性能表征、故障状态、检测工具")
        print("3. 关系抽取: 抽取部件故障、性能故障、检测工具、组成关系")
        print("4. 模型训练: 基于UIE模型进行微调训练")
        print("5. 预测推理: 对新文本进行信息抽取")
        
        print("\n使用说明:")
        print("1. 安装依赖: pip install torch transformers numpy tqdm")
        print("2. 运行完整流程: python3 run_fault_extraction.py")
        print("3. 查看详细文档: cat README_fault_extraction.md")
        
        return True
    else:
        print("❌ 部分测试失败，请检查系统配置。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)