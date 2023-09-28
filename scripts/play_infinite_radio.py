import json
import time
import asyncio
from functools import partial
from decouple import config
from pathlib import Path
from multiprocessing import Process, Queue
from src.radio_generator import RadioGenerator
from src.telegram_notifier import TelegramNotifier
from src.time_manager import TimeManager
from src.media_player import MediaPlayer
from src.utils import generate_paths, change_suffix, connection_is_active
from src.inputtimeout import inputtimeout, TimeoutOccurred

# from src.button_monitor import ButtonMonitor
try:
    from src.pi_buttons import RPButtons

    IS_RASPBERYY_PI = True
except (ImportError, RuntimeError):
    IS_RASPBERYY_PI = False


class RadioPlayer:
    def __init__(self, bc_user=None, mp_queue=None):
        self.rg = RadioGenerator(bc_user)
        self.tm = TimeManager()
        self.tn = TelegramNotifier(
            config("TELEGRAM_TOKEN"), config("TELEGRAM_CHAT_ID")
        )
        self.mp = MediaPlayer(
            on_media_start=self.on_media_start, on_media_end=self.on_media_end
        )
        self.tmp_dir = Path(config("MP3_DIR")) / "tmp"
        self.tmp_dir.mkdir(exist_ok=True, parents=True)
        self.slice_dir = Path(config("MP3_DIR")) / "slices"
        self.slice_dir.mkdir(exist_ok=True, parents=True)
        self.mp_queue = mp_queue

        self.buttons = RPButtons([24, 23]) if IS_RASPBERYY_PI else None

    async def start_radio(self):
        # Start queue task
        check_queue_task = asyncio.create_task(self.check_queue_and_enqueue())

        # Generate intro speech
        intro_speech_fpath = self.rg.generate_intro_speech(
            self.tm.time_difference_in_minutes()
        )
        self.mp.enqueue(intro_speech_fpath)

        # Initialize radio
        self.init_radio()

        # Start cleanup process
        cleanup_task = asyncio.create_task(self.continuous_cleanup())

        button_task = asyncio.create_task(self.monitor_buttons())

        # Start continuous playpack
        await self.mp.play_queue()

        cleanup_task.cancel()
        button_task.cancel()
        self.p.terminate()
        # generator_task.cancel()

    def init_radio(self):
        existing_slices = self._get_existing_slices()
        sorted_slices = sorted(
            existing_slices, key=lambda x: int(x.stem.split("_")[0])
        )
        if len(sorted_slices) > 2:
            del_fpath = sorted_slices.pop(0)
            del_fpath.unlink()  # Delete last playing one
            change_suffix(del_fpath, ".json").unlink()

        for mp3_fpath in sorted_slices:
            # if mp3_fpath not in self.mp.queue:
            self.mp.enqueue(mp3_fpath)

    async def monitor_buttons(self):
        if IS_RASPBERYY_PI:
            input_monitor_fn = self.buttons.button_pressed
            print(
                "press 1st button to send song info to phone, press 2nd for next wishlist item"
            )
        else:
            print(
                "press i to send song info to phone, press n for next wishlist item"
            )
            input_monitor_fn = partial(self._monitor_keyboard, timeout=0.5)

        while True:
            button_pressed = input_monitor_fn()
            if button_pressed is False:
                await asyncio.sleep(0.1)
                continue

            if button_pressed == 0:
                print("GET INFO")
                await self.send_info_to_phone()
            elif button_pressed == 1:
                print("SKIP SONG")
                self.mp.play_next_in_queue()
            await asyncio.sleep(0.5)

    @staticmethod
    def _monitor_keyboard(timeout=1):
        try:
            kb_press = inputtimeout(prompt="", timeout=timeout)
            if kb_press == "i":
                return 0
            if kb_press == "n":
                return 1
            return False
        except TimeoutOccurred:
            return False

    async def send_info_to_phone(self):
        # TODO: Include genres
        print("* sending track to phone *")
        track_info = self.mp.get_info()
        await self.tn.send_message(track_info)

    async def check_queue_and_enqueue(self):
        while True:
            while not self.mp_queue.empty():
                radio_fpath = self.mp_queue.get()
                print(f"* adding {radio_fpath.name} to queue *")
                self.mp.enqueue(radio_fpath)
            await asyncio.sleep(5)  # Check every 5 seconds or as needed

    async def continuous_cleanup(self):
        while True:
            print("* running cleanup *")
            self.cleanup()
            await asyncio.sleep(360)

    def cleanup(self):
        cleanup_files = self.tmp_dir.glob("*_*_*.mp3")

        current_time = time.time()
        for fpath in cleanup_files:
            if len(fpath.stem.split("_")) != 3:
                continue

            if (
                self._time_diff(
                    current_time, self._extract_time_from_fpath(fpath)
                )
                > 360
            ):
                fpath.unlink()

        # Clean slices
        existing_slices = self._get_existing_slices()
        rem_slices = [
            x
            for x in existing_slices
            if not self.mp.mp3_in_queue_or_playing(x)
        ]

        self._rem_files(rem_slices)

    def _time_diff(self, t1, t2):
        return t1 - t2

    def _extract_time_from_fpath(self, fpath):
        return int(fpath.stem.split("_")[0])

    def _rem_files(self, fpaths):
        for fpath in fpaths:
            fpath.unlink()

    def _get_existing_slices(self):
        return list(self.slice_dir.glob("*_bkradio_*.mp3"))

    def on_media_start(self):
        self.tm.update_time()

    def on_media_end(self, url):
        # Delete the file if it exists
        fpath = Path(url)
        if fpath.exists() and fpath.is_file():
            fpath.unlink()

        json_fpath = change_suffix(fpath, ".json")
        if json_fpath.exists() and json_fpath.is_file():
            json_fpath.unlink()


def run_generate_radio(bc_user, mp_queue):
    try:
        rg = RadioGenerator(bc_user)
        asyncio.run(rg.continuous_generate_radio(mp_queue, min_slices=20))
    except Exception as e:
        error_callback(e)


def run_radio(bc_user, mp_queue):
    try:
        rp = RadioPlayer(bc_user, mp_queue)
        asyncio.run(rp.start_radio())
    except Exception as e:
        rp.mp.pause()
        error_callback(e)


def error_callback(e):
    print(f"An error occurred: {e}")
    mp = MediaPlayer()
    mp.play_from_url(config("PROJECT_DIR") + "mp3/offline_mode.mp3")
    mp.await_end_blocking()


def no_internet(e):
    mp = MediaPlayer()
    mp.play_from_url(config("PROJECT_DIR") + "mp3/no_internet.mp3")
    mp.await_end_blocking()


if __name__ == "__main__":
    bc_user = None  # can be overwritten here (enter string)
    bc_user = "adriaanscholtens"

    if not connection_is_active():
        print("ERROR: No internet connection was established")
        no_internet()
        quit()

    mp_queue = Queue()
    # p = Process(target=run_radio, args=(bc_user, mp_queue))
    # p.start()

    # run_generate_radio(bc_user, mp_queue)

    p = Process(target=run_generate_radio, args=(bc_user, mp_queue))
    p.start()

    run_radio(bc_user, mp_queue)
