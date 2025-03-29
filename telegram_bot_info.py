
import aiohttp

from config import BOT_TOKEN, ADMIN_ID


class InfoBot:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_id = ADMIN_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send(self, text: str):
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, data=payload) as resp:
                if resp.status != 200:
                    print("Не удалось отправить!")

