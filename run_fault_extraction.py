#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障案例信息抽取完整运行脚本
包含数据预处理、模型训练和预测的完整流程
"""

import os
import json
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理错误"""
    print(f"\n{'='*50}")
    print(f"执行: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("执行成功!")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"执行失败: {e}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False


def check_dependencies():
    """检查依赖"""
    print("检查依赖...")
    
    required_packages = [
        "torch",
        "transformers", 
        "numpy",
        "tqdm"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少依赖包: {missing_packages}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("依赖检查通过!")
    return True


def create_directories():
    """创建必要的目录"""
    directories = [
        "data",
        "checkpoints", 
        "results",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"创建目录: {directory}")


def preprocess_data(input_file, output_dir):
    """数据预处理"""
    cmd = f"python preprocess_fault_data.py --input_file {input_file} --output_dir {output_dir}"
    return run_command(cmd, "数据预处理")


def train_model(train_path, dev_path, config_file, model, save_dir, device, **kwargs):
    """模型训练"""
    cmd = f"python train_fault_extraction.py --train_path {train_path} --dev_path {dev_path} --config_file {config_file} --model {model} --save_dir {save_dir} --device {device}"
    
    # 添加可选参数
    for key, value in kwargs.items():
        if value is not None:
            cmd += f" --{key} {value}"
    
    return run_command(cmd, "模型训练")


def predict(model_path, config_file, test_file, output_file, device):
    """模型预测"""
    cmd = f"python predict_fault_extraction.py --model_path {model_path} --config_file {config_file} --test_file {test_file} --output_file {output_file} --device {device} --verbose"
    return run_command(cmd, "模型预测")


def main():
    parser = argparse.ArgumentParser(description="故障案例信息抽取完整流程")
    
    # 数据相关参数
    parser.add_argument("--input_file", type=str, default="sample_fault_data.json", help="输入数据文件")
    parser.add_argument("--data_dir", type=str, default="./data", help="数据目录")
    parser.add_argument("--checkpoint_dir", type=str, default="./checkpoints", help="模型保存目录")
    parser.add_argument("--result_dir", type=str, default="./results", help="结果保存目录")
    
    # 模型相关参数
    parser.add_argument("--model", type=str, default="uie-base", help="预训练模型")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "gpu"], help="设备类型")
    
    # 训练相关参数
    parser.add_argument("--num_epochs", type=int, default=5, help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=8, help="批次大小")
    parser.add_argument("--learning_rate", type=float, default=1e-5, help="学习率")
    parser.add_argument("--early_stopping", action="store_true", help="是否使用早停")
    
    # 流程控制
    parser.add_argument("--skip_preprocess", action="store_true", help="跳过数据预处理")
    parser.add_argument("--skip_train", action="store_true", help="跳过模型训练")
    parser.add_argument("--skip_predict", action="store_true", help="跳过模型预测")
    parser.add_argument("--only_predict", action="store_true", help="仅进行预测")
    
    args = parser.parse_args()
    
    print("故障案例信息抽取系统")
    print("="*50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 如果只是预测，跳过训练相关步骤
    if args.only_predict:
        print("仅进行预测模式")
        model_path = os.path.join(args.checkpoint_dir, "model_best")
        config_file = os.path.join(args.data_dir, "config.json")
        test_file = args.input_file
        output_file = os.path.join(args.result_dir, "prediction_results.json")
        
        if not os.path.exists(model_path):
            print(f"错误: 模型路径不存在: {model_path}")
            sys.exit(1)
        
        if not os.path.exists(config_file):
            print(f"错误: 配置文件不存在: {config_file}")
            sys.exit(1)
        
        predict(model_path, config_file, test_file, output_file, args.device)
        return
    
    # 数据预处理
    if not args.skip_preprocess:
        if not os.path.exists(args.input_file):
            print(f"错误: 输入文件不存在: {args.input_file}")
            sys.exit(1)
        
        if not preprocess_data(args.input_file, args.data_dir):
            print("数据预处理失败!")
            sys.exit(1)
    
    # 检查预处理结果
    train_path = os.path.join(args.data_dir, "train.txt")
    dev_path = os.path.join(args.data_dir, "dev.txt")
    config_file = os.path.join(args.data_dir, "config.json")
    
    if not os.path.exists(train_path) or not os.path.exists(dev_path):
        print("错误: 预处理后的数据文件不存在，请先运行数据预处理")
        sys.exit(1)
    
    # 模型训练
    if not args.skip_train:
        train_kwargs = {
            "num_epochs": args.num_epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate
        }
        
        if args.early_stopping:
            train_kwargs["early_stopping"] = True
        
        if not train_model(train_path, dev_path, config_file, args.model, args.checkpoint_dir, args.device, **train_kwargs):
            print("模型训练失败!")
            sys.exit(1)
    
    # 模型预测
    if not args.skip_predict:
        model_path = os.path.join(args.checkpoint_dir, "model_best")
        test_file = os.path.join(args.data_dir, "test.txt")
        output_file = os.path.join(args.result_dir, "prediction_results.json")
        
        if not os.path.exists(model_path):
            print(f"错误: 训练好的模型不存在: {model_path}")
            sys.exit(1)
        
        if not predict(model_path, config_file, test_file, output_file, args.device):
            print("模型预测失败!")
            sys.exit(1)
    
    print("\n" + "="*50)
    print("所有任务完成!")
    print("="*50)
    
    # 显示结果文件位置
    if os.path.exists(os.path.join(args.result_dir, "prediction_results.json")):
        print(f"预测结果保存在: {os.path.join(args.result_dir, 'prediction_results.json')}")
    
    if os.path.exists(os.path.join(args.checkpoint_dir, "model_best")):
        print(f"最佳模型保存在: {os.path.join(args.checkpoint_dir, 'model_best')}")


if __name__ == "__main__":
    main()