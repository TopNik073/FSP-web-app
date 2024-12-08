import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Optional, List
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class EmailService:
    def __init__(self):
        self.smtp_server = "64.233.161.109"
        self.smtp_port = 465
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")

        # Настраиваем окружение для шаблонов
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def _create_connection(self) -> smtplib.SMTP:
        """Создает SMTP соединение с сервером"""
        server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        server.login(self.sender_email, self.sender_password)
        return server

    def _create_message(
            self,
            to_email: str,
            subject: str,
            body: str,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None
    ) -> MIMEMultipart:
        """Создает объект сообщения"""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ", ".join(cc)
        if bcc:
            msg['Bcc'] = ", ".join(bcc)

        msg.attach(MIMEText(body, 'html'))
        return msg

    def send_email(
            self,
            to_email: str,
            subject: str,
            body: str,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Отправляет email
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            body: Текст письма (HTML)
            cc: Список адресов в копии
            bcc: Список адресов в скрытой копии
            
        Returns:
            bool: True если отправка успешна, False если произошла ошибка
        """
        try:
            msg = self._create_message(to_email, subject, body, cc, bcc)

            with self._create_connection() as server:
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.sendmail(self.sender_email, recipients, msg.as_string())
            return True

        except Exception as e:
            print(f"Ошибка при отправке письма: {str(e)}")
            return False

    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Отправляет письмо с подтверждением email"""
        template = self.env.get_template("verification_email.html")
        body = template.render(verification_token=verification_token)
        subject = "Подтверждение email адреса"

        return self.send_email(to_email, subject, body)

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Отправляет письмо для сброса пароля"""
        template = self.env.get_template("password_reset_email.html")
        body = template.render(reset_token=reset_token)
        subject = "Сброс пароля"

        return self.send_email(to_email, subject, body)

    def send_send_password_email(self, to_email: str, password: str) -> bool:
        """Отправляет письмо с паролем"""
        template = self.env.get_template("send_password.html")
        body = template.render(password=password)
        subject = "Данные для входа в систему ФСП"

        return self.send_email(to_email, subject, body)

    def send_event_notification(self, to_email: str, subject: str, event: str) -> bool:
        """Отправляет уведомление о событии"""
        template = self.env.get_template("event_notification.html")
        body = template.render(event=event)
        return self.send_email(to_email, subject, body)


if __name__ == "__main__":
    emailer = EmailService()
    event = {
        "title": "test",
        "date_start": datetime.now(),
        "place": "test",
        "description": "test"
    }
    emailer.send_event_notification("borzovn169@gmail.com", "Тест", event)
