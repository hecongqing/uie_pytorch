# 工业制造领域故障诊断信息抽取系统

基于UIE（Universal Information Extraction）实现的工业制造领域故障诊断信息抽取系统，能够从故障案例文本中自动抽取实体和关系信息。

## 📋 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [数据格式](#数据格式)
- [使用说明](#使用说明)
- [模型训练](#模型训练)
- [性能评估](#性能评估)
- [示例](#示例)
- [常见问题](#常见问题)

## 🚀 功能特性

### 实体抽取
- **部件单元**: 高端装备制造领域中的各种单元、零件、设备
- **性能表征**: 部件的特征或者性能描述
- **故障状态**: 系统或部件的故障状态描述，多为故障类型
- **检测工具**: 用于检测某些故障的专用仪器

### 关系抽取
- **部件故障**: 部件单元 → 故障状态
- **性能故障**: 性能表征 → 故障状态  
- **检测工具**: 检测工具 → 性能表征
- **组成**: 部件单元 → 部件单元

## 💻 环境要求

```bash
Python >= 3.7
torch >= 1.10
transformers >= 4.18
numpy >= 1.22
tqdm
colorlog
```

## 🔧 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载模型

```bash
# 自动下载并转换UIE模型
python convert.py --model uie-base --save_dir ./uie-base
```

### 3. 运行演示

```bash
# 运行内置演示
python fault_diagnosis_uie.py --mode demo

# 交互式模式
python fault_diagnosis_uie.py --mode interactive
```

## 📊 数据格式

### 输入数据格式

故障案例数据采用JSON格式，每行一个样本：

```json
{
  "ID": "AT0001",
  "text": "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。",
  "spo_list": [
    {
      "h": {"name": "发动机盖", "pos": [14, 18]},
      "t": {"name": "抖动", "pos": [24, 26]},
      "relation": "部件故障"
    },
    {
      "h": {"name": "发动机盖锁", "pos": [46, 51]},
      "t": {"name": "松旷", "pos": [58, 60]},
      "relation": "部件故障"
    }
  ]
}
```

### 字段说明

- `ID`: 样本唯一标识符
- `text`: 故障案例文本内容
- `spo_list`: SPO三元组列表
  - `h`: 头实体（主体）
  - `t`: 尾实体（客体）
  - `relation`: 关系类型
  - `pos`: 实体在文本中的位置 [开始位置, 结束位置]

## 🎯 使用说明

### 基本使用

```python
from fault_diagnosis_uie import FaultDiagnosisUIE

# 初始化抽取器
extractor = FaultDiagnosisUIE(model_path="uie-base", device="cpu")

# 输入故障文本
text = "发动机出现异响，可能是轴承磨损造成的。"

# 抽取实体
entities = extractor.extract_entities(text)
print("实体:", entities)

# 抽取SPO三元组
spo_list = extractor.extract_with_spo_format(text)
print("关系:", spo_list)
```

### 命令行使用

#### 处理测试数据

```bash
python fault_diagnosis_uie.py \
    --mode process \
    --input_file test_data.json \
    --output_file results.json \
    --model_path uie-base \
    --device cpu
```

#### 交互式使用

```bash
python fault_diagnosis_uie.py --mode interactive
```

## 🏋️ 模型训练

### 1. 数据预处理

将原始故障案例数据转换为UIE训练格式：

```bash
python data_processor.py \
    --input_file sample_data.json \
    --output_dir ./processed_data \
    --format uie \
    --split_ratio 0.8
```

这将生成以下文件：
- `train_entity.txt`: 实体抽取训练数据
- `dev_entity.txt`: 实体抽取验证数据
- `train_relation.txt`: 关系抽取训练数据
- `dev_relation.txt`: 关系抽取验证数据

### 2. 模型微调

#### 实体抽取模型训练

```bash
python fault_finetune.py \
    --train_path ./processed_data/train_entity.txt \
    --dev_path ./processed_data/dev_entity.txt \
    --save_dir ./fault_entity_model \
    --model uie-base \
    --batch_size 16 \
    --num_epochs 20 \
    --learning_rate 1e-5 \
    --early_stopping \
    --device cpu
```

#### 关系抽取模型训练

```bash
python fault_finetune.py \
    --train_path ./processed_data/train_relation.txt \
    --dev_path ./processed_data/dev_relation.txt \
    --save_dir ./fault_relation_model \
    --model uie-base \
    --batch_size 16 \
    --num_epochs 20 \
    --learning_rate 1e-5 \
    --early_stopping \
    --device cpu
```

### 训练参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--train_path` | 训练数据路径 | - |
| `--dev_path` | 验证数据路径 | - |
| `--save_dir` | 模型保存目录 | ./fault_uie_model |
| `--model` | 预训练模型路径 | uie-base |
| `--batch_size` | 批次大小 | 16 |
| `--num_epochs` | 训练轮数 | 20 |
| `--learning_rate` | 学习率 | 1e-5 |
| `--max_seq_len` | 最大序列长度 | 512 |
| `--early_stopping` | 是否使用早停 | False |
| `--patience` | 早停耐心值 | 7 |
| `--device` | 运行设备 | cpu |

## 📈 性能评估

### 使用模型进行评估

```bash
python fault_evaluation.py \
    --gold_file test_data.json \
    --model_path ./fault_uie_model \
    --device cpu \
    --output_file evaluation_results.json
```

### 使用预测结果评估

```bash
python fault_evaluation.py \
    --gold_file test_data.json \
    --pred_file predictions.json \
    --output_file evaluation_results.json
```

### 评估指标

系统提供以下评估指标：

- **Precision（精确率）**: 预测正确的实体/关系占所有预测的比例
- **Recall（召回率）**: 预测正确的实体/关系占所有真实实体/关系的比例
- **F1-Score**: 精确率和召回率的调和平均数

## 📝 示例

### 示例1：基本实体抽取

```python
from fault_diagnosis_uie import FaultDiagnosisUIE

extractor = FaultDiagnosisUIE()
text = "发动机轴承温度过高，可能是润滑油不足导致的。"

entities = extractor.extract_entities(text)
# 输出: {
#   "部件单元": [{"text": "发动机轴承", "start": 0, "end": 5}],
#   "性能表征": [{"text": "温度", "start": 5, "end": 7}],
#   "故障状态": [{"text": "过高", "start": 7, "end": 9}]
# }
```

### 示例2：关系抽取

```python
spo_list = extractor.extract_with_spo_format(text)
# 输出: [
#   {
#     "h": {"name": "发动机轴承", "pos": [0, 5]},
#     "t": {"name": "过高", "pos": [7, 9]},
#     "relation": "部件故障"
#   }
# ]
```

### 示例3：批量处理

```python
# 处理多个文本
texts = [
    "燃油泵损坏导致发动机无法启动",
    "使用压力表检测液压系统压力",
    "变速箱由齿轮和离合器组成"
]

for text in texts:
    result = extractor.extract_comprehensive(text)
    print(f"文本: {text}")
    print(f"结果: {result}")
```

## ❓ 常见问题

### Q1: 如何提高抽取准确率？

**A**: 
1. 使用领域相关的训练数据进行模型微调
2. 调整position_prob阈值参数
3. 增加训练数据的多样性和质量
4. 根据具体业务场景调整关系判断逻辑

### Q2: 支持哪些预训练模型？

**A**: 
- `uie-base`: 基础UIE模型（推荐）
- `uie-medium`: 中等规模UIE模型
- `uie-mini`: 轻量级UIE模型
- `uie-micro`: 超轻量级UIE模型

### Q3: 如何处理长文本？

**A**: 
系统自动处理长文本分割，默认最大序列长度为512。可通过`max_seq_len`参数调整。

### Q4: GPU训练需要什么配置？

**A**: 
- 推荐：NVIDIA GPU with >= 8GB memory
- CUDA >= 10.1
- 设置`--device gpu`参数

### Q5: 如何自定义实体和关系类型？

**A**: 
修改`FaultDiagnosisUIE`类中的`entity_schema`和`relation_schema`定义，并相应调整数据处理逻辑。

## 📄 输出格式

### 实体抽取输出

```json
{
  "部件单元": [
    {"text": "发动机", "start": 0, "end": 3},
    {"text": "轴承", "start": 3, "end": 5}
  ],
  "故障状态": [
    {"text": "磨损", "start": 10, "end": 12}
  ]
}
```

### 关系抽取输出

```json
[
  {
    "h": {"name": "发动机", "pos": [0, 3]},
    "t": {"name": "磨损", "pos": [10, 12]},
    "relation": "部件故障"
  }
]
```

### 综合输出格式

```json
{
  "text": "输入文本",
  "entities": {/* 实体抽取结果 */},
  "relations": {/* 关系抽取结果 */}
}
```

## 🔍 性能优化建议

1. **数据质量**: 确保训练数据标注的准确性和一致性
2. **模型选择**: 根据计算资源选择合适大小的预训练模型
3. **参数调优**: 调整学习率、批次大小等超参数
4. **增量学习**: 利用新数据持续改进模型性能
5. **领域适应**: 针对特定工业领域进行专门的模型微调

## 📞 技术支持

如遇到问题或需要技术支持，请：

1. 查看本文档的常见问题部分
2. 检查日志输出中的错误信息
3. 验证输入数据格式是否正确
4. 确保所有依赖包正确安装

---

**祝您使用愉快！** 🎉