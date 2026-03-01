# Career Planning AI Agent - Backend

基于 FastAPI 的后端服务，为大学生职业规划智能体提供 API 支持。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

必需配置：
- `GLM_API_KEY`: 智谱 AI API 密钥
- `NEO4J_PASSWORD`: Neo4j 数据库密码

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

## 项目结构

```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── services/     # 业务服务
│   ├── utils/        # 工具函数
│   ├── main.py       # 应用入口
│   └── config.py     # 配置管理
├── scripts/          # 脚本工具
├── tests/            # 测试代码
└── requirements.txt  # Python 依赖
```

## 技术栈

- **框架**: FastAPI
- **LLM**: 智谱 GLM-5
- **向量数据库**: Chroma (localhost:8000)
- **图数据库**: Neo4j (localhost:7474, 数据库：career_planning)

## 开发命令

```bash
# 运行测试
pytest

# 代码检查
flake8 app/

# 类型检查
mypy app/
```
