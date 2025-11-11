"""数据库模型定义.

定义请求日志等数据库表的 ORM 模型。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RequestLog(Base):
    """请求日志表模型."""

    __tablename__ = 'request_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    request_id = Column(String(64), nullable=False, unique=True, index=True, comment='请求ID')
    input_type = Column(String(32), nullable=False, comment='输入类型: html_content, url, file')
    input_html = Column(Text, nullable=True, comment='输入HTML字符串')
    url = Column(Text, nullable=True, comment='输入URL地址')
    output_markdown = Column(Text, nullable=True, comment='输出Markdown内容')
    status = Column(String(32), default='processing', nullable=False, comment='状态: processing-处理中, success-成功, fail-失败')
    error_message = Column(Text, nullable=True, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment='更新时间')

    def __repr__(self):
        return f"<RequestLog(id={self.id}, request_id={self.request_id}, status={self.status})>"
