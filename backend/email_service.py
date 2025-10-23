from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pathlib import Path
from jinja2 import Template
import base64
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        # Get SMTP configuration from environment variables
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', '587'))
        mail_username = os.getenv('MAIL_USERNAME', 'noreply@fitsani.com')
        mail_password = os.getenv('MAIL_PASSWORD', 'defaultpassword')
        mail_from = os.getenv('MAIL_FROM', mail_username)
        
        # Configure SMTP connection
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_FROM=mail_from,
            MAIL_PORT=mail_port,
            MAIL_SERVER=mail_server,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=Path(__file__).parent / "templates"
        )
        
        self.fm = FastMail(self.mail_config)
    
    async def send_verification_email(
        self, 
        user_email: str,
        verification_link: str,
        user_name: str
    ) -> bool:
        """Send HTML verification email with embedded logo."""
        try:
            # Read and encode logo image for embedding
            logo_path = Path(__file__).parent / "static" / "logo.png"
            logo_base64 = None
            if logo_path.exists():
                with open(logo_path, "rb") as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode()
            
            # Read HTML template
            template_path = Path(__file__).parent / "templates" / "verification_email.html"
            with open(template_path, "r") as template_file:
                template_content = template_file.read()
            
            # Render template with context
            template = Template(template_content)
            html_content = template.render(
                user_name=user_name,
                verification_link=verification_link,
                logo_base64=logo_base64,
                app_name="Fitsani"
            )
            
            # Create message
            message = MessageSchema(
                subject="Verify Your Fitsani Email Address",
                recipients=[user_email],
                body=html_content,
                subtype=MessageType.html
            )
            
            # Send email
            await self.fm.send_message(message)
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# Singleton instance
email_service = EmailService()
