#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障案例信息抽取训练脚本
基于UIE模型进行故障案例的实体和关系抽取训练
"""

import os
import json
import argparse
import torch
from torch.utils.data import DataLoader
from transformers import BertTokenizerFast

from utils import IEDataset, logger, set_seed, SpanEvaluator, EarlyStopping
from model import UIE
from evaluate import evaluate


def load_config(config_file: str) -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def train_fault_extraction():
    """训练故障案例信息抽取模型"""
    
    # 设置随机种子
    set_seed(args.seed)
    
    # 加载配置
    config = load_config(args.config_file)
    logger.info(f"Loaded config: {config}")
    
    # 初始化tokenizer和模型
    logger.info(f"Initializing model from {args.model}")
    tokenizer = BertTokenizerFast.from_pretrained(args.model)
    model = UIE.from_pretrained(args.model)
    
    if args.device == 'gpu':
        model = model.cuda()
        logger.info("Using GPU for training")
    else:
        logger.info("Using CPU for training")
    
    # 创建数据集
    logger.info("Creating datasets")
    train_ds = IEDataset(args.train_path, tokenizer=tokenizer, max_seq_len=args.max_seq_len)
    dev_ds = IEDataset(args.dev_path, tokenizer=tokenizer, max_seq_len=args.max_seq_len)
    
    train_data_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    dev_data_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False)
    
    logger.info(f"Train dataset size: {len(train_ds)}")
    logger.info(f"Dev dataset size: {len(dev_ds)}")
    
    # 初始化优化器和损失函数
    optimizer = torch.optim.AdamW(lr=args.learning_rate, params=model.parameters())
    criterion = torch.nn.functional.binary_cross_entropy
    metric = SpanEvaluator()
    
    # 早停机制
    if args.early_stopping:
        early_stopping_save_dir = os.path.join(args.save_dir, "early_stopping")
        if not os.path.exists(early_stopping_save_dir):
            os.makedirs(early_stopping_save_dir)
        early_stopping = EarlyStopping(
            patience=args.patience, 
            verbose=True, 
            trace_func=logger.info,
            save_dir=early_stopping_save_dir
        )
    
    # 训练循环
    loss_list = []
    loss_sum = 0
    loss_num = 0
    global_step = 0
    best_step = 0
    best_f1 = 0
    
    logger.info("Starting training...")
    
    for epoch in range(1, args.num_epochs + 1):
        logger.info(f"Epoch {epoch}/{args.num_epochs}")
        
        model.train()
        for batch_idx, batch in enumerate(train_data_loader):
            input_ids, token_type_ids, att_mask, start_ids, end_ids = batch
            
            if args.device == 'gpu':
                input_ids = input_ids.cuda()
                token_type_ids = token_type_ids.cuda()
                att_mask = att_mask.cuda()
                start_ids = start_ids.cuda()
                end_ids = end_ids.cuda()
            
            # 前向传播
            outputs = model(
                input_ids=input_ids,
                token_type_ids=token_type_ids,
                attention_mask=att_mask
            )
            start_prob, end_prob = outputs[0], outputs[1]
            
            # 计算损失
            start_ids = start_ids.type(torch.float32)
            end_ids = end_ids.type(torch.float32)
            loss_start = criterion(start_prob, start_ids)
            loss_end = criterion(end_prob, end_ids)
            loss = (loss_start + loss_end) / 2.0
            
            # 反向传播
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            # 记录损失
            loss_list.append(float(loss))
            loss_sum += float(loss)
            loss_num += 1
            
            global_step += 1
            
            # 打印训练信息
            if global_step % args.logging_steps == 0:
                loss_avg = loss_sum / loss_num
                logger.info(f"Step {global_step}, Epoch {epoch}, Loss: {loss_avg:.5f}")
                loss_sum = 0
                loss_num = 0
            
            # 验证
            if global_step % args.valid_steps == 0:
                logger.info(f"Evaluating at step {global_step}")
                
                # 保存模型
                save_dir = os.path.join(args.save_dir, f"model_{global_step}")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                model.save_pretrained(save_dir)
                tokenizer.save_pretrained(save_dir)
                
                # 评估
                dev_loss_avg, precision, recall, f1 = evaluate(
                    model, metric, data_loader=dev_data_loader, 
                    device=args.device, loss_fn=criterion
                )
                
                logger.info(f"Evaluation - Precision: {precision:.5f}, Recall: {recall:.5f}, F1: {f1:.5f}, Loss: {dev_loss_avg:.5f}")
                
                # 保存最佳模型
                if f1 > best_f1:
                    logger.info(f"New best F1: {best_f1:.5f} -> {f1:.5f}")
                    best_f1 = f1
                    best_step = global_step
                    
                    save_dir = os.path.join(args.save_dir, "model_best")
                    model.save_pretrained(save_dir)
                    tokenizer.save_pretrained(save_dir)
                    
                    # 保存最佳模型信息
                    best_model_info = {
                        "best_f1": best_f1,
                        "best_step": best_step,
                        "precision": precision,
                        "recall": recall,
                        "config": config
                    }
                    with open(os.path.join(save_dir, "best_model_info.json"), 'w', encoding='utf-8') as f:
                        json.dump(best_model_info, f, ensure_ascii=False, indent=2)
                
                # 早停检查
                if args.early_stopping:
                    early_stopping(dev_loss_avg, model)
                    if early_stopping.early_stop:
                        logger.info("Early stopping triggered")
                        break
        
        # 每个epoch结束后验证
        if not args.early_stopping or not early_stopping.early_stop:
            logger.info(f"Epoch {epoch} evaluation")
            dev_loss_avg, precision, recall, f1 = evaluate(
                model, metric, data_loader=dev_data_loader, 
                device=args.device, loss_fn=criterion
            )
            logger.info(f"Epoch {epoch} - Precision: {precision:.5f}, Recall: {recall:.5f}, F1: {f1:.5f}, Loss: {dev_loss_avg:.5f}")
    
    logger.info(f"Training completed! Best F1: {best_f1:.5f} at step {best_step}")


def main():
    parser = argparse.ArgumentParser(description="故障案例信息抽取训练")
    
    # 数据相关参数
    parser.add_argument("--train_path", type=str, required=True, help="训练数据路径")
    parser.add_argument("--dev_path", type=str, required=True, help="验证数据路径")
    parser.add_argument("--config_file", type=str, required=True, help="配置文件路径")
    
    # 模型相关参数
    parser.add_argument("--model", type=str, default="uie-base", help="预训练模型")
    parser.add_argument("--save_dir", type=str, default="./checkpoints", help="模型保存目录")
    parser.add_argument("--max_seq_len", type=int, default=512, help="最大序列长度")
    
    # 训练相关参数
    parser.add_argument("--num_epochs", type=int, default=10, help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=16, help="批次大小")
    parser.add_argument("--learning_rate", type=float, default=1e-5, help="学习率")
    parser.add_argument("--logging_steps", type=int, default=100, help="日志打印步数")
    parser.add_argument("--valid_steps", type=int, default=500, help="验证步数")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    
    # 设备相关参数
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "gpu"], help="设备类型")
    
    # 早停相关参数
    parser.add_argument("--early_stopping", action="store_true", help="是否使用早停")
    parser.add_argument("--patience", type=int, default=3, help="早停耐心值")
    
    global args
    args = parser.parse_args()
    
    # 创建保存目录
    os.makedirs(args.save_dir, exist_ok=True)
    
    # 开始训练
    train_fault_extraction()


if __name__ == "__main__":
    main()