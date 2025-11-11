-- ============================================
-- LLM Web Kit API - 数据库建表语句
-- ============================================
-- 数据库: mineru_ai
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
-- ============================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS mineru_ai
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE mineru_ai;

-- ============================================
-- 请求日志表
-- ============================================
-- 用于记录每次 HTML 解析请求的详细信息
-- ============================================

DROP TABLE IF EXISTS `request_logs`;

CREATE TABLE `request_logs` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
    `request_id` VARCHAR(64) NOT NULL COMMENT '请求ID，每次请求的唯一标识符',
    `input_type` VARCHAR(32) NOT NULL COMMENT '输入类型: html_content(HTML字符串), url(URL地址), file(文件上传)',
    `input_html` LONGTEXT DEFAULT NULL COMMENT '输入的HTML字符串内容',
    `url` TEXT DEFAULT NULL COMMENT '输入的URL地址',
    `output_markdown` LONGTEXT DEFAULT NULL COMMENT '输出的Markdown格式内容',
    `status` VARCHAR(32) NOT NULL DEFAULT 'processing' COMMENT '状态: processing-处理中, success-成功, fail-失败',
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息，失败时记录详细错误',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_request_id` (`request_id`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='请求日志表';

-- ============================================
-- 索引说明
-- ============================================
-- 1. PRIMARY KEY (id): 主键索引，自增ID，用于快速定位记录
-- 2. UNIQUE KEY (request_id): 唯一索引，确保请求ID唯一性
-- 3. INDEX (created_at): 普通索引，用于按时间范围查询
-- 4. INDEX (status): 普通索引，用于按状态查询和统计
-- ============================================

-- ============================================
-- 示例查询语句
-- ============================================

-- 1. 查询最近100条请求记录
-- SELECT * FROM request_logs ORDER BY created_at DESC LIMIT 100;

-- 2. 查询处理中的请求
-- SELECT * FROM request_logs WHERE status = 'processing' ORDER BY created_at DESC;

-- 3. 查询失败的请求
-- SELECT * FROM request_logs WHERE status = 'fail' ORDER BY created_at DESC;

-- 4. 查询成功的请求
-- SELECT * FROM request_logs WHERE status = 'success' ORDER BY created_at DESC;

-- 5. 统计各状态的请求数量
-- SELECT
--     status,
--     COUNT(*) as count,
--     ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM request_logs), 2) as percentage
-- FROM request_logs
-- GROUP BY status;

-- 6. 按日期统计请求量
-- SELECT
--     DATE(created_at) as date,
--     COUNT(*) as total,
--     SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
--     SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failed,
--     SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing
-- FROM request_logs
-- GROUP BY DATE(created_at)
-- ORDER BY date DESC;

-- 7. 查询某个请求的详细信息
-- SELECT * FROM request_logs WHERE request_id = 'your_request_id';
