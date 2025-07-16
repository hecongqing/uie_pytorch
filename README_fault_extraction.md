# 故障案例信息抽取系统

基于UIE（Universal Information Extraction）的工业制造领域故障案例信息抽取系统，能够从故障案例文本中自动抽取部件单元、性能表征、故障状态、检测工具等实体及其关系。

## 功能特点

- **多类型实体抽取**：支持抽取部件单元、性能表征、故障状态、检测工具四种实体类型
- **关系抽取**：支持抽取部件故障、性能故障、检测工具、组成四种关系类型
- **零样本能力**：基于UIE模型，具备良好的零样本和少样本学习能力
- **完整流程**：提供数据预处理、模型训练、预测的完整解决方案
- **易于使用**：提供简单易用的命令行接口

## 系统架构

```
故障案例信息抽取系统
├── 数据预处理模块 (preprocess_fault_data.py)
├── 模型训练模块 (train_fault_extraction.py)
├── 预测模块 (predict_fault_extraction.py)
├── 完整流程脚本 (run_fault_extraction.py)
└── 示例数据 (sample_fault_data.json)
```

## 实体和关系定义

### 实体类型

| 实体类型 | 说明 | 示例 |
|---------|------|------|
| 部件单元 | 高端装备制造领域中的各种单元、零件、设备 | "燃油泵"、"换流变压器"、"分离器" |
| 性能表征 | 部件的特征或者性能描述 | "压力"、"转速"、"温度" |
| 故障状态 | 系统或部件的故障状态描述，多为故障类型 | "漏油"、"断裂"、"变形"、"卡滞" |
| 检测工具 | 用于检测某些故障的专用仪器 | "零序互感器"、"保护器"、"漏电测试仪" |

### 关系类型

| 主体 | 客体 | 关系 | 主体示例 | 客体示例 |
|------|------|------|----------|----------|
| 部件单元 | 故障状态 | 部件故障 | 发动机盖 | 抖动 |
| 性能表征 | 故障状态 | 性能故障 | 液面 | 变低 |
| 检测工具 | 性能表征 | 检测工具 | 漏电测试仪 | 电流 |
| 部件单元 | 部件单元 | 组成 | 断路器 | 换流变压器 |

## 安装依赖

```bash
# 安装基础依赖
pip install torch transformers numpy tqdm

# 安装UIE相关依赖
pip install -r requirements.txt
```

## 快速开始

### 1. 准备数据

数据格式为JSON格式，每行一个样本：

```json
{
    "ID": "AT0001",
    "text": "故障现象:车速到100迈以上发动机盖后部随着车速抖动。故障原因简要分析:经技术人员试车；怀疑发动机盖锁或发动机盖铰链松旷。",
    "spo_list": [
        {
            "h": {"name": "发动机盖", "pos": [14, 18]},
            "t": {"name": "抖动", "pos": [24, 26]},
            "relation": "部件故障"
        }
    ]
}
```

### 2. 运行完整流程

```bash
# 使用示例数据运行完整流程
python run_fault_extraction.py

# 使用自定义数据
python run_fault_extraction.py --input_file your_data.json

# 使用GPU训练
python run_fault_extraction.py --device gpu

# 调整训练参数
python run_fault_extraction.py --num_epochs 10 --batch_size 16 --learning_rate 2e-5
```

### 3. 分步骤运行

#### 数据预处理

```bash
python preprocess_fault_data.py \
    --input_file sample_fault_data.json \
    --output_dir ./data \
    --negative_ratio 3 \
    --splits 0.8 0.1 0.1
```

#### 模型训练

```bash
python train_fault_extraction.py \
    --train_path ./data/train.txt \
    --dev_path ./data/dev.txt \
    --config_file ./data/config.json \
    --model uie-base \
    --save_dir ./checkpoints \
    --num_epochs 10 \
    --batch_size 8 \
    --learning_rate 1e-5 \
    --device cpu
```

#### 模型预测

```bash
python predict_fault_extraction.py \
    --model_path ./checkpoints/model_best \
    --config_file ./data/config.json \
    --test_file ./data/test.txt \
    --output_file ./results/prediction_results.json \
    --device cpu \
    --verbose
```

## 参数说明

### 数据预处理参数

- `--input_file`: 输入数据文件路径
- `--output_dir`: 输出目录
- `--negative_ratio`: 负样本比例，默认为3
- `--splits`: 训练/验证/测试集比例，默认为[0.8, 0.1, 0.1]

### 训练参数

- `--train_path`: 训练数据路径
- `--dev_path`: 验证数据路径
- `--config_file`: 配置文件路径
- `--model`: 预训练模型，默认为uie-base
- `--save_dir`: 模型保存目录
- `--num_epochs`: 训练轮数，默认为10
- `--batch_size`: 批次大小，默认为16
- `--learning_rate`: 学习率，默认为1e-5
- `--device`: 设备类型，cpu或gpu
- `--early_stopping`: 是否使用早停机制

### 预测参数

- `--model_path`: 训练好的模型路径
- `--config_file`: 配置文件路径
- `--test_file`: 测试数据文件路径
- `--output_file`: 输出文件路径
- `--device`: 设备类型
- `--verbose`: 是否详细输出

## 输出格式

### 训练输出

训练过程中会输出：
- 训练损失
- 验证指标（精确率、召回率、F1值）
- 最佳模型保存路径

### 预测输出

预测结果格式：

```json
{
    "ID": "AE0001",
    "text": "燃油泵的作用是将燃油加压输送到喷油器...",
    "entities": {
        "部件单元": [
            {"text": "燃油泵", "start": 0, "end": 3, "probability": 0.95}
        ],
        "故障状态": [
            {"text": "损坏", "start": 15, "end": 17, "probability": 0.88}
        ]
    },
    "relations": [
        {"text": "加速不良", "start": 45, "end": 49, "probability": 0.92}
    ]
}
```

## 性能优化

### 1. 数据质量优化

- 确保标注数据的质量和一致性
- 增加负样本比例以提高模型鲁棒性
- 使用领域特定的实体类型判断规则

### 2. 模型优化

- 调整学习率和批次大小
- 使用早停机制避免过拟合
- 尝试不同的预训练模型（uie-base, uie-medium等）

### 3. 推理优化

- 使用GPU加速推理
- 调整position_prob阈值平衡精确率和召回率
- 使用批处理提高推理效率

## 常见问题

### Q1: 如何处理长文本？

A: 系统会自动将长文本分割成适合模型处理的片段，并在预测时合并结果。

### Q2: 如何提高抽取准确率？

A: 
1. 增加训练数据量
2. 优化实体类型判断规则
3. 调整模型超参数
4. 使用领域特定的预训练模型

### Q3: 如何添加新的实体类型？

A: 修改`preprocess_fault_data.py`中的`get_entity_type`函数，添加新的实体类型判断规则。

### Q4: 如何处理多语言数据？

A: 可以使用UIE-M系列模型，支持多语言信息抽取。

## 扩展功能

### 1. 自定义实体类型

在`preprocess_fault_data.py`中添加新的实体类型：

```python
def get_entity_type(entity_name: str) -> str:
    # 添加新的实体类型判断逻辑
    if "新实体关键词" in entity_name:
        return "新实体类型"
    # ... 其他逻辑
```

### 2. 自定义关系类型

在配置文件中添加新的关系类型：

```json
{
    "relation_types": ["部件故障", "性能故障", "检测工具", "组成", "新关系类型"]
}
```

### 3. 集成到现有系统

可以将训练好的模型集成到现有的故障诊断系统中，提供实时的信息抽取服务。

## 许可证

本项目基于Apache 2.0许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者