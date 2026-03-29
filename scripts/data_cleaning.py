"""
数据清洗脚本 - Phase 1: 数据清洗与处理
将原始Excel数据清洗为结构化JSON格式
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import json
import re
from pathlib import Path

# 常量定义
RAW_DATA_PATH = 'data/raw/20260226105856_457.xls'
PROCESSED_DIR = 'data/processed/'
JOBS_CLEANED_PATH = PROCESSED_DIR + 'jobs_cleaned.json'
DUPLICATES_PATH = PROCESSED_DIR + 'duplicates.json'
CLEANING_REPORT_PATH = PROCESSED_DIR + 'cleaning_report.json'


def load_raw_data():
    """加载原始Excel数据"""
    print(f"Loading raw data from {RAW_DATA_PATH}...")
    df = pd.read_excel(RAW_DATA_PATH, engine='xlrd')
    print(f"Loaded {len(df)} records with {len(df.columns)} columns")
    return df


def save_cleaned_data(df, filepath):
    """保存清洗后的数据为JSON"""
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = df.to_dict('records')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(records)} records to {filepath}")


def analyze_data(df):
    """分析数据结构"""
    print("\n" + "="*60)
    print("数据字段分析")
    print("="*60)

    print("\n列名:")
    print(df.columns.tolist())

    print(f"\n记录数: {len(df)}")

    print("\n前3条样本:")
    print(df.head(3).to_string())

    print("\n缺失值统计:")
    print(df.isnull().sum())

    print("\n薪资范围样本 (前5个):")
    salary_samples = df['薪资范围'].dropna().unique()[:5]
    for s in salary_samples:
        print(f"  - {s}")

    print("\n地址样本 (前5个):")
    addr_samples = df['地址'].dropna().unique()[:5]
    for a in addr_samples:
        print(f"  - {a}")


if __name__ == '__main__':
    # 加载并分析数据
    df = load_raw_data()
    analyze_data(df)
