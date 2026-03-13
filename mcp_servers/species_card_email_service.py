from fastmcp import FastMCP
import sys
import logging
import smtplib
import os
import json
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.card_renderer import CardRenderer

logger = logging.getLogger('SpeciesCardEmailService')

# 修复 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# 创建 MCP 服务
mcp = FastMCP("SpeciesCardEmailService")


def _find_card_by_id(card_id: str) -> dict:
    """根据卡片ID查找卡片信息"""
    index_file = Path(__file__).parent.parent / "cards" / "index.json"
    if not index_file.exists():
        return None

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)

        for card in index:
            if card.get("card_id") == card_id:
                return card
    except Exception as e:
        logger.error(f"读取索引文件失败: {e}")

    return None


@mcp.tool()
def send_species_card_email(
        card_id: str,
        to_email: str = "13640292241@qq.com",
        email_subject: str = None,
        email_body: str = None
) -> dict:
    """发送已有的物种图鉴卡片到邮箱

    Parameters:
    - card_id: 卡片编号（如 P001）
    - to_email: 收件人邮箱（默认 13640292241@qq.com）
    - email_subject: 邮件主题（可选）
    - email_body: 邮件正文（可选）

    Returns:
    - success: 是否成功
    - message: 结果信息
    - error: 错误信息（如果失败）
    """
    try:
        # 查找卡片信息
        card_info = _find_card_by_id(card_id)
        if not card_info:
            return {"success": False, "error": f"未找到卡片 {card_id}"}

        # 检查图片文件是否存在
        image_path = card_info.get('image_path')
        if not image_path or not Path(image_path).exists():
            return {"success": False, "error": f"卡片图片文件不存在: {image_path}"}

        # 发送邮件
        email_result = _send_card_email(
            image_path,
            card_info['chinese_name'],
            card_info.get('latin_name', ''),
            card_id,
            to_email,
            email_subject,
            email_body
        )

        return email_result

    except Exception as e:
        logger.error(f"发送卡片邮件时发生错误: {e}")
        return {"success": False, "error": str(e)}


def _send_card_email(card_image_path: str, chinese_name: str, latin_name: str,
                     card_id: str, to_email: str, subject: str = None, body: str = None) -> dict:
    """发送卡片邮件的内部函数"""
    try:
        # 获取邮件配置
        from_email = os.environ.get('EMAIL_FROM')
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_password = os.environ.get('SMTP_PASSWORD')

        if not all([from_email, smtp_server, smtp_password]):
            return {
                "success": False,
                "error": "缺少邮件配置，请设置 EMAIL_FROM, SMTP_SERVER 和 SMTP_PASSWORD 环境变量"
            }

        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject or f"物种图鉴卡片 - {chinese_name} ({card_id})"

        # 邮件正文
        if not body:
            body = f"""
您好！

这是为您生成的物种图鉴卡片：

【{chinese_name}】
学名：{latin_name}
卡片编号：{card_id}

请查看附件中的卡片图片。

祝好！
"""

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 附加图片
        with open(card_image_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment',
                           filename=f"{chinese_name}_{card_id}.png")
            msg.attach(img)

        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, smtp_password)
            server.send_message(msg)

        logger.info(f"卡片邮件发送成功到 {to_email}")
        return {"success": True, "message": f"卡片邮件已发送到 {to_email}"}

    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return {"success": False, "error": str(e)}


# 启动服务
if __name__ == "__main__":
    mcp.run(transport="stdio")
