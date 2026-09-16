"""GitHub 连接器工具 — 只读查询 GitHub 仓库信息。

工具注册方式与邮件连接器一致：
config.yaml ``tools:`` 块通过
``use: deerflow.connectors.github.tools:repo_info_tool`` 引用。

用户需先在「连接器页面」保存 GitHub 仓库地址和 Fine-grained Token。
"""

import json
import logging
import re

import httpx
from langchain.tools import tool

from deerflow.connectors.common.auth import get_auth_store

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _get_github_credentials() -> dict | None:
    """从 AuthStore 读取已保存的 GitHub 连接器凭证。"""
    record = get_auth_store().get_first_auth("github")
    if record is None:
        return None
    metadata = record.get("metadata", {}) or {}
    return {
        "repo_url": metadata.get("repo_url"),
        "token": record.get("authorization"),
    }


def _parse_owner_repo(url: str) -> tuple[str, str] | None:
    """从仓库地址解析 owner/repo。

    支持格式:
        https://github.com/{owner}/{repo}
        http://github.com/{owner}/{repo}
        github.com/{owner}/{repo}
        {owner}/{repo}
    """
    url = url.strip().rstrip("/").removesuffix(".git")
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+)$", url)
    if match:
        return match.group(1), match.group(2)
    # 纯 owner/repo 形式
    parts = url.split("/")
    if len(parts) == 2 and all(parts):
        return parts[0], parts[1]
    return None


def _resolve_repo(owner: str | None, repo: str | None, creds: dict) -> tuple[str, str] | None:
    """优先使用显式传入的 owner/repo，否则回退到已保存的默认仓库。"""
    if owner and repo:
        return owner, repo
    if creds.get("repo_url"):
        return _parse_owner_repo(creds["repo_url"])
    return None


def _github_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _github_get(creds: dict, path: str, params: dict | None = None) -> httpx.Response:
    return httpx.get(
        f"{GITHUB_API_BASE}{path}",
        headers=_github_headers(creds["token"]),
        params=params,
        timeout=30,
    )


@tool("repo_info", parse_docstring=True)
def repo_info_tool(owner: str = "", repo: str = "") -> str:
    """查看 GitHub 仓库的基本信息（描述、star 数、默认分支、最近更新等）。当用户询问"仓库信息""仓库情况""star 数""项目简介"时使用此工具。
    仓库地址从已保存的连接器配置中自动获取，无需额外指定；也可通过 owner 和 repo 参数显式查询其他仓库。

    Args:
        owner: 仓库所有者（如 gsaxzzl），留空则使用已保存的默认仓库。
        repo: 仓库名（如 deer-flow），留空则使用已保存的默认仓库。
    """
    creds = _get_github_credentials()
    if creds is None or not creds.get("token"):
        return json.dumps(
            {"error": "未找到已保存的 GitHub 凭证。请先在「连接器」页面配置 GitHub 仓库地址和 Fine-grained Token。"},
            ensure_ascii=False,
        )

    resolved = _resolve_repo(owner or None, repo or None, creds)
    if resolved is None:
        return json.dumps({"error": "无法确定目标仓库，请提供 owner 和 repo 参数，或在连接器中保存仓库地址。"}, ensure_ascii=False)

    o, r = resolved
    try:
        resp = _github_get(creds, f"/repos/{o}/{r}")
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("GitHub API 请求失败: %s", e)
        return json.dumps({"error": f"GitHub API 返回 {e.response.status_code}: {e.response.text[:200]}"}, ensure_ascii=False)
    except httpx.HTTPError as e:
        logger.warning("GitHub API 网络错误: %s", e)
        return json.dumps({"error": f"网络错误: {e}"}, ensure_ascii=False)

    data = resp.json()
    return json.dumps(
        {
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "html_url": data.get("html_url"),
            "default_branch": data.get("default_branch"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "visibility": data.get("visibility"),
            "updated_at": data.get("updated_at"),
        },
        ensure_ascii=False,
    )


@tool("list_commits", parse_docstring=True)
def list_commits_tool(owner: str = "", repo: str = "", branch: str = "", limit: int = 10) -> str:
    """查看 GitHub 仓库的提交历史。当用户询问"提交记录""提交历史""最近提交""commits""更新了什么"时使用此工具。
    仓库地址从已保存的连接器配置中自动获取，无需额外指定；也可通过 owner 和 repo 参数显式查询其他仓库。

    Args:
        owner: 仓库所有者，留空则使用已保存的默认仓库。
        repo: 仓库名，留空则使用已保存的默认仓库。
        branch: 分支名（如 zzl-connector），留空则使用默认分支。
        limit: 返回条数，默认 10，最大 50。
    """
    creds = _get_github_credentials()
    if creds is None or not creds.get("token"):
        return json.dumps(
            {"error": "未找到已保存的 GitHub 凭证。请先在「连接器」页面配置 GitHub 仓库地址和 Fine-grained Token。"},
            ensure_ascii=False,
        )

    resolved = _resolve_repo(owner or None, repo or None, creds)
    if resolved is None:
        return json.dumps({"error": "无法确定目标仓库，请提供 owner 和 repo 参数，或在连接器中保存仓库地址。"}, ensure_ascii=False)

    o, r = resolved
    params: dict = {"per_page": min(max(int(limit), 1), 50)}
    if branch:
        params["sha"] = branch
    try:
        resp = _github_get(creds, f"/repos/{o}/{r}/commits", params)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("GitHub API 请求失败: %s", e)
        return json.dumps({"error": f"GitHub API 返回 {e.response.status_code}: {e.response.text[:200]}"}, ensure_ascii=False)
    except httpx.HTTPError as e:
        logger.warning("GitHub API 网络错误: %s", e)
        return json.dumps({"error": f"网络错误: {e}"}, ensure_ascii=False)

    commits = [
        {
            "sha": item.get("sha", "")[:8],
            "author": (item.get("commit") or {}).get("author", {}).get("name"),
            "date": (item.get("commit") or {}).get("author", {}).get("date"),
            "message": ((item.get("commit") or {}).get("message") or "").split("\n")[0],
            "url": item.get("html_url"),
        }
        for item in resp.json()
    ]
    return json.dumps({"repo": f"{o}/{r}", "branch": branch or "默认分支", "count": len(commits), "commits": commits}, ensure_ascii=False)


@tool("list_issues", parse_docstring=True)
def list_issues_tool(owner: str = "", repo: str = "", state: str = "open", limit: int = 10) -> str:
    """查看 GitHub 仓库的 Issue 列表。当用户询问"issue""问题列表""有哪些 issue""待办问题"时使用此工具。
    仓库地址从已保存的连接器配置中自动获取，无需额外指定；也可通过 owner 和 repo 参数显式查询其他仓库。

    Args:
        owner: 仓库所有者，留空则使用已保存的默认仓库。
        repo: 仓库名，留空则使用已保存的默认仓库。
        state: Issue 状态：open（默认）、closed、all。
        limit: 返回条数，默认 10，最大 50。
    """
    creds = _get_github_credentials()
    if creds is None or not creds.get("token"):
        return json.dumps(
            {"error": "未找到已保存的 GitHub 凭证。请先在「连接器」页面配置 GitHub 仓库地址和 Fine-grained Token。"},
            ensure_ascii=False,
        )

    resolved = _resolve_repo(owner or None, repo or None, creds)
    if resolved is None:
        return json.dumps({"error": "无法确定目标仓库，请提供 owner 和 repo 参数，或在连接器中保存仓库地址。"}, ensure_ascii=False)

    o, r = resolved
    if state not in ("open", "closed", "all"):
        state = "open"
    params: dict = {"state": state, "per_page": min(max(int(limit), 1), 50)}
    try:
        resp = _github_get(creds, f"/repos/{o}/{r}/issues", params)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("GitHub API 请求失败: %s", e)
        return json.dumps({"error": f"GitHub API 返回 {e.response.status_code}: {e.response.text[:200]}"}, ensure_ascii=False)
    except httpx.HTTPError as e:
        logger.warning("GitHub API 网络错误: %s", e)
        return json.dumps({"error": f"网络错误: {e}"}, ensure_ascii=False)

    # issues API 会混入 PR（带 pull_request 字段），过滤掉
    issues = [
        {
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "author": (item.get("user") or {}).get("login"),
            "labels": [lb.get("name") for lb in item.get("labels", [])],
            "created_at": item.get("created_at"),
            "url": item.get("html_url"),
        }
        for item in resp.json()
        if "pull_request" not in item
    ]
    return json.dumps({"repo": f"{o}/{r}", "state": state, "count": len(issues), "issues": issues}, ensure_ascii=False)
