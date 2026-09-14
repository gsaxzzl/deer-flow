"""连接器凭证管理路由 — 保存/查询连接器授权凭证。

公共服务层，所有连接器（邮件、Wiki 等）共用。
- POST /api/connectors/auth     — 保存凭证（username 取自当前登录用户）
- GET  /api/connectors/auth/{connector_type} — 查询当前用户的凭证
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.gateway.deps import get_current_user_from_request
from deerflow.connectors.common.auth import get_auth_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["connectors"])


class ConnectorAuthRequest(BaseModel):
    """保存连接器凭证的请求体。"""

    connector_type: str = Field(..., description="连接器类型，如 mail")
    authorization: str = Field(..., description="授权凭证（SMTP 密码/授权码、Bearer token 等）")
    metadata: dict = Field(default_factory=dict, description="额外元数据，如 email/smtp_host")


class ConnectorAuthResponse(BaseModel):
    """连接器凭证响应。"""

    username: str
    connector_type: str
    authorization: str
    metadata: dict
    status: str


@router.post("/connectors/auth", response_model=ConnectorAuthResponse, summary="保存连接器凭证")
async def save_connector_auth(request: Request, body: ConnectorAuthRequest) -> ConnectorAuthResponse:
    user = await get_current_user_from_request(request)
    username = getattr(user, "email", None) or str(user.id)
    store = get_auth_store()
    record = store.save_auth(
        username=username,
        connector_type=body.connector_type,
        authorization=body.authorization,
        metadata=body.metadata,
    )
    logger.info("连接器凭证已保存: user=%s, type=%s", username, body.connector_type)
    return ConnectorAuthResponse(**record)


@router.get("/connectors/auth/{connector_type}", response_model=ConnectorAuthResponse, summary="查询连接器凭证")
async def get_connector_auth(request: Request, connector_type: str) -> ConnectorAuthResponse:
    user = await get_current_user_from_request(request)
    username = getattr(user, "email", None) or str(user.id)
    store = get_auth_store()
    record = store.get_auth(username, connector_type)
    if record is None:
        raise HTTPException(status_code=404, detail=f"未找到连接器类型 '{connector_type}' 的凭证")
    return ConnectorAuthResponse(**record)
