---
wave: 1
depends_on: []
files_modified:
  - .planning/phases/01-data-cleaning/PLAN.md
autonomous: false
---

# Phase 1 Plan: 数据清洗与处理

## Goal (from ROADMAP.md)

将原始Excel数据（9958条）清洗为干净的结构化数据集

## Success Criteria

1. 数据集完整率≥99%（9958条中至少9857条可用）
2. 字段填充率≥95%（12个字段中缺失值比例≤5%）
3. 重复职位编码检测并去重
4. 薪资范围、地址、公司规模等字段标准化

## must_haves (goal-backward verification)

- [ ] `data/processed/jobs_cleaned.json` exists and contains ≥9857 records
- [ ] `data/processed/duplicates.json` exists (may be empty array if no duplicates)
- [ ] `data/processed/cleaning_report.json` exists with quality metrics
- [ ] Each record has: `salary_min_monthly`, `salary_max_monthly` (or `data_quality: "incomplete"`)
- [ ] Each record has: `city`, `district` (or district is null)
- [ ] Each record has: `company_size_min`, `company_size_max` (or original field)
- [ ] Each record has: `industry_tags` (list), `industry_primary`
- [ ] HTML tags removed from job details
- [ ] No duplicate `job_code` values in cleaned output

## Verification

```bash
# Check output files exist
ls -la data/processed/

# Count records
python -c "import json; d=json.load(open('data/processed/jobs_cleaned.json')); print(f'Records: {len(d)}')"

# Verify quality metrics
python -c "import json; d=json.load(open('data/processed/cleaning_report.json')); print(json.dumps(d, indent=2, ensure_ascii=False))"
```

---

## Task 1.1: 创建目录结构与清洗脚本

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-01 to D-12 implementation decisions
- `.planning/ROADMAP.md` — Phase 1 success criteria
</read_first>

<acceptance_criteria>
- [ ] `data/raw/` directory created (holds original .xls file)
- [ ] `data/processed/` directory created (holds output files)
- [ ] `scripts/data_cleaning.py` script created with basic structure
- [ ] `scripts/data_cleaning.py` contains `import pandas`, `import json`, `import re`
- [ ] Script reads source file: `20260226105856_457.xls` from `data/raw/`
- [ ] Script outputs to `data/processed/`
</acceptance_criteria>

<action>
Create directory structure:
```
data/raw/
data/processed/
scripts/data_cleaning.py
```

Create `scripts/data_cleaning.py` with:
- Import statements: `pandas`, `json`, `re`
- Constants for file paths
- Function `load_raw_data()` that reads `data/raw/20260226105856_457.xls`
- Function `save_cleaned_data()` that writes JSON to `data/processed/`
- Basic structure for subsequent task functions
</action>

---

## Task 1.2: 读取原始数据并分析字段结构

<read_first>
- `C:/Users/Administrator/Desktop/职引未来/20260226105856_457.xls` — raw data file
</read_first>

<acceptance_criteria>
- [ ] Script can load the .xls file successfully
- [ ] Output shows column names: 岗位名称, 地址, 薪资范围, 公司名称, 所属行业, 公司规模, 公司类型, 岗位编码, 岗位详情, 更新日期, 公司详情, 岗位来源地址
- [ ] Output shows record count: 9958
- [ ] Output shows sample values for each field (first 3 rows)
- [ ] Missing value counts per column displayed
- [ ] Unique salary formats identified (sample at least 5 patterns)
- [ ] Unique address formats identified (sample at least 5 patterns)
</acceptance_criteria>

<action>
Extend `scripts/data_cleaning.py`:

1. In `load_raw_data()`: Read Excel file using `pandas.read_excel('data/raw/20260226105856_457.xls', engine='xlrd')`

2. Add analysis function `analyze_data(df)` that:
   - Prints `df.columns.tolist()` — verify 12 columns
   - Prints `len(df)` — expect 9958
   - Prints first 3 rows as sample
   - Prints `df.isnull().sum()` — missing value counts per column
   - Prints `df['薪资范围'].dropna().unique()[:5]` — sample salary patterns
   - Prints `df['地址'].dropna().unique()[:5]` — sample address patterns

3. Copy raw file to `data/raw/` directory

Run script to verify data loads correctly.
</action>

---

## Task 1.3: 实现薪资标准化

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-02 salary standardization rules
- `scripts/data_cleaning.py` — current state of cleaning script
</read_first>

<acceptance_criteria>
- [ ] `normalize_salary(salary_str)` function exists in script
- [ ] Function handles: "8000-12000" → returns (8000, 12000) monthly
- [ ] Function handles: "8000" → returns (8000, 8000) monthly
- [ ] Function handles: "10000元/天" → returns (264000, 264000) monthly (10000×22×12)
- [ ] Function handles: "10-15万/年" → returns (100000, 150000) monthly (divide by 12)
- [ ] Function handles: "面议" → returns None
- [ ] Function handles: "" (empty) → returns None
- [ ] Function handles: null → returns None
- [ ] Adds `salary_min_monthly`, `salary_max_monthly` columns to dataframe
- [ ] Adds `salary_original` column preserving original text
- [ ] Salary standardization coverage ≥95% logged in report
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
def normalize_salary(salary_str):
    """Convert salary to monthly (×12) format.
    Returns (min_monthly, max_monthly) or None if unparseable.
    """
    if pd.isna(salary_str) or salary_str in ['面议', '', '未知']:
        return None, None

    salary_str = str(salary_str).strip()

    # Pattern: "8000-12000" or "8000~12000" (plain monthly range)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)$', salary_str)
    if match:
        return float(match.group(1)), float(match.group(2))

    # Pattern: "10000元/天" or "10000/天"
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(?:元)?/天$', salary_str)
    if match:
        daily = float(match.group(1))
        monthly = daily * 22
        return monthly, monthly

    # Pattern: "10-15万/年" or "10-15万" (annual in 万)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*万\s*(?:/年)?$', salary_str)
    if match:
        min_annual = float(match.group(1)) * 10000
        max_annual = float(match.group(2)) * 10000
        return min_annual / 12, max_annual / 12

    # Pattern: "10万/年" or "10万"
    match = re.match(r'^(\d+(?:\.\d+)?)\s*万\s*(?:/年)?$', salary_str)
    if match:
        annual = float(match.group(1)) * 10000
        monthly = annual / 12
        return monthly, monthly

    # Pattern: "8000元" or "8000" (plain monthly)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*元?$', salary_str)
    if match:
        return float(match.group(1)), float(match.group(1))

    return None, None
```

Apply in cleaning pipeline:
```python
df['salary_min_monthly'], df['salary_max_monthly'] = zip(*df['薪资范围'].apply(normalize_salary))
df['salary_original'] = df['薪资范围']
```
</action>

---

## Task 1.4: 实现地址拆分

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-06 address splitting rules
- `scripts/data_cleaning.py` — current state
</read_first>

<acceptance_criteria>
- [ ] `split_address(address_str)` function exists
- [ ] "东莞-虎门镇" → returns ("东莞", "虎门镇")
- [ ] "广州-天河区" → returns ("广州", "天河区")
- [ ] "深圳" → returns ("深圳", None)
- [ ] "" (empty) → returns (None, None)
- [ ] null → returns (None, None)
- [ ] Adds `city` and `district` columns
- [ ] Adds `address_original` column preserving original text
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
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
        return city, district

    # No dash: entire string is city
    return address_str, None
```

Apply in cleaning pipeline:
```python
df['city'], df['district'] = zip(*df['地址'].apply(split_address))
df['address_original'] = df['地址']
```
</action>

---

## Task 1.5: 实现公司规模映射

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-04 company size mapping rules
- `scripts/data_cleaning.py` — current state
</read_first>

<acceptance_criteria>
- [ ] `normalize_company_size(size_str)` function exists
- [ ] "20-99人" → returns (20, 99)
- [ ] "1000-9999人" → returns (1000, 9999)
- [ ] "少于20人" → returns (0, 19)
- [ ] "10000人以上" → returns (10000, None)
- [ ] "面议" → returns (None, None)
- [ ] "" (empty) → returns (None, None)
- [ ] null → returns (None, None)
- [ ] Adds `company_size_min`, `company_size_max` columns
- [ ] Adds `company_size_original` column preserving original text
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
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
```

Apply in cleaning pipeline:
```python
df['company_size_min'], df['company_size_max'] = zip(*df['公司规模'].apply(normalize_company_size))
df['company_size_original'] = df['公司规模']
```
</action>

---

## Task 1.6: 实现行业分类提取

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-05 industry classification rules
- `scripts/data_cleaning.py` — current state
</read_first>

<acceptance_criteria>
- [ ] `extract_industry_tags(industry_str)` function exists
- [ ] "计算机软件,互联网,IT服务" → returns (["计算机软件", "互联网", "IT服务"], "计算机软件")
- [ ] "计算机软件" → returns (["计算机软件"], "计算机软件")
- [ ] "" (empty) → returns ([], None)
- [ ] null → returns ([], None)
- [ ] Adds `industry_tags` column (list)
- [ ] Adds `industry_primary` column (first tag or None)
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
def extract_industry_tags(industry_str):
    """Extract industry tags from comma-separated string.
    Returns (tags_list, primary_industry) tuple.
    """
    if pd.isna(industry_str) or industry_str.strip() == '':
        return [], None

    tags = [t.strip() for t in str(industry_str).split(',') if t.strip()]
    primary = tags[0] if tags else None
    return tags, primary
```

Apply in cleaning pipeline:
```python
df['industry_tags'], df['industry_primary'] = zip(*df['所属行业'].apply(extract_industry_tags))
```
</action>

---

## Task 1.7: 去除HTML标签

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-07 HTML removal rule
- `scripts/data_cleaning.py` — current state
</read_first>

<acceptance_criteria>
- [ ] `remove_html_tags(text)` function exists
- [ ] "<br>岗位要求<br>熟悉Python</br>" → returns "岗位要求熟悉Python"
- [ ] "<p>内容</p>" → returns "内容"
- [ ] "&nbsp;" → returns " "
- [ ] "普通文本" → returns "普通文本" unchanged
- [ ] null → returns null (no change)
- [ ] Adds `job_detail_cleaned` column with HTML removed
- [ ] Preserves original `岗位详情` column
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
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
```

Apply in cleaning pipeline:
```python
df['job_detail_cleaned'] = df['岗位详情'].apply(remove_html_tags)
```
</action>

---

## Task 1.8: 实现重复检测与去重

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-08 deduplication rules
- `scripts/data_cleaning.py` — current state
</read_first>

<acceptance_criteria>
- [ ] Deduplication based on `岗位编码` (job_code)
- [ ] First occurrence kept, subsequent duplicates logged
- [ ] `duplicates.json` contains array of duplicate records (original records)
- [ ] Cleaned data has no duplicate `job_code` values
- [ ] Duplicate count printed in output
- [ ] Empty array `[]` written if no duplicates found
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
def detect_duplicates(df):
    """Detect duplicate job codes, return (deduplicated_df, duplicates_list)."""
    duplicate_mask = df.duplicated(subset=['岗位编码'], keep='first')
    duplicates = df[duplicate_mask].to_dict('records')
    df_clean = df[~duplicate_mask].reset_index(drop=True)
    return df_clean, duplicates
```

In cleaning pipeline:
```python
df, duplicates_list = detect_duplicates(df)
print(f"Found {len(duplicates_list)} duplicate records")
```
</action>

---

## Task 1.9: 生成清洗报告

<read_first>
- `.planning/phases/01-data-cleaning/01-CONTEXT.md` — D-09, D-10, D-11, D-12 output specs
- `scripts/data_cleaning.py` — current state
</read_first>

<acceptance_criteria>
- [ ] `cleaning_report.json` created with structure:
  ```json
  {
    "total_input_records": 9958,
    "total_output_records": <number>,
    "duplicate_count": <number>,
    "dataset_completeness_rate": <float>,
    "field_fill_rates": {
      "salary_min_monthly": <float>,
      "city": <float>,
      ...
    },
    "salary_standardization_coverage": <float>,
    "quality_distribution": {
      "complete": <count>,
      "incomplete": <count>
    }
  }
  ```
- [ ] dataset_completeness_rate = output_records / input_records × 100%
- [ ] field_fill_rate per field = non_null / total × 100%
- [ ] salary_standardization_coverage = records with parsed salary / total × 100%
- [ ] Records with missing job_detail marked as `"data_quality": "incomplete"`
- [ ] All 3 output files written to `data/processed/`
</acceptance_criteria>

<action>
Add to `scripts/data_cleaning.py`:

```python
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

    # Quality distribution
    complete_count = len(df_output[df_output.get('job_detail_cleaned', pd.Series()).notna()])
    incomplete_count = total_output - complete_count

    report = {
        "total_input_records": total_input,
        "total_output_records": total_output,
        "duplicate_count": duplicate_count,
        "dataset_completeness_rate": round(dataset_completeness_rate, 2),
        "field_fill_rates": field_fill_rates,
        "salary_standardization_coverage": round(salary_coverage, 2),
        "quality_distribution": {
            "complete": complete_count,
            "incomplete": incomplete_count
        }
    }

    return report
```

Apply in cleaning pipeline after all transformations:
```python
# Count records with successfully parsed salary
parsed_salary_count = df['salary_min_monthly'].notna().sum()

report = generate_cleaning_report(df_original, df, duplicates_list, parsed_salary_count)

with open('data/processed/cleaning_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
```
</action>

---

## Task 1.10: 执行完整清洗流程并验证

<read_first>
- `scripts/data_cleaning.py` — final script
- `data/processed/jobs_cleaned.json` — output
- `data/processed/duplicates.json` — output
- `data/processed/cleaning_report.json` — output
</read_first>

<acceptance_criteria>
- [ ] `python scripts/data_cleaning.py` exits with code 0 (no errors)
- [ ] `data/processed/jobs_cleaned.json` contains ≥9857 records
- [ ] `data/processed/duplicates.json` is valid JSON (array)
- [ ] `data/processed/cleaning_report.json` is valid JSON
- [ ] Report shows `dataset_completeness_rate` ≥ 99.0
- [ ] Report shows all `field_fill_rates` ≥ 95.0
- [ ] Report shows `salary_standardization_coverage` ≥ 95.0
- [ ] No duplicate `job_code` in cleaned output (verify with code)
- [ ] Sample 3 records from cleaned output show all normalized fields present
</acceptance_criteria>

<action>
Final integration - ensure `scripts/data_cleaning.py` has complete pipeline:

1. Load raw data
2. Apply all normalizations in order:
   - Salary normalization
   - Address splitting
   - Company size mapping
   - Industry tag extraction
   - HTML removal
3. Mark records with missing job_detail as `data_quality: "incomplete"`
4. Deduplicate by job_code
5. Generate cleaning report
6. Save all 3 output files

Run verification commands:
```bash
python scripts/data_cleaning.py
python -c "import json; d=json.load(open('data/processed/jobs_cleaned.json')); print(f'Records: {len(d)}')"
python -c "import json; r=json.load(open('data/processed/cleaning_report.json')); print(f'Completeness: {r[\"dataset_completeness_rate\"]}%')"
```

Verify must_haves are all satisfied.
</action>

---

## Output Files

After successful execution:
- `data/processed/jobs_cleaned.json` — cleaned job records (JSON array)
- `data/processed/duplicates.json` — duplicate records (JSON array)
- `data/processed/cleaning_report.json` — quality metrics (JSON object)
