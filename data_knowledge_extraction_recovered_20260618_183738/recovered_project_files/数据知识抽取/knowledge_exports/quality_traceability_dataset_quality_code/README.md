# 品质异常溯源建模数据集

本目录将连铸原始数据重新整理为建模友好的 X/y 结构。

## 文件

- `X_process_features.csv`: 生产工艺参数合集 X。第一列 `record_id` 用于和 y 对齐，其余列为数值型工艺特征。
- `y_quality_abnormal.csv`: 品质异常标签 y，包含主异常大类、中文标签、原始异常代码集合和多标签 one-hot。
- `y_quality_label.csv`: 兼容旧版 KIEP-GL 脚本的标签表，内容同 `y_quality_abnormal.csv`。
- `xy_quality_traceability.csv`: 元数据 + y + X 的统筹宽表，便于直接分析和建模。
- `auxiliary_quality_events.csv`: 过渡/状态类辅助样本。
- `invalid_data_quality_rows.csv`: 全特征缺失等不适合建模的记录。
- `feature_groups.json`: X 特征按工艺模块分组。
- `label_mapping.json`: 品质异常代码到异常大类的映射。
- `dataset_summary.json`: 行数、特征数、标签分布和输出清单。

## 建议用法

优先用 `quality_abnormal_group` / `quality_abnormal_group_cn` 做单标签主任务；
若一条记录有多个异常大类，用 `quality_group_*` 列做多标签溯源。
