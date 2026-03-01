"""
Data Cleaning Script for Job Positions

Reads raw Excel data, cleans and standardizes it, then outputs to JSON format.

Usage:
    python scripts/clean_data.py --input data/raw/jobs_raw.xls --output data/processed/jobs.json
"""
import argparse
import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Any


def load_excel_data(input_path: str) -> pd.DataFrame:
    """Load data from Excel file"""
    print(f"Loading data from: {input_path}")
    df = pd.read_excel(input_path)
    print(f"Loaded {len(df)} rows")
    return df


def clean_salary(salary_str: str) -> Dict[str, float]:
    """
    Clean salary string and extract min/max values.
    Examples: "10-15K", "20-30K·14 薪", "100-150 元/天", "8-10 万"
    Returns: {"min": 10000, "max": 15000, "period": "month"}
    """
    if pd.isna(salary_str) or not salary_str:
        return {"min": 0, "max": 0, "period": "month"}

    salary_str = str(salary_str).strip()

    # Default period
    period = "month"

    # Extract numbers and units
    # Pattern for K (thousand)
    k_pattern = r'(\d+(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:\.\d+)?)\s*[KkK 千]'
    match = re.search(k_pattern, salary_str)
    if match:
        min_sal = float(match.group(1)) * 1000
        max_sal = float(match.group(2)) * 1000
        return {"min": min_sal, "max": max_sal, "period": "month"}

    # Pattern for 万 (ten thousand)
    wan_pattern = r'(\d+(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:\.\d+)?)\s*[万万]'
    match = re.search(wan_pattern, salary_str)
    if match:
        min_sal = float(match.group(1)) * 10000
        max_sal = float(match.group(2)) * 10000
        period = "year"
        if "月" in salary_str or "薪" in salary_str:
            period = "month"
        return {"min": min_sal, "max": max_sal, "period": period}

    # Pattern for simple range without unit (assume K)
    simple_pattern = r'(\d+)\s*[-~至到]\s*(\d+)'
    match = re.search(simple_pattern, salary_str)
    if match:
        min_sal = float(match.group(1))
        max_sal = float(match.group(2))
        # If numbers are small, assume K
        if max_sal < 1000:
            min_sal *= 1000
            max_sal *= 1000
        return {"min": min_sal, "max": max_sal, "period": "month"}

    return {"min": 0, "max": 0, "period": "month"}


def standardize_city(city: str) -> str:
    """
    Standardize city names.
    """
    if pd.isna(city) or not city:
        return "Unknown"

    city = str(city).strip()

    # Remove common suffixes
    city = re.sub(r'[市区县]+$', '', city)

    # Standardize common variations
    city_map = {
        "北京": "北京",
        "北京市": "北京",
        "上海": "上海",
        "上海市": "上海",
        "广州": "广州",
        "广州市": "广州",
        "深圳": "深圳",
        "深圳市": "深圳",
        "杭州": "杭州",
        "杭州市": "杭州",
        "成都": "成都",
        "成都市": "成都",
        "武汉": "武汉",
        "武汉市": "武汉",
        "西安": "西安",
        "西安市": "西安",
        "南京": "南京",
        "南京市": "南京",
    }

    return city_map.get(city, city)


def clean_job_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize job data"""

    print("Cleaning job data...")

    # Map corrupted column names to standard names
    # XLS file has encoding issues, map by column index
    col_mapping = {}
    if len(df.columns) >= 12:
        cols = list(df.columns)
        col_mapping = {
            cols[0]: 'job_name',         # 职位名称
            cols[1]: 'city',             # 地址
            cols[2]: 'salary',           # 薪资范围
            cols[3]: 'company',          # 公司全称
            cols[4]: 'industry',         # 所属行业
            cols[5]: 'company_size',     # 公司规模
            cols[6]: 'company_type',     # 公司性质
            cols[7]: 'job_code',         # 职位编码
            cols[8]: 'job_description',  # 职位描述
            cols[9]: 'publish_date',     # 发布时间
            cols[10]: 'company_intro',   # 公司简介
            cols[11]: 'job_url',         # 职位 URL
        }
        df = df.rename(columns=col_mapping)
        print(f"Mapped {len(col_mapping)} columns")

    # Standardize column names (remove spaces, convert to lowercase)
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

    # Remove duplicates
    initial_count = len(df)
    df = df.copy()  # Avoid SettingWithCopyWarning
    df = df.drop_duplicates()
    duplicates_removed = initial_count - len(df)
    print(f"Removed {duplicates_removed} duplicate rows")

    # Standardize city field
    city_columns = [col for col in df.columns if 'city' in col or '城市' in col or '地区' in col]
    if city_columns:
        city_col = city_columns[0]
        df.loc[:, city_col] = df[city_col].apply(standardize_city)
        print(f"Standardized city column: {city_col}")

    # Process salary field
    salary_columns = [col for col in df.columns if 'salary' in col or '薪资' in col or '工资' in col]
    if salary_columns:
        salary_col = salary_columns[0]
        df.loc[:, f'{salary_col}_raw'] = df[salary_col]
        salary_data = df[salary_col].apply(clean_salary)
        df.loc[:, 'salary_min'] = [s['min'] for s in salary_data]
        df.loc[:, 'salary_max'] = [s['max'] for s in salary_data]
        df.loc[:, 'salary_period'] = [s['period'] for s in salary_data]
        print(f"Processed salary column: {salary_col}")

    # Remove rows with missing critical fields
    critical_fields = [col for col in df.columns if 'job' in col or '职位' in col or 'name' in col]
    for field in critical_fields:
        if field in df.columns:
            missing_count = df[field].isna().sum()
            if missing_count > 0:
                print(f"Missing values in {field}: {missing_count}")

    return df


def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate cleaned data and return statistics"""
    stats = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "missing_values": {},
        "duplicates": int(df.duplicated().sum()),
    }

    # Check missing values in each column
    for col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            stats["missing_values"][col] = {
                "count": int(missing),
                "percentage": round(missing / len(df) * 100, 2)
            }

    return stats


def save_to_json(df: pd.DataFrame, output_path: str):
    """Save cleaned data to JSON file"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to list of dicts
    records = df.to_dict('records')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} records to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Clean job position data')
    parser.add_argument('--input', type=str, required=True, help='Input Excel file path')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file path')
    args = parser.parse_args()

    print("=" * 50)
    print("Job Data Cleaning Script")
    print("=" * 50)

    # Load data
    df = load_excel_data(args.input)

    # Show initial info
    print(f"\nInitial columns: {list(df.columns)}")
    print(f"\nTotal rows: {len(df)}")
    print(f"\nSample data (first row):")
    print(df.iloc[0].to_dict())

    # Clean data
    df_clean = clean_job_data(df)

    # Validate
    stats = validate_data(df_clean)
    print(f"\nData Statistics:")
    print(f"  Total rows: {stats['total_rows']}")
    print(f"  Duplicates: {stats['duplicates']}")
    if stats['missing_values']:
        print(f"  Missing values:")
        for col, info in stats['missing_values'].items():
            print(f"    - {col}: {info['count']} ({info['percentage']}%)")

    # Save to JSON
    save_to_json(df_clean, args.output)

    print("\n" + "=" * 50)
    print("Data cleaning completed!")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    exit(main())
