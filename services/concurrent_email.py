import asyncio
import logging
from typing import List, Dict, Optional
from services import EmailService

logger = logging.getLogger(__name__)

class ConcurrentEmailService:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
    
    async def send_single_email(self, recipient: str, content: str, subject: str = "Newsletter") -> Dict:
        """Send email to single recipient with concurrency control"""
        async with self.semaphore:
            try:
                email_service = EmailService(
                    recipients=[recipient],
                    subject=subject,
                    body_text=content
                )
                result = email_service.send_email()
                return {"recipient": recipient, "status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {e}")
                return {"recipient": recipient, "status": "error", "error": str(e)}
    
    async def send_emails_concurrent(self, recipients: List[str], content: str, subject: str = "Newsletter") -> Dict:
        """Send emails to multiple recipients concurrently"""
        if not recipients:
            return {"status": "error", "message": "No recipients provided"}
        
        logger.info(f"Sending emails to {len(recipients)} recipients with max {self.max_concurrent} concurrent")
        
        tasks = [
            self.send_single_email(recipient, content, subject)
            for recipient in recipients
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        failed = len(results) - successful
        
        return {
            "status": "completed",
            "total": len(recipients),
            "successful": successful,
            "failed": failed,
            "results": results
        }