"""响应数据模型.

定义 API 响应的数据结构和格式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """错误响应模型."""

    success: bool = Field(False, description="请求是否成功")
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误发生时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "HTML 解析失败",
                "detail": "无效的 HTML 格式",
                "timestamp": "2024-01-01T12:00:00"
            }
        }
    )


class BaseResponse(BaseModel):
    """基础响应模型."""

    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class HTMLParseData(BaseModel):
    """HTML 解析结果的结构化数据."""
    layout_file_list: List[str] = Field(default_factory=list, description="布局文件列表")
    typical_raw_html: Optional[str] = Field(None, description="原始 HTML")
    typical_raw_tag_html: Optional[str] = Field(None, description="带标签标注的原始 HTML")
    llm_response: Dict[str, int] = Field(default_factory=dict, description="LLM 项目打标结果")
    typical_main_html: Optional[str] = Field(None, description="解析得到的主体 HTML")
    html_target_list: List[Any] = Field(default_factory=list, description="正文候选/目标列表")
    markdown: Optional[str] = Field(None, description="从正文HTML提取的Markdown格式内容")


class HTMLParseResponse(BaseResponse):
    """HTML 解析响应模型."""

    data: Optional[HTMLParseData] = Field(None, description="解析结果数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据信息")
    request_id: Optional[str] = Field(None, description="请求ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "HTML 解析成功",
                "timestamp": "2025-08-26T16:45:43.140638",
                "data": {
                    "layout_file_list": [],
                    "typical_raw_html": "<html><body><h1>Hello World</h1></body></html>",
                    "typical_raw_tag_html": "<html><body><h1 _item_id=\"1\">Hello World</h1></body></html>\n",
                    "llm_response": {
                        "item_id 1": 0,
                        "item_id 9": 1
                    },
                    "typical_main_html": "<html></html>",
                    "html_target_list": [],
                    "markdown": "# Hello World"
                },
                "metadata": None
            }
        }
    )


class ServiceStatusResponse(BaseResponse):
    """服务状态响应模型."""

    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="服务版本")
    status: str = Field(..., description="服务状态")
    uptime: Optional[float] = Field(None, description="运行时间（秒）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "服务状态正常",
                "timestamp": "2024-01-01T12:00:00",
                "service": "HTML Processing Service",
                "version": "1.0.0",
                "status": "running",
                "uptime": 3600.5
            }
        }
    )
