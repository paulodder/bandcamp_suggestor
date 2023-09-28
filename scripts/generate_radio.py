import asyncio
from decouple import config
from pathlib import Path
from src.utils import get_date_str
from src.telegram_notifier import TelegramNotifier
from src.radio_generator import RadioGenerator


def main():
    bc_user = None
    # bc_user = "adriaanscholtens" # Override
    # bc_user = "tabletop13"
    rg = RadioGenerator()
    radio_fpath = (
        Path(config("MP3_DIR"))
        / f"bkradio_{config('BANDCAMP_USER')}_{get_date_str(file_format=True)}.mp3"
    )
    tracklist_msg = None
    tracklist_msg = rg.generate_radio(
        radio_fpath, n_source_songs=2, n_recs_per_song=2
    )

    # Send the result to phone using TelegramNotifier
    print("Sending to phone")
    tn = TelegramNotifier(config("TELEGRAM_TOKEN"), config("TELEGRAM_CHAT_ID"))
    asyncio.run(send_to_phone(tn, radio_fpath, tracklist_msg))


async def send_to_phone(telegram_notifier, mp3_fpath, message=None):
    for _ in range(3):  # try 3 times
        try:
            await telegram_notifier.send_audio(mp3_fpath)
            await telegram_notifier.send_message(
                "here's your personalized boemketel radio for today :)"
            )
            if message is not None:
                await telegram_notifier.send_message(message)
            break  # if successful, break the retry loop
        except Exception as e:  # replace Exception with the specific exception you're handling
            print(f"exception while sending: {e}. retrying...")
            await asyncio.sleep(5)  # wait for 5 seconds before retrying


if __name__ == "__main__":
    main()
