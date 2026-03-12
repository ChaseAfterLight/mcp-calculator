# email_sender.py
from fastmcp import FastMCP
import sys
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger('EmailSender')

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# Create an MCP server
mcp = FastMCP("EmailSender")

@mcp.tool()
def send_email(subject: str, body: str) -> dict:
    """Send an email to 13640292241@qq.com. Use this tool to send emails with a subject and body content.
    Parameters:
    - subject: email subject line
    - body: email body content
    """
    to_email = "13640292241@qq.com"
    to_email = "13640292241@qq.com"
    
    try:
        # Get config from environment variables
        from_email = os.environ.get('EMAIL_FROM')
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([from_email, smtp_server, smtp_password]):
            return {
                "success": False, 
                "error": "Missing email configuration. Please set EMAIL_FROM, SMTP_SERVER, and SMTP_PASSWORD environment variables."
            }
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return {"success": True, "message": f"Email sent to {to_email}"}
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}

# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
