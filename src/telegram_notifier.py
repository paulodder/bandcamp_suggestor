from decouple import config
from pathlib import Path
from telegram import Bot


class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.bot = Bot(token)
        self.chat_id = chat_id

    async def send_message(self, message):
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    async def send_audio(self, audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            await self.bot.send_audio(chat_id=self.chat_id, audio=audio_file)


async def send_radio_w():
    await tn.send_message("Here's your daily radio")
    await tn.send_audio(Path(config("MP3_DIR")) / "todays_boemketel_radio.mp3")


# if __name__ == "__main__":
#     tn = TelegramNotifier(config("TELEGRAM_TOKEN"), config("TELEGRAM_CHAT_ID"))
#     asyncio.run(main())
