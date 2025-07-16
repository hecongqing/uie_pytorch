#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障诊断信息抽取评估脚本
评估模型在实体抽取和关系抽取任务上的性能
"""

import json
import argparse
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import numpy as np
from fault_diagnosis_uie import FaultDiagnosisUIE


class FaultEvaluator:
    """
    故障诊断信息抽取评估器
    """
    
    def __init__(self):
        self.entity_types = ["部件单元", "性能表征", "故障状态", "检测工具"]
        self.relation_types = ["部件故障", "性能故障", "检测工具", "组成"]
    
    def load_gold_data(self, file_path: str) -> List[Dict]:
        """
        加载标准答案数据
        
        Args:
            file_path: 标准答案文件路径
            
        Returns:
            标准答案数据列表
        """
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    data_list.append(data)
        return data_list
    
    def extract_entities_from_spo(self, spo_list: List[Dict]) -> Dict[str, Set[Tuple]]:
        """
        从SPO列表中提取实体信息
        
        Args:
            spo_list: SPO三元组列表
            
        Returns:
            实体字典，格式为 {entity_type: {(text, start, end), ...}}
        """
        entities = defaultdict(set)
        
        for spo in spo_list:
            h_entity = spo["h"]
            t_entity = spo["t"]
            relation = spo["relation"]
            
            # 根据关系类型推断实体类型
            if relation == "部件故障":
                h_type = "部件单元"
                t_type = "故障状态"
            elif relation == "性能故障":
                h_type = "性能表征"
                t_type = "故障状态"
            elif relation == "检测工具":
                h_type = "检测工具"
                t_type = "性能表征"
            elif relation == "组成":
                h_type = "部件单元"
                t_type = "部件单元"
            else:
                continue
            
            # 添加实体
            entities[h_type].add((h_entity["name"], h_entity["pos"][0], h_entity["pos"][1]))
            entities[t_type].add((t_entity["name"], t_entity["pos"][0], t_entity["pos"][1]))
        
        return entities
    
    def extract_relations_from_spo(self, spo_list: List[Dict]) -> Dict[str, Set[Tuple]]:
        """
        从SPO列表中提取关系信息
        
        Args:
            spo_list: SPO三元组列表
            
        Returns:
            关系字典，格式为 {relation_type: {(h_text, h_start, h_end, t_text, t_start, t_end), ...}}
        """
        relations = defaultdict(set)
        
        for spo in spo_list:
            h_entity = spo["h"]
            t_entity = spo["t"]
            relation = spo["relation"]
            
            relation_tuple = (
                h_entity["name"], h_entity["pos"][0], h_entity["pos"][1],
                t_entity["name"], t_entity["pos"][0], t_entity["pos"][1]
            )
            relations[relation].add(relation_tuple)
        
        return relations
    
    def compute_metrics(self, gold_set: Set, pred_set: Set) -> Dict[str, float]:
        """
        计算评估指标
        
        Args:
            gold_set: 标准答案集合
            pred_set: 预测结果集合
            
        Returns:
            评估指标字典
        """
        tp = len(gold_set & pred_set)  # 正确预测的数量
        fp = len(pred_set - gold_set)  # 错误预测的数量
        fn = len(gold_set - pred_set)  # 漏掉的数量
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn
        }
    
    def evaluate_entities(self, gold_data: List[Dict], pred_data: List[Dict]) -> Dict[str, Dict]:
        """
        评估实体抽取性能
        
        Args:
            gold_data: 标准答案数据
            pred_data: 预测结果数据
            
        Returns:
            实体抽取评估结果
        """
        # 按实体类型分别评估
        entity_results = {}
        
        for entity_type in self.entity_types:
            gold_entities = set()
            pred_entities = set()
            
            for gold_item, pred_item in zip(gold_data, pred_data):
                # 提取标准答案中的实体
                gold_spo = gold_item.get("spo_list", [])
                gold_entity_dict = self.extract_entities_from_spo(gold_spo)
                gold_entities.update(gold_entity_dict.get(entity_type, set()))
                
                # 提取预测结果中的实体
                pred_spo = pred_item.get("spo_list", [])
                pred_entity_dict = self.extract_entities_from_spo(pred_spo)
                pred_entities.update(pred_entity_dict.get(entity_type, set()))
            
            # 计算指标
            entity_results[entity_type] = self.compute_metrics(gold_entities, pred_entities)
        
        # 计算总体指标
        all_gold_entities = set()
        all_pred_entities = set()
        
        for gold_item, pred_item in zip(gold_data, pred_data):
            gold_spo = gold_item.get("spo_list", [])
            gold_entity_dict = self.extract_entities_from_spo(gold_spo)
            for entities in gold_entity_dict.values():
                all_gold_entities.update(entities)
            
            pred_spo = pred_item.get("spo_list", [])
            pred_entity_dict = self.extract_entities_from_spo(pred_spo)
            for entities in pred_entity_dict.values():
                all_pred_entities.update(entities)
        
        entity_results["overall"] = self.compute_metrics(all_gold_entities, all_pred_entities)
        
        return entity_results
    
    def evaluate_relations(self, gold_data: List[Dict], pred_data: List[Dict]) -> Dict[str, Dict]:
        """
        评估关系抽取性能
        
        Args:
            gold_data: 标准答案数据
            pred_data: 预测结果数据
            
        Returns:
            关系抽取评估结果
        """
        # 按关系类型分别评估
        relation_results = {}
        
        for relation_type in self.relation_types:
            gold_relations = set()
            pred_relations = set()
            
            for gold_item, pred_item in zip(gold_data, pred_data):
                # 提取标准答案中的关系
                gold_spo = gold_item.get("spo_list", [])
                gold_relation_dict = self.extract_relations_from_spo(gold_spo)
                gold_relations.update(gold_relation_dict.get(relation_type, set()))
                
                # 提取预测结果中的关系
                pred_spo = pred_item.get("spo_list", [])
                pred_relation_dict = self.extract_relations_from_spo(pred_spo)
                pred_relations.update(pred_relation_dict.get(relation_type, set()))
            
            # 计算指标
            relation_results[relation_type] = self.compute_metrics(gold_relations, pred_relations)
        
        # 计算总体指标
        all_gold_relations = set()
        all_pred_relations = set()
        
        for gold_item, pred_item in zip(gold_data, pred_data):
            gold_spo = gold_item.get("spo_list", [])
            gold_relation_dict = self.extract_relations_from_spo(gold_spo)
            for relations in gold_relation_dict.values():
                all_gold_relations.update(relations)
            
            pred_spo = pred_item.get("spo_list", [])
            pred_relation_dict = self.extract_relations_from_spo(pred_spo)
            for relations in pred_relation_dict.values():
                all_pred_relations.update(relations)
        
        relation_results["overall"] = self.compute_metrics(all_gold_relations, all_pred_relations)
        
        return relation_results
    
    def print_results(self, entity_results: Dict, relation_results: Dict):
        """
        打印评估结果
        
        Args:
            entity_results: 实体抽取评估结果
            relation_results: 关系抽取评估结果
        """
        print("=" * 60)
        print("实体抽取评估结果:")
        print("=" * 60)
        print(f"{'类型':<12} {'Precision':<10} {'Recall':<10} {'F1':<10} {'TP':<6} {'FP':<6} {'FN':<6}")
        print("-" * 60)
        
        for entity_type, metrics in entity_results.items():
            print(f"{entity_type:<12} {metrics['precision']:<10.4f} {metrics['recall']:<10.4f} "
                  f"{metrics['f1']:<10.4f} {metrics['tp']:<6} {metrics['fp']:<6} {metrics['fn']:<6}")
        
        print("\n" + "=" * 60)
        print("关系抽取评估结果:")
        print("=" * 60)
        print(f"{'类型':<12} {'Precision':<10} {'Recall':<10} {'F1':<10} {'TP':<6} {'FP':<6} {'FN':<6}")
        print("-" * 60)
        
        for relation_type, metrics in relation_results.items():
            print(f"{relation_type:<12} {metrics['precision']:<10.4f} {metrics['recall']:<10.4f} "
                  f"{metrics['f1']:<10.4f} {metrics['tp']:<6} {metrics['fp']:<6} {metrics['fn']:<6}")
    
    def save_detailed_results(self, entity_results: Dict, relation_results: Dict, output_file: str):
        """
        保存详细的评估结果
        
        Args:
            entity_results: 实体抽取评估结果
            relation_results: 关系抽取评估结果
            output_file: 输出文件路径
        """
        results = {
            "entity_extraction": entity_results,
            "relation_extraction": relation_results,
            "summary": {
                "entity_overall_f1": entity_results["overall"]["f1"],
                "relation_overall_f1": relation_results["overall"]["f1"],
                "average_f1": (entity_results["overall"]["f1"] + relation_results["overall"]["f1"]) / 2
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细评估结果已保存到: {output_file}")


def run_evaluation_with_model(gold_file: str, model_path: str, device: str = "cpu") -> Tuple[Dict, Dict]:
    """
    使用模型对测试数据进行预测并评估
    
    Args:
        gold_file: 标准答案文件路径
        model_path: 模型路径
        device: 运行设备
        
    Returns:
        (实体抽取评估结果, 关系抽取评估结果)
    """
    # 加载标准答案数据
    evaluator = FaultEvaluator()
    gold_data = evaluator.load_gold_data(gold_file)
    
    # 初始化模型
    extractor = FaultDiagnosisUIE(model_path, device)
    
    # 对每个样本进行预测
    pred_data = []
    for gold_item in gold_data:
        text = gold_item["text"]
        
        # 使用模型进行预测
        spo_list = extractor.extract_with_spo_format(text)
        
        pred_item = {
            "ID": gold_item["ID"],
            "text": text,
            "spo_list": spo_list
        }
        pred_data.append(pred_item)
    
    # 进行评估
    entity_results = evaluator.evaluate_entities(gold_data, pred_data)
    relation_results = evaluator.evaluate_relations(gold_data, pred_data)
    
    return entity_results, relation_results


def run_evaluation_with_predictions(gold_file: str, pred_file: str) -> Tuple[Dict, Dict]:
    """
    使用已有的预测结果进行评估
    
    Args:
        gold_file: 标准答案文件路径
        pred_file: 预测结果文件路径
        
    Returns:
        (实体抽取评估结果, 关系抽取评估结果)
    """
    evaluator = FaultEvaluator()
    
    # 加载数据
    gold_data = evaluator.load_gold_data(gold_file)
    pred_data = evaluator.load_gold_data(pred_file)
    
    # 确保数据长度一致
    if len(gold_data) != len(pred_data):
        print(f"警告: 标准答案数据长度 ({len(gold_data)}) 与预测结果数据长度 ({len(pred_data)}) 不一致")
        min_len = min(len(gold_data), len(pred_data))
        gold_data = gold_data[:min_len]
        pred_data = pred_data[:min_len]
    
    # 进行评估
    entity_results = evaluator.evaluate_entities(gold_data, pred_data)
    relation_results = evaluator.evaluate_relations(gold_data, pred_data)
    
    return entity_results, relation_results


def main():
    parser = argparse.ArgumentParser(description="故障诊断信息抽取评估工具")
    parser.add_argument("--gold_file", type=str, required=True, help="标准答案文件路径")
    parser.add_argument("--pred_file", type=str, help="预测结果文件路径")
    parser.add_argument("--model_path", type=str, help="模型路径（用于直接预测）")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu", help="运行设备")
    parser.add_argument("--output_file", type=str, help="详细结果输出文件路径")
    
    args = parser.parse_args()
    
    if args.pred_file:
        # 使用已有预测结果进行评估
        print(f"使用预测结果文件进行评估: {args.pred_file}")
        entity_results, relation_results = run_evaluation_with_predictions(
            args.gold_file, args.pred_file
        )
    elif args.model_path:
        # 使用模型进行预测并评估
        print(f"使用模型进行预测并评估: {args.model_path}")
        entity_results, relation_results = run_evaluation_with_model(
            args.gold_file, args.model_path, args.device
        )
    else:
        print("错误: 必须指定 --pred_file 或 --model_path 中的一个")
        return
    
    # 创建评估器并打印结果
    evaluator = FaultEvaluator()
    evaluator.print_results(entity_results, relation_results)
    
    # 保存详细结果
    if args.output_file:
        evaluator.save_detailed_results(entity_results, relation_results, args.output_file)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("评估总结:")
    print("=" * 60)
    print(f"实体抽取总体F1: {entity_results['overall']['f1']:.4f}")
    print(f"关系抽取总体F1: {relation_results['overall']['f1']:.4f}")
    print(f"平均F1: {(entity_results['overall']['f1'] + relation_results['overall']['f1']) / 2:.4f}")


if __name__ == "__main__":
    main()