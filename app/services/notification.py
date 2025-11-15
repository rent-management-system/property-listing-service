import httpx
from app.config import settings
from app.utils.retry import async_retry

@async_retry()
async def send_notification(user_id: str, message: str):
    async with httpx.AsyncClient() as client:
        # This is a mock implementation. In a real scenario, you would format
        # the message based on the user's preferred language.
        payload = {"user_id": user_id, "message": message}
        await client.post(f"{settings.NOTIFICATION_URL}/send", json=payload)

def get_approval_message(language: str, title: str, location: str, payment_amount: float, payment_currency: str) -> str:
    messages = {
        "am": f'"" የተሰኘው በአ/አ {location} የሚገኘው ዝርዝርዎ በ {payment_amount} {payment_currency} ክፍያ ጸድቋል።',
        "om": f'Galmeen keessan kan "" jedhamu kan Finfinnee {location} jiru, kaffaltii {payment_amount} {payment_currency} booda mirkanaa\'eera.',
        "en": f'Your listing "" located in Addis Ababa, {location} has been approved after a {payment_amount} {payment_currency} payment.'
    }
    return messages.get(language, messages["en"])
