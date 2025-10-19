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

def get_approval_message(language: str, title: str, location: str) -> str:
    messages = {
        "am": f'"{title}" የተሰኘው በአ/አ {location} የሚገኘው ዝርዝርዎ ጸድቋል።',
        "om": f'Galmeen keessan kan "{title}" jedhamu kan Finfinnee {location} jiru mirkanaa'eera.',
        "en": f'Your listing "{title}" located in Addis Ababa, {location} has been approved.'
    }
    return messages.get(language, messages["en"])
