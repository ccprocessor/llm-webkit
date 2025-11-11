# 数据库配置说明

## 功能概述

本项目新增了 MySQL 请求日志功能，用于记录每次 HTML 解析请求的详细信息，包括：

- **任务ID** (`task_id`): 用于关联同一任务的多个请求
- **请求ID** (`request_id`): 每次请求的唯一标识符（自动生成UUID）
- **输入类型** (`input_type`): html_content（HTML字符串）、url（URL地址）、file（文件上传）
- **输入HTML** (`input_html`): 输入的HTML字符串内容
- **URL** (`url`): 输入的URL地址
- **输出Markdown** (`output_markdown`): 解析后输出的Markdown格式内容
- **成功状态** (`is_success`): 请求是否成功
- **错误信息** (`error_message`): 失败时的详细错误信息
- **创建时间** (`created_at`): 请求创建时间
- **更新时间** (`updated_at`): 记录最后更新时间

## 数据库设置

### 1. 安装 MySQL

确保已安装 MySQL 5.7+ 或 MariaDB 10.2+。

### 2. 创建数据库和表

执行 `database_setup.sql` 文件中的 SQL 语句：

```bash
mysql -u root -p < database_setup.sql
```

或者登录 MySQL 后执行：

```sql
source /path/to/database_setup.sql;
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接：

```env
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/llm_web_kit
```

**连接字符串格式说明：**

```
mysql+aiomysql://用户名:密码@主机:端口/数据库名
```

**示例：**

- 本地开发: `mysql+aiomysql://root:123456@localhost:3306/llm_web_kit`
- 远程服务器: `mysql+aiomysql://user:pass@192.168.1.100:3306/llm_web_kit`

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包括：

- `sqlalchemy>=2.0.0` - ORM框架
- `aiomysql>=0.2.0` - 异步MySQL驱动
- `pymysql>=1.1.0` - MySQL客户端库

## 使用说明

### 启动服务

```bash
python llm_web_kit/api/run_server.py
```

或者：

```bash
python -m llm_web_kit.api.main
```

### API 调用示例

#### 1. 解析 HTML 内容

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/html/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html><body><h1>Hello World</h1></body></html>",
    "url": "https://example.com",
    "options": {
      "task_id": "task_001",
      "clean_html": true
    }
  }'
```

**响应示例：**

```json
{
  "success": true,
  "message": "HTML 解析成功",
  "timestamp": "2025-10-27T15:30:00.123456",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "markdown": "# Hello World",
    ...
  }
}
```

#### 2. 上传 HTML 文件

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/html/upload" \
  -F "file=@/path/to/file.html"
```

### 传递任务ID

如果需要关联多个请求到同一任务，可以在 `options` 中传递 `task_id`：

```json
{
  "html_content": "...",
  "options": {
    "task_id": "my_task_123"
  }
}
```

## 数据库查询示例

### 查询最近的请求记录

```sql
SELECT * FROM request_logs
ORDER BY created_at DESC
LIMIT 100;
```

### 查询某个任务的所有请求

```sql
SELECT * FROM request_logs
WHERE task_id = 'task_001'
ORDER BY created_at;
```

### 查询失败的请求

```sql
SELECT request_id, input_type, error_message, created_at
FROM request_logs
WHERE is_success = 0
ORDER BY created_at DESC;
```

### 统计成功率

```sql
SELECT
    COUNT(*) as total_requests,
    SUM(is_success) as success_count,
    ROUND(SUM(is_success) / COUNT(*) * 100, 2) as success_rate
FROM request_logs;
```

### 按日期统计请求量

```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as total,
    SUM(is_success) as success,
    COUNT(*) - SUM(is_success) as failed
FROM request_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 查询特定请求的详细信息

```sql
SELECT * FROM request_logs
WHERE request_id = '550e8400-e29b-41d4-a716-446655440000';
```

## 功能特性

### 1. 自动日志记录

每次调用 `/api/v1/html/parse` 或 `/api/v1/html/upload` 接口时，系统会自动：

- 生成唯一的 `request_id`
- 记录请求开始时间
- 保存输入参数（HTML内容、URL等）
- 记录解析结果（Markdown输出）
- 记录成功/失败状态和错误信息

### 2. 异步数据库操作

使用 SQLAlchemy 异步引擎和 aiomysql 驱动，不会阻塞 API 请求处理。

### 3. 优雅降级

如果数据库未配置或连接失败：

- API 服务仍然正常运行
- 只是不记录请求日志
- 不影响 HTML 解析功能

### 4. 连接池管理

使用数据库连接池，提高性能：

- 默认池大小: 5
- 最大溢出: 10
- 可通过环境变量配置

## 故障排查

### 问题1: 数据库连接失败

**错误信息：**

```
数据库连接初始化失败: (2003, "Can't connect to MySQL server...")
```

**解决方案：**

1. 检查 MySQL 服务是否运行
2. 验证 `DATABASE_URL` 配置是否正确
3. 确认数据库用户权限
4. 检查防火墙设置

### 问题2: 表不存在

**错误信息：**

```
Table 'llm_web_kit.request_logs' doesn't exist
```

**解决方案：**
执行 `database_setup.sql` 创建表：

```bash
mysql -u root -p llm_web_kit < database_setup.sql
```

### 问题3: 依赖包缺失

**错误信息：**

```
ModuleNotFoundError: No module named 'aiomysql'
```

**解决方案：**
安装依赖包：

```bash
pip install sqlalchemy aiomysql pymysql
```

### 问题4: 字符编码问题

**解决方案：**
确保数据库和表使用 `utf8mb4` 字符集：

```sql
ALTER DATABASE llm_web_kit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE request_logs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 性能优化建议

### 1. 定期清理历史数据

```sql
-- 删除30天前的日志
DELETE FROM request_logs
WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 2. 添加分区表（可选）

对于大量数据，可以按月分区：

```sql
ALTER TABLE request_logs
PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    ...
);
```

### 3. 监控慢查询

启用 MySQL 慢查询日志，优化查询性能。

### 4. 调整连接池大小

根据并发量调整 `.env` 中的配置：

```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## 安全建议

1. **不要提交 .env 文件到版本控制**
2. **使用强密码**
3. **限制数据库用户权限**（只授予必要的权限）
4. **定期备份数据库**
5. **在生产环境使用 SSL 连接**

## 技术架构

```
FastAPI Application
    ↓
Router (htmls.py)
    ↓
RequestLogService (request_log_service.py)
    ↓
DatabaseManager (database.py)
    ↓
SQLAlchemy + aiomysql
    ↓
MySQL Database
```

## 相关文件

- `models/db_models.py` - 数据库模型定义
- `database.py` - 数据库连接管理
- `services/request_log_service.py` - 请求日志服务
- `routers/htmls.py` - API 路由（集成日志记录）
- `database_setup.sql` - 数据库建表语句
- `.env.example` - 环境变量配置示例

## 联系支持

如有问题，请查看项目文档或提交 Issue。
