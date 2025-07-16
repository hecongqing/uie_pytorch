#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障诊断领域UIE模型微调脚本
"""

import argparse
import os
import shutil
import time
import torch
from torch.utils.data import DataLoader
from transformers import BertTokenizerFast
from utils import IEDataset, logger, tqdm, set_seed, SpanEvaluator, EarlyStopping, logging_redirect_tqdm
from model import UIE
from evaluate import evaluate


def create_fault_finetune_script():
    """
    创建故障诊断领域的微调脚本
    """
    
    def do_fault_train(args):
        """
        执行故障诊断模型训练
        """
        set_seed(args.seed)
        show_bar = True

        # 初始化tokenizer和模型
        tokenizer = BertTokenizerFast.from_pretrained(args.model)
        model = UIE.from_pretrained(args.model)
        
        if args.device == 'gpu':
            model = model.cuda()

        # 准备数据集
        train_ds = IEDataset(args.train_path, tokenizer=tokenizer,
                           max_seq_len=args.max_seq_len)
        dev_ds = IEDataset(args.dev_path, tokenizer=tokenizer,
                         max_seq_len=args.max_seq_len)

        train_data_loader = DataLoader(
            train_ds, batch_size=args.batch_size, shuffle=True)
        dev_data_loader = DataLoader(
            dev_ds, batch_size=args.batch_size, shuffle=False)

        # 优化器设置
        optimizer = torch.optim.AdamW(
            lr=args.learning_rate, params=model.parameters(), weight_decay=args.weight_decay)

        # 学习率调度器
        if args.warmup_steps > 0:
            from transformers import get_linear_schedule_with_warmup
            total_steps = len(train_data_loader) * args.num_epochs
            scheduler = get_linear_schedule_with_warmup(
                optimizer, 
                num_warmup_steps=args.warmup_steps, 
                num_training_steps=total_steps
            )
        else:
            scheduler = None

        criterion = torch.nn.functional.binary_cross_entropy
        metric = SpanEvaluator()

        # 早停机制
        if args.early_stopping:
            early_stopping_save_dir = os.path.join(args.save_dir, "early_stopping")
            if not os.path.exists(early_stopping_save_dir):
                os.makedirs(early_stopping_save_dir)
            if show_bar:
                def trace_func(*args, **kwargs):
                    with logging_redirect_tqdm([logger.logger]):
                        logger.info(*args, **kwargs)
            else:
                trace_func = logger.info
            early_stopping = EarlyStopping(
                patience=args.patience, verbose=True, trace_func=trace_func,
                save_dir=early_stopping_save_dir)

        # 训练变量初始化
        loss_list = []
        loss_sum = 0
        loss_num = 0
        global_step = 0
        best_step = 0
        best_f1 = 0
        tic_train = time.time()

        # 创建保存目录
        if not os.path.exists(args.save_dir):
            os.makedirs(args.save_dir)

        # 训练循环
        epoch_iterator = range(1, args.num_epochs + 1)
        if show_bar:
            train_postfix_info = {'loss': 'unknown'}
            epoch_iterator = tqdm(epoch_iterator, desc='Training', unit='epoch')

        for epoch in epoch_iterator:
            model.train()
            train_data_iterator = train_data_loader
            
            if show_bar:
                train_data_iterator = tqdm(train_data_iterator,
                                         desc=f'Training Epoch {epoch}', unit='batch')
                train_data_iterator.set_postfix(train_postfix_info)

            for batch in train_data_iterator:
                if show_bar:
                    epoch_iterator.refresh()
                
                input_ids, token_type_ids, att_mask, start_ids, end_ids = batch
                
                if args.device == 'gpu':
                    input_ids = input_ids.cuda()
                    token_type_ids = token_type_ids.cuda()
                    att_mask = att_mask.cuda()
                    start_ids = start_ids.cuda()
                    end_ids = end_ids.cuda()

                # 前向传播
                outputs = model(input_ids=input_ids,
                              token_type_ids=token_type_ids,
                              attention_mask=att_mask)
                start_logits, end_logits = outputs[0], outputs[1]

                # 计算损失
                start_loss = criterion(start_logits, start_ids)
                end_loss = criterion(end_logits, end_ids)
                loss = (start_loss + end_loss) / 2.0

                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                if scheduler:
                    scheduler.step()

                # 记录损失
                loss_list.append(float(loss))
                loss_sum += float(loss)
                loss_num += 1
                global_step += 1

                if show_bar:
                    train_postfix_info.update({
                        'loss': f'{loss_sum / loss_num:.5f}',
                        'lr': f'{optimizer.param_groups[0]["lr"]:.2e}'
                    })
                    train_data_iterator.set_postfix(train_postfix_info)

                # 定期评估
                if global_step % args.eval_steps == 0:
                    model.eval()
                    with torch.no_grad():
                        # 评估验证集
                        precision, recall, f1 = evaluate(model, metric, dev_data_loader, args.device)
                        
                        eval_info = f"Evaluation precision: {precision:.5f}, recall: {recall:.5f}, F1: {f1:.5f}"
                        
                        if show_bar:
                            with logging_redirect_tqdm([logger.logger]):
                                logger.info(eval_info)
                        else:
                            logger.info(eval_info)

                        # 保存最佳模型
                        if f1 > best_f1:
                            best_f1 = f1
                            best_step = global_step
                            model.save_pretrained(args.save_dir)
                            tokenizer.save_pretrained(args.save_dir)
                            
                            save_info = f"Best F1 updated: {best_f1:.5f} at step {best_step}"
                            if show_bar:
                                with logging_redirect_tqdm([logger.logger]):
                                    logger.info(save_info)
                            else:
                                logger.info(save_info)

                        # 早停检查
                        if args.early_stopping:
                            early_stopping(f1, model, tokenizer)
                            if early_stopping.early_stop:
                                logger.info("Early stopping triggered")
                                break
                    
                    model.train()

            # 每个epoch结束后也进行一次评估
            model.eval()
            with torch.no_grad():
                precision, recall, f1 = evaluate(model, metric, dev_data_loader, args.device)
                
                epoch_info = f"Epoch {epoch} - precision: {precision:.5f}, recall: {recall:.5f}, F1: {f1:.5f}"
                
                if show_bar:
                    with logging_redirect_tqdm([logger.logger]):
                        logger.info(epoch_info)
                else:
                    logger.info(epoch_info)

                if f1 > best_f1:
                    best_f1 = f1
                    best_step = global_step
                    model.save_pretrained(args.save_dir)
                    tokenizer.save_pretrained(args.save_dir)

            # 早停检查
            if args.early_stopping and early_stopping.early_stop:
                break

        # 训练结束
        train_time = time.time() - tic_train
        logger.info(f"Training completed in {train_time:.2f} seconds")
        logger.info(f"Best F1: {best_f1:.5f} at step {best_step}")

        # 如果使用了早停，恢复最佳模型
        if args.early_stopping and early_stopping.early_stop:
            logger.info("Loading best model from early stopping...")
            model = UIE.from_pretrained(early_stopping_save_dir)
            tokenizer = BertTokenizerFast.from_pretrained(early_stopping_save_dir)
            
            # 保存到最终目录
            model.save_pretrained(args.save_dir)
            tokenizer.save_pretrained(args.save_dir)

    return do_fault_train


def main():
    parser = argparse.ArgumentParser(description="故障诊断领域UIE模型微调")
    
    # 数据相关参数
    parser.add_argument("--train_path", type=str, required=True, help="训练数据路径")
    parser.add_argument("--dev_path", type=str, required=True, help="验证数据路径")
    parser.add_argument("--save_dir", type=str, default="./fault_uie_model", help="模型保存目录")
    
    # 模型相关参数
    parser.add_argument("--model", type=str, default="uie-base", help="预训练模型路径")
    parser.add_argument("--max_seq_len", type=int, default=512, help="最大序列长度")
    
    # 训练相关参数
    parser.add_argument("--batch_size", type=int, default=16, help="批次大小")
    parser.add_argument("--num_epochs", type=int, default=20, help="训练轮数")
    parser.add_argument("--learning_rate", type=float, default=1e-5, help="学习率")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="权重衰减")
    parser.add_argument("--warmup_steps", type=int, default=0, help="预热步数")
    
    # 评估和保存相关参数
    parser.add_argument("--eval_steps", type=int, default=100, help="评估间隔步数")
    parser.add_argument("--early_stopping", action="store_true", help="是否使用早停")
    parser.add_argument("--patience", type=int, default=7, help="早停耐心值")
    
    # 其他参数
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu", help="运行设备")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    
    args = parser.parse_args()
    
    # 检查必要的文件是否存在
    if not os.path.exists(args.train_path):
        logger.error(f"训练数据文件不存在: {args.train_path}")
        return
    
    if not os.path.exists(args.dev_path):
        logger.error(f"验证数据文件不存在: {args.dev_path}")
        return
    
    # 创建训练函数并执行
    do_fault_train = create_fault_finetune_script()
    
    logger.info("开始故障诊断模型微调...")
    logger.info(f"训练数据: {args.train_path}")
    logger.info(f"验证数据: {args.dev_path}")
    logger.info(f"模型保存路径: {args.save_dir}")
    logger.info(f"基础模型: {args.model}")
    logger.info(f"批次大小: {args.batch_size}")
    logger.info(f"学习率: {args.learning_rate}")
    logger.info(f"训练轮数: {args.num_epochs}")
    logger.info(f"设备: {args.device}")
    
    do_fault_train(args)
    
    logger.info("故障诊断模型微调完成！")


if __name__ == "__main__":
    main()