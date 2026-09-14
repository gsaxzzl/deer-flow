"""邮件连接器工具 — 通过 SMTP 发送邮件。

工具注册方式与 ``deerflow.community`` 下的社区工具一致：
config.yaml ``tools:`` 块通过
``use: deerflow.connectors.mail.tools:send_mail`` 引用。
"""

import json
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from langchain.tools import tool

from deerflow.connectors.common.auth import get_auth_store

logger = logging.getLogger(__name__)


def _get_mail_credentials() -> dict | None:
    """从 AuthStore 读取已保存的邮件连接器凭证。"""
    record = get_auth_store().get_first_auth("mail")
    if record is None:
        return None
    metadata = record.get("metadata", {}) or {}
    return {
        "email": metadata.get("email"),
        "smtp_host": metadata.get("smtp_host"),
        "smtp_port": metadata.get("smtp_port", 465),
        "smtp_user": metadata.get("smtp_user") or metadata.get("email"),
        "smtp_security": metadata.get("smtp_security", "ssl"),
        "authorization": record.get("authorization"),
    }


@tool("send_mail", parse_docstring=True)
def send_mail_tool(to: str, subject: str, body: str) -> str:
    """发送邮件给指定收件人。当用户要求"发邮件""发送邮件""通知某人""邮件告诉某人"时使用此工具。
    发件人邮箱和 SMTP 授权凭证从已保存的连接器配置中自动获取，无需额外指定。

    Args:
        to: 收件人邮箱地址。多个地址用英文逗号分隔。
        subject: 邮件主题。
        body: 邮件正文（纯文本）。
    """
    creds = _get_mail_credentials()
    if creds is None or not creds.get("email"):
        return json.dumps(
            {"error": "未找到已保存的邮箱凭证。请先在「设置 → 工具 → 邮件连接器」中保存邮箱和授权凭证。"},
            ensure_ascii=False,
        )

    from_email = creds["email"]
    smtp_host = creds["smtp_host"]
    smtp_port = int(creds["smtp_port"])
    smtp_user = creds["smtp_user"]
    smtp_password = creds["authorization"]
    security = creds["smtp_security"]

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("", from_email))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=from_email.split("@")[-1] if "@" in from_email else None)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        if security == "ssl" or smtp_port in (465, 994):
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30, context=context) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [addr.strip() for addr in to.split(",")], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                if security == "starttls" or smtp_port in (587, 25):
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [addr.strip() for addr in to.split(",")], msg.as_string())
        logger.info("邮件已发送: from=%s to=%s subject=%s", from_email, to, subject)
        return json.dumps(
            {"status": "sent", "from": from_email, "to": to, "subject": subject},
            ensure_ascii=False,
        )
    except Exception as e:
        logger.error("发送邮件失败: %s", e, exc_info=True)
        return json.dumps({"error": f"发送邮件失败: {e}"}, ensure_ascii=False)


@tool("mail_list", parse_docstring=True)
def mail_list_tool(folder: str = "INBOX", page: int = 1) -> str:
    """查看收件箱邮件列表。当用户要求"查看邮件""收件箱""最近邮件"时使用此工具。

    Args:
        folder: 邮箱文件夹名称，默认 INBOX。
        page: 页码，从 1 开始。
    """
    creds = _get_mail_credentials()
    if creds is None or not creds.get("email"):
        return json.dumps(
            {"error": "未找到已保存的邮箱凭证。请先在「设置 → 工具 → 邮件连接器」中保存邮箱和授权凭证。"},
            ensure_ascii=False,
        )

    import imaplib
    from email import message_from_bytes
    from email.header import decode_header

    try:
        imap_host = creds["smtp_host"].replace("smtp.", "imap.", 1)
        if creds["smtp_security"] == "ssl" or creds["smtp_port"] in (465, 994):
            conn = imaplib.IMAP4_SSL(imap_host, 993)
        else:
            conn = imaplib.IMAP4(imap_host, 143)
        conn.login(creds["smtp_user"], creds["authorization"])
        conn.select(folder)

        _, data = conn.search(None, "ALL")
        ids = data[0].split()
        per_page = 10
        start = max(0, len(ids) - page * per_page)
        end = max(0, start + per_page)
        page_ids = ids[start:end][::-1]

        results = []
        for mid in page_ids:
            _, msg_data = conn.fetch(mid, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
            raw = msg_data[0][1] if msg_data and msg_data[0] else b""
            msg = message_from_bytes(raw)
            subject_parts = decode_header(msg.get("Subject", ""))
            subject = "".join(part.decode(enc or "utf-8", errors="replace") if isinstance(part, bytes) else part for part, enc in subject_parts)
            results.append({"id": mid.decode(), "subject": subject, "from": msg.get("From", ""), "date": msg.get("Date", "")})
        conn.logout()
        return json.dumps({"folder": folder, "page": page, "total": len(ids), "results": results}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("获取邮件列表失败: %s", e, exc_info=True)
        return json.dumps({"error": f"获取邮件列表失败: {e}"}, ensure_ascii=False)


@tool("mail_detail", parse_docstring=True)
def mail_detail_tool(mail_id: str) -> str:
    """查看指定邮件的详细内容。当用户要求"打开邮件""查看某封邮件"时使用此工具。

    Args:
        mail_id: 邮件 ID（从 mail_list 结果中获取）。
    """
    creds = _get_mail_credentials()
    if creds is None or not creds.get("email"):
        return json.dumps(
            {"error": "未找到已保存的邮箱凭证。请先在「设置 → 工具 → 邮件连接器」中保存邮箱和授权凭证。"},
            ensure_ascii=False,
        )

    import imaplib
    from email import message_from_bytes
    from email.header import decode_header

    try:
        imap_host = creds["smtp_host"].replace("smtp.", "imap.", 1)
        if creds["smtp_security"] == "ssl" or creds["smtp_port"] in (465, 994):
            conn = imaplib.IMAP4_SSL(imap_host, 993)
        else:
            conn = imaplib.IMAP4(imap_host, 143)
        conn.login(creds["smtp_user"], creds["authorization"])
        conn.select("INBOX")
        _, msg_data = conn.fetch(mail_id.encode(), "(RFC822)")
        raw = msg_data[0][1] if msg_data and msg_data[0] else b""
        msg = message_from_bytes(raw)
        subject_parts = decode_header(msg.get("Subject", ""))
        subject = "".join(part.decode(enc or "utf-8", errors="replace") if isinstance(part, bytes) else part for part, enc in subject_parts)
        body_text = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
        conn.logout()
        return json.dumps(
            {"id": mail_id, "subject": subject, "from": msg.get("From", ""), "date": msg.get("Date", ""), "body": body_text[:5000]},
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        logger.error("获取邮件详情失败: %s", e, exc_info=True)
        return json.dumps({"error": f"获取邮件详情失败: {e}"}, ensure_ascii=False)
