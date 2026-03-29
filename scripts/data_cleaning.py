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


# ============================================================
# Task 1.3: 薪资标准化
# ============================================================
def normalize_salary(salary_str):
    """Convert salary to monthly (x12) format.
    Returns (min_monthly, max_monthly) or None if unparseable.
    """
    if pd.isna(salary_str):
        return None, None

    salary_str = str(salary_str).strip()

    # Handle negotiable and empty
    if salary_str in ['面议', '', '未知', '工资面议']:
        return None, None

    # Strip year-end bonus suffix like "·13薪" or "·14薪" or "13薪" etc.
    salary_str = re.sub(r'·?\d* ?薪$', '', salary_str)

    # Pattern: "8000-12000元" or "8000~12000元" or "8000-12000" (plain monthly range)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*元?$', salary_str)
    if match:
        return float(match.group(1)), float(match.group(2))

    # Pattern: "8000元" or "8000" (plain monthly)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*元$', salary_str)
    if match:
        return float(match.group(1)), float(match.group(1))

    # Pattern: "120-150元/天" (range daily rate)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*元\s*/\s*天$', salary_str)
    if match:
        daily_min = float(match.group(1))
        daily_max = float(match.group(2))
        return daily_min * 22, daily_max * 22

    # Pattern: "10000元/天" or "10000/天" (single daily rate)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:元)?\s*/\s*天$', salary_str)
    if match:
        daily = float(match.group(1))
        monthly = daily * 22
        return monthly, monthly

    # Pattern: "1-1.5万" or "1-1.5万/年" (annual in wan)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*万(?:\s*/年)?$', salary_str)
    if match:
        min_annual = float(match.group(1)) * 10000
        max_annual = float(match.group(2)) * 10000
        return min_annual / 12, max_annual / 12

    # Pattern: "4.5万" or "4.5万/年" (single wan value)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*万(?:\s*/年)?$', salary_str)
    if match:
        annual = float(match.group(1)) * 10000
        monthly = annual / 12
        return monthly, monthly

    # Pattern: "1000元以下" (below X yuan)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*元\s*以下$', salary_str)
    if match:
        max_monthly = float(match.group(1))
        return None, max_monthly

    return None, None


# ============================================================
# Task 1.4: 地址拆分
# ============================================================
def split_address(address_str):
    """Split address into city and district.
    Returns (city, district) tuple.
    """
    if pd.isna(address_str) or address_str.strip() == '':
        return None, None

    address_str = str(address_str).strip()

    # Pattern: "城市-区域" or "城市-区域-详细"
    if '-' in address_str:
        parts = address_str.split('-', 1)
        city = parts[0].strip()
        district = parts[1].strip() if len(parts) > 1 else None
        # Handle "None" string from raw data
        if district and district.lower() != 'none':
            return city, district
        return city, None

    # No dash: entire string is city
    return address_str, None


# ============================================================
# Task 1.5: 公司规模映射
# ============================================================
def normalize_company_size(size_str):
    """Map company size to numeric range.
    Returns (min_size, max_size) or (None, None) if unparseable.
    """
    if pd.isna(size_str) or size_str in ['面议', '', '未知']:
        return None, None

    size_str = str(size_str).strip()

    # Pattern: "20-99人" or "1000-9999人"
    match = re.match(r'^(\d+)\s*[-~]\s*(\d+)\s*人$', size_str)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Pattern: "少于20人"
    match = re.match(r'^少于\s*(\d+)\s*人$', size_str)
    if match:
        return 0, int(match.group(1)) - 1

    # Pattern: "10000人以上"
    match = re.match(r'^(\d+)\s*人以上?$', size_str)
    if match:
        return int(match.group(1)), None

    return None, None


# ============================================================
# Task 1.6: 行业分类提取
# ============================================================
def extract_industry_tags(industry_str):
    """Extract industry tags from comma-separated string.
    Returns (tags_list, primary_industry) tuple.
    """
    if pd.isna(industry_str) or industry_str.strip() == '':
        return [], None

    tags = [t.strip() for t in str(industry_str).split(',') if t.strip()]
    primary = tags[0] if tags else None
    return tags, primary


# ============================================================
# Task 1.7: 去除HTML标签
# ============================================================
def remove_html_tags(text):
    """Remove HTML tags from text, convert common entities."""
    if pd.isna(text):
        return None

    text = str(text)

    # Replace common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')

    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)

    # Collapse whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()

    return clean if clean else None


# ============================================================
# Task 1.8: 重复检测与去重
# ============================================================
def detect_duplicates(df):
    """Detect duplicate job codes, return (deduplicated_df, duplicates_list)."""
    duplicate_mask = df.duplicated(subset=['岗位编码'], keep='first')
    duplicates = df[duplicate_mask].to_dict('records')
    df_clean = df[~duplicate_mask].reset_index(drop=True)
    return df_clean, duplicates


# ============================================================
# Task 1.9: 生成清洗报告
# ============================================================
def generate_cleaning_report(df_input, df_output, duplicates_list, parsed_salary_count):
    """Generate cleaning report with quality metrics."""
    total_input = len(df_input)
    total_output = len(df_output)
    duplicate_count = len(duplicates_list)

    dataset_completeness_rate = (total_output / total_input * 100) if total_input > 0 else 0

    # Field fill rates for key normalized fields
    fields_to_check = [
        'salary_min_monthly', 'salary_max_monthly', 'city', 'district',
        'company_size_min', 'company_size_max', 'industry_tags', 'industry_primary',
        'job_detail_cleaned'
    ]
    field_fill_rates = {}
    for field in fields_to_check:
        if field in df_output.columns:
            non_null = df_output[field].notna().sum()
            # For list fields, count non-empty lists
            if field == 'industry_tags':
                non_null = df_output[field].apply(lambda x: bool(x) and len(x) > 0).sum()
            rate = (non_null / len(df_output) * 100) if len(df_output) > 0 else 0
            field_fill_rates[field] = round(rate, 2)

    salary_coverage = (parsed_salary_count / total_output * 100) if total_output > 0 else 0

    # Quality distribution based on job_detail_cleaned
    job_detail_col = df_output.get('job_detail_cleaned', pd.Series([None] * len(df_output)))
    complete_count = job_detail_col.notna().sum()
    incomplete_count = total_output - complete_count

    report = {
        "total_input_records": total_input,
        "total_output_records": total_output,
        "duplicate_count": duplicate_count,
        "dataset_completeness_rate": round(dataset_completeness_rate, 2),
        "field_fill_rates": field_fill_rates,
        "salary_standardization_coverage": round(salary_coverage, 2),
        "quality_distribution": {
            "complete": int(complete_count),
            "incomplete": int(incomplete_count)
        }
    }

    return report


# ============================================================
# Task 1.10: 完整清洗流程
# ============================================================
def run_cleaning_pipeline():
    """Execute the complete data cleaning pipeline."""
    print("="*60)
    print("开始数据清洗流程")
    print("="*60)

    # Step 1: Load raw data
    print("\n[1/6] 加载原始数据...")
    df = load_raw_data()
    df_original = df.copy()

    # Step 2: Apply salary normalization (Task 1.3)
    print("\n[2/6] 薪资标准化...")
    df['salary_min_monthly'], df['salary_max_monthly'] = zip(*df['薪资范围'].apply(normalize_salary))
    df['salary_original'] = df['薪资范围']
    salary_parsed = df['salary_min_monthly'].notna().sum()
    print(f"  成功解析薪资: {salary_parsed}/{len(df)} ({salary_parsed/len(df)*100:.1f}%)")

    # Step 3: Apply address splitting (Task 1.4)
    print("\n[3/6] 地址拆分...")
    df['city'], df['district'] = zip(*df['地址'].apply(split_address))
    df['address_original'] = df['地址']
    city_filled = df['city'].notna().sum()
    print(f"  城市填充: {city_filled}/{len(df)} ({city_filled/len(df)*100:.1f}%)")

    # Step 4: Apply company size mapping (Task 1.5)
    print("\n[4/6] 公司规模映射...")
    df['company_size_min'], df['company_size_max'] = zip(*df['公司规模'].apply(normalize_company_size))
    df['company_size_original'] = df['公司规模']
    size_filled = df['company_size_min'].notna().sum()
    print(f"  规模填充: {size_filled}/{len(df)} ({size_filled/len(df)*100:.1f}%)")

    # Step 5: Apply industry extraction (Task 1.6)
    print("\n[5/6] 行业分类提取...")
    df['industry_tags'], df['industry_primary'] = zip(*df['所属行业'].apply(extract_industry_tags))
    industry_filled = df['industry_primary'].notna().sum()
    print(f"  行业填充: {industry_filled}/{len(df)} ({industry_filled/len(df)*100:.1f}%)")

    # Step 6: Remove HTML tags (Task 1.7)
    print("\n[6/6] 去除HTML标签...")
    df['job_detail_cleaned'] = df['岗位详情'].apply(remove_html_tags)
    detail_filled = df['job_detail_cleaned'].notna().sum()
    print(f"  详情填充: {detail_filled}/{len(df)} ({detail_filled/len(df)*100:.1f}%)")

    # Mark records with missing job_detail as incomplete
    df['data_quality'] = df['job_detail_cleaned'].apply(lambda x: 'complete' if pd.notna(x) else 'incomplete')

    # Step 7: Detect duplicates (Task 1.8)
    print("\n检测重复职位编码...")
    df, duplicates_list = detect_duplicates(df)
    print(f"  发现 {len(duplicates_list)} 条重复记录")

    # Recalculate salary_parsed after deduplication for accurate coverage
    salary_parsed = df['salary_min_monthly'].notna().sum()

    # Step 8: Generate cleaning report (Task 1.9)
    print("\n生成清洗报告...")
    report = generate_cleaning_report(df_original, df, duplicates_list, salary_parsed)

    # Step 9: Save output files
    print("\n保存输出文件...")
    save_cleaned_data(df, JOBS_CLEANED_PATH)

    # Save duplicates
    with open(DUPLICATES_PATH, 'w', encoding='utf-8') as f:
        json.dump(duplicates_list, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(duplicates_list)} duplicate records to {DUPLICATES_PATH}")

    # Save cleaning report
    with open(CLEANING_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved cleaning report to {CLEANING_REPORT_PATH}")

    # Print summary
    print("\n" + "="*60)
    print("数据清洗完成")
    print("="*60)
    print(f"输入记录: {report['total_input_records']}")
    print(f"输出记录: {report['total_output_records']}")
    print(f"重复记录: {report['duplicate_count']}")
    print(f"数据集完整率: {report['dataset_completeness_rate']}%")
    print(f"薪资标准化覆盖率: {report['salary_standardization_coverage']}%")
    print(f"质量分布: {report['quality_distribution']}")

    return df, report


if __name__ == '__main__':
    df, report = run_cleaning_pipeline()
