"""HTML 处理路由.

提供 HTML 解析、内容提取等功能的 API 端点。
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies import get_logger, get_settings
from ..models.request import HTMLParseRequest
from ..models.response import HTMLParseResponse
from ..services.html_service import HTMLService
from ..services.request_log_service import RequestLogService

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter()


@router.post('/html/parse', response_model=HTMLParseResponse)
async def parse_html(
    request: HTMLParseRequest,
    html_service: HTMLService = Depends(HTMLService),
    db_session: Optional[AsyncSession] = Depends(get_db_session)
):
    """解析 HTML 内容.

    接收 HTML 字符串并返回解析后的结构化内容。
    """
    # 生成请求ID
    request_id = RequestLogService.generate_request_id()

    # 确定输入类型
    if request.html_content:
        input_type = 'html_content'
    elif request.url:
        input_type = 'url'
    else:
        input_type = 'unknown'

    # 创建请求日志
    await RequestLogService.create_log(
        session=db_session,
        request_id=request_id,
        input_type=input_type,
        input_html=request.html_content,
        url=request.url,
    )

    # 立即提交，使 processing 状态在数据库中可见
    if db_session:
        try:
            await db_session.commit()
        except Exception as commit_error:
            logger.error(f'提交初始日志时出错: {commit_error}')

    try:
        logger.info(f'开始解析 HTML [request_id={request_id}]，内容长度: {len(request.html_content) if request.html_content else 0}')

        result = await html_service.parse_html(
            html_content=request.html_content,
            url=request.url,
            options=request.options
        )

        # 更新日志为成功
        await RequestLogService.update_log_success(
            session=db_session,
            request_id=request_id,
            output_markdown=result.get('markdown'),
        )

        return HTMLParseResponse(
            success=True,
            data=result,
            message='HTML 解析成功',
            request_id=request_id
        )
    except Exception as e:
        logger.error(f'HTML 解析失败 [request_id={request_id}]: {str(e)}')

        # 更新日志为失败
        await RequestLogService.update_log_failure(
            session=db_session,
            request_id=request_id,
            error_message=str(e),
        )

        # 手动提交事务，确保失败日志被保存
        if db_session:
            try:
                await db_session.commit()
            except Exception as commit_error:
                logger.error(f'提交失败日志时出错: {commit_error}')

        raise HTTPException(status_code=500, detail=f'HTML 解析失败: {str(e)}')


@router.post('/html/upload')
async def upload_html_file(
    file: UploadFile = File(...),
    html_service: HTMLService = Depends(HTMLService),
    db_session: Optional[AsyncSession] = Depends(get_db_session)
):
    """上传 HTML 文件进行解析.

    支持上传 HTML 文件，自动解析并返回结果。
    """
    # 生成请求ID
    request_id = RequestLogService.generate_request_id()

    try:
        if not file.filename.endswith(('.html', '.htm')):
            raise HTTPException(status_code=400, detail='只支持 HTML 文件')

        content = await file.read()
        html_content = content.decode('utf-8')

        logger.info(f'上传 HTML 文件 [request_id={request_id}]: {file.filename}, 大小: {len(content)} bytes')

        # 创建请求日志
        await RequestLogService.create_log(
            session=db_session,
            request_id=request_id,
            input_type='file',
            input_html=html_content,
            url=None,
        )

        # 立即提交，使 processing 状态在数据库中可见
        if db_session:
            try:
                await db_session.commit()
            except Exception as commit_error:
                logger.error(f'提交初始日志时出错: {commit_error}')

        result = await html_service.parse_html(html_content=html_content)

        # 更新日志为成功
        await RequestLogService.update_log_success(
            session=db_session,
            request_id=request_id,
            output_markdown=result.get('markdown'),
        )

        return HTMLParseResponse(
            success=True,
            data=result,
            message='HTML 文件解析成功',
            request_id=request_id
        )
    except Exception as e:
        logger.error(f'HTML 文件解析失败 [request_id={request_id}]: {str(e)}')

        # 更新日志为失败
        await RequestLogService.update_log_failure(
            session=db_session,
            request_id=request_id,
            error_message=str(e),
        )

        # 手动提交事务，确保失败日志被保存
        if db_session:
            try:
                await db_session.commit()
            except Exception as commit_error:
                logger.error(f'提交失败日志时出错: {commit_error}')

        raise HTTPException(status_code=500, detail=f'HTML 文件解析失败: {str(e)}')


@router.get('/html/status')
async def get_service_status():
    """获取服务状态.

    返回 HTML 处理服务的当前状态信息。
    """
    return {
        'service': 'HTML Processing Service',
        'status': 'running',
        'version': '1.0.0'
    }
