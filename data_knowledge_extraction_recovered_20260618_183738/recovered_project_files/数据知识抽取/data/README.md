# 数据目录

本目录存放软件系统搭建、数据处理和模型实验所需的数据文件。

## 目录约定

- `raw/`: 原始数据，只做归档和只读使用。
- `processed/`: 后续可放清洗后的中间数据。

## 当前原始数据

- `raw/baosteel_protection_slag_raw.csv`
  - 原始文件名：`4.9.1 001-宝钢保护渣数据集_原始.csv`
  - 用途：钢铁全流程生产异常预警溯源系统的数据处理入口。
  - 处理入口：`Scripts/continuous_casting_processing.py`

建议不要直接修改 `raw/` 下的原始文件；所有清洗、拆分、建模数据和系统演示数据应输出到 `knowledge_exports/`。
