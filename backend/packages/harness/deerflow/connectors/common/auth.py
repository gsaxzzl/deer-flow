"""连接器凭证存储 — 文件后端 (auth_db=false, encrypt_token=false)。

所有连接器（邮件、Wiki 等）共用此公共服务层。
凭证以 JSON 文件持久化在 ``runtime_home() / "connector_auth.json"``，
键为 ``"{username}:{connector_type}"``。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from deerflow.config.runtime_paths import runtime_home

logger = logging.getLogger(__name__)

_AUTH_FILE_NAME = "connector_auth.json"


def _auth_file_path() -> Path:
    """返回凭证文件的绝对路径，确保父目录存在。"""
    path = runtime_home() / _AUTH_FILE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class AuthStore:
    """连接器凭证存储，文件后端实现。"""

    def _load(self) -> dict[str, dict[str, Any]]:
        path = _auth_file_path()
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("读取连接器凭证文件失败: %s", e)
            return {}

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        path = _auth_file_path()
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        logger.info("连接器凭证已保存到 %s", path)

    @staticmethod
    def _key(username: str, connector_type: str) -> str:
        return f"{username}:{connector_type}"

    def save_auth(
        self,
        username: str,
        connector_type: str,
        authorization: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """保存连接器授权凭证。

        Args:
            username: 用户标识。
            connector_type: 连接器类型，如 ``"mail"``。
            authorization: 授权凭证（SMTP 密码/授权码、Bearer token 等）。
            metadata: 额外元数据，如 ``{"email": "...", "smtp_host": "..."}``。

        Returns:
            保存后的凭证记录。
        """
        data = self._load()
        key = self._key(username, connector_type)
        data[key] = {
            "username": username,
            "connector_type": connector_type,
            "authorization": authorization,
            "metadata": metadata or {},
            "status": "active",
        }
        self._save(data)
        logger.info("已保存连接器凭证: username=%s, connector_type=%s", username, connector_type)
        return data[key]

    def get_auth(self, username: str, connector_type: str) -> dict[str, Any] | None:
        """读取指定用户和连接器类型的凭证。"""
        data = self._load()
        key = self._key(username, connector_type)
        return data.get(key)

    def get_first_auth(self, connector_type: str) -> dict[str, Any] | None:
        """读取指定连接器类型的第一条凭证（单用户部署场景）。"""
        data = self._load()
        for value in data.values():
            if value.get("connector_type") == connector_type:
                return value
        return None


_auth_store: AuthStore | None = None


def get_auth_store() -> AuthStore:
    """获取全局 AuthStore 单例。"""
    global _auth_store
    if _auth_store is None:
        _auth_store = AuthStore()
    return _auth_store
