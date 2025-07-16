#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障诊断信息抽取系统快速启动脚本
一键运行演示和测试
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_dependencies():
    """
    检查系统依赖
    """
    print("🔍 检查系统依赖...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本需要 >= 3.7")
        return False
    
    # 检查必要的包
    required_packages = [
        'torch', 'transformers', 'numpy', 'tqdm'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 依赖检查通过!")
    return True


def download_model():
    """
    下载UIE模型
    """
    print("📥 检查UIE模型...")
    
    model_dir = Path("./uie-base")
    if model_dir.exists() and (model_dir / "pytorch_model.bin").exists():
        print("✅ UIE模型已存在!")
        return True
    
    print("📦 下载UIE模型...")
    try:
        cmd = ["python", "convert.py", "--model", "uie-base", "--save_dir", "./uie-base"]
        subprocess.run(cmd, check=True)
        print("✅ UIE模型下载完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 模型下载失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ convert.py文件不存在")
        return False


def run_demo():
    """
    运行演示
    """
    print("🚀 启动故障诊断演示...")
    
    try:
        cmd = ["python", "fault_diagnosis_uie.py", "--mode", "demo"]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 演示运行失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ fault_diagnosis_uie.py文件不存在")
        return False
    
    return True


def run_interactive():
    """
    运行交互式模式
    """
    print("🎯 启动交互式模式...")
    print("💡 提示: 输入'quit'退出")
    
    try:
        cmd = ["python", "fault_diagnosis_uie.py", "--mode", "interactive"]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 交互式模式运行失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ fault_diagnosis_uie.py文件不存在")
        return False
    except KeyboardInterrupt:
        print("\n👋 退出交互式模式")
    
    return True


def process_sample_data():
    """
    处理示例数据
    """
    print("📊 处理示例数据...")
    
    # 检查示例数据是否存在
    sample_file = Path("sample_data.json")
    if not sample_file.exists():
        print("❌ sample_data.json文件不存在")
        return False
    
    try:
        cmd = [
            "python", "fault_diagnosis_uie.py",
            "--mode", "process",
            "--input_file", "sample_data.json",
            "--output_file", "sample_results.json",
            "--model_path", "uie-base"
        ]
        subprocess.run(cmd, check=True)
        print("✅ 示例数据处理完成! 结果保存在 sample_results.json")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据处理失败: {e}")
        return False


def prepare_training_data():
    """
    准备训练数据
    """
    print("🔄 准备训练数据...")
    
    sample_file = Path("sample_data.json")
    if not sample_file.exists():
        print("❌ sample_data.json文件不存在")
        return False
    
    try:
        cmd = [
            "python", "data_processor.py",
            "--input_file", "sample_data.json",
            "--output_dir", "./processed_data",
            "--format", "uie",
            "--split_ratio", "0.8"
        ]
        subprocess.run(cmd, check=True)
        print("✅ 训练数据准备完成! 输出目录: ./processed_data")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据处理失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ data_processor.py文件不存在")
        return False


def show_system_info():
    """
    显示系统信息
    """
    print("\n" + "="*50)
    print("🔧 系统信息")
    print("="*50)
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 检查文件
    required_files = [
        "fault_diagnosis_uie.py",
        "data_processor.py", 
        "fault_evaluation.py",
        "fault_finetune.py",
        "sample_data.json",
        "requirements.txt"
    ]
    
    print("\n📁 文件检查:")
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
    
    # 检查模型
    model_dir = Path("./uie-base")
    if model_dir.exists():
        print(f"✅ UIE模型目录: {model_dir}")
        if (model_dir / "pytorch_model.bin").exists():
            print("  ✅ pytorch_model.bin")
        else:
            print("  ❌ pytorch_model.bin")
    else:
        print("❌ UIE模型目录不存在")


def main():
    parser = argparse.ArgumentParser(description="故障诊断信息抽取系统快速启动")
    parser.add_argument(
        "--action", 
        choices=["demo", "interactive", "process", "prepare", "info", "setup"],
        default="demo",
        help="选择执行的操作"
    )
    parser.add_argument("--skip-check", action="store_true", help="跳过依赖检查")
    
    args = parser.parse_args()
    
    print("🎉 欢迎使用故障诊断信息抽取系统!")
    print("="*50)
    
    # 显示系统信息
    if args.action == "info":
        show_system_info()
        return
    
    # 完整设置
    if args.action == "setup":
        print("🔧 开始完整设置...")
        
        if not check_dependencies():
            return
        
        if not download_model():
            return
        
        if not prepare_training_data():
            print("⚠️  训练数据准备失败，但演示仍可运行")
        
        print("✅ 设置完成!")
        print("💡 现在可以运行: python quick_start.py --action demo")
        return
    
    # 检查依赖
    if not args.skip_check and not check_dependencies():
        print("💡 建议先运行: python quick_start.py --action setup")
        return
    
    # 执行相应操作
    if args.action == "demo":
        # 确保模型存在
        if not Path("./uie-base").exists():
            if not download_model():
                return
        
        run_demo()
        
    elif args.action == "interactive":
        # 确保模型存在
        if not Path("./uie-base").exists():
            if not download_model():
                return
        
        run_interactive()
        
    elif args.action == "process":
        # 确保模型存在
        if not Path("./uie-base").exists():
            if not download_model():
                return
        
        process_sample_data()
        
    elif args.action == "prepare":
        prepare_training_data()
    
    print("\n🎉 操作完成!")


if __name__ == "__main__":
    main()