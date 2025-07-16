#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障案例信息抽取系统测试脚本
验证系统的基本功能是否正常工作
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


def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        import torch
        import transformers
        import numpy as np
        import tqdm
        print("✓ 基础依赖导入成功")
    except ImportError as e:
        print(f"✗ 基础依赖导入失败: {e}")
        return False
    
    try:
        from utils import logger, IEDataset, convert_ext_examples
        print("✓ UIE工具模块导入成功")
    except ImportError as e:
        print(f"✗ UIE工具模块导入失败: {e}")
        return False
    
    try:
        from model import UIE
        print("✓ UIE模型模块导入成功")
    except ImportError as e:
        print(f"✗ UIE模型模块导入失败: {e}")
        return False
    
    try:
        from uie_predictor import UIEPredictor
        print("✓ UIE预测器导入成功")
    except ImportError as e:
        print(f"✗ UIE预测器导入失败: {e}")
        return False
    
    return True


def test_preprocessing():
    """测试数据预处理"""
    print("测试数据预处理...")
    
    try:
        # 检查预处理脚本是否存在
        if not os.path.exists("preprocess_fault_data.py"):
            print("✗ 预处理脚本不存在")
            return False
        
        # 检查示例数据是否存在
        if not os.path.exists("sample_fault_data.json"):
            print("✗ 示例数据不存在")
            return False
        
        print("✓ 预处理脚本和示例数据存在")
        return True
    except Exception as e:
        print(f"✗ 预处理测试失败: {e}")
        return False


def test_training():
    """测试训练脚本"""
    print("测试训练脚本...")
    
    try:
        # 检查训练脚本是否存在
        if not os.path.exists("train_fault_extraction.py"):
            print("✗ 训练脚本不存在")
            return False
        
        print("✓ 训练脚本存在")
        return True
    except Exception as e:
        print(f"✗ 训练测试失败: {e}")
        return False


def test_prediction():
    """测试预测脚本"""
    print("测试预测脚本...")
    
    try:
        # 检查预测脚本是否存在
        if not os.path.exists("predict_fault_extraction.py"):
            print("✗ 预测脚本不存在")
            return False
        
        print("✓ 预测脚本存在")
        return True
    except Exception as e:
        print(f"✗ 预测测试失败: {e}")
        return False


def test_run_script():
    """测试运行脚本"""
    print("测试运行脚本...")
    
    try:
        # 检查运行脚本是否存在
        if not os.path.exists("run_fault_extraction.py"):
            print("✗ 运行脚本不存在")
            return False
        
        print("✓ 运行脚本存在")
        return True
    except Exception as e:
        print(f"✗ 运行脚本测试失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("测试目录结构...")
    
    # 创建必要的目录
    directories = ["data", "checkpoints", "results", "logs"]
    
    try:
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            print(f"✓ 目录 {directory} 创建成功")
        
        return True
    except Exception as e:
        print(f"✗ 目录结构测试失败: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("测试基本功能...")
    
    try:
        # 测试实体类型判断
        from preprocess_fault_data import get_entity_type
        
        test_cases = [
            ("燃油泵", "部件单元"),
            ("压力", "性能表征"),
            ("抖动", "故障状态"),
            ("互感器", "检测工具")
        ]
        
        for entity_name, expected_type in test_cases:
            actual_type = get_entity_type(entity_name)
            if actual_type == expected_type:
                print(f"✓ 实体类型判断正确: {entity_name} -> {actual_type}")
            else:
                print(f"✗ 实体类型判断错误: {entity_name} -> {actual_type} (期望: {expected_type})")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("故障案例信息抽取系统测试")
    print("="*50)
    
    tests = [
        ("数据格式", test_data_format),
        ("模块导入", test_imports),
        ("数据预处理", test_preprocessing),
        ("模型训练", test_training),
        ("模型预测", test_prediction),
        ("运行脚本", test_run_script),
        ("目录结构", test_directory_structure),
        ("基本功能", test_basic_functionality)
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
        print("🎉 所有测试通过！系统可以正常使用。")
        print("\n下一步:")
        print("1. 运行完整流程: python run_fault_extraction.py")
        print("2. 查看README文档: cat README_fault_extraction.md")
        return True
    else:
        print("❌ 部分测试失败，请检查系统配置。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)