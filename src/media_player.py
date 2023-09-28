import vlc
import time
import asyncio
from pathlib import Path
from decouple import config
from src.utils import load_json, change_suffix


class MediaPlayer:
    def __init__(self, on_media_start=None, on_media_end=None):
        self.vlc_instance = vlc.Instance("--aout=alsa")
        self.player = self.vlc_instance.media_player_new()
        self.queue = []
        self.on_media_start = on_media_start
        self.on_media_end = on_media_end
        self.playing = None

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def toggle_playback(self):
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def get_volume(self):
        return self.player.audio_get_volume()

    def get_progress(self):
        """Returns the current progress in seconds."""
        return int(self.player.get_time() / 1000)

    def get_info(self):
        """Returns the current song name."""
        if self.playing:
            info_fpath = change_suffix(self.playing, ".json")
            time = self.get_progress()

            song_info = load_json(info_fpath)
            n_tracks = len(song_info["tracklist"])
            if time < song_info["times"][0]:
                return song_info["tracklist"][0]

            for i in range(n_tracks - 1):
                if (
                    time > song_info["times"][i]
                    and time < song_info["times"][i + 1]
                ):
                    return song_info["tracklist"][i]
            return song_info["tracklist"][-1]

    def set_volume(self, volume):
        if volume < 0 or volume > 100:
            raise ValueError("Volume should be between 0 and 100")
        self.player.audio_set_volume(volume)

    def enqueue(self, url):
        self.queue.append(url)

    def play_from_url(self, url, volume=100):
        if volume != self.get_volume():
            self.set_volume(volume)

        url = Path(url)
        print(f"playing: {url.name}")
        self._create_and_set_media(url)
        self.play()
        self.playing = url

    def media_has_ended(self):
        return self.player.get_state() == vlc.State.Ended

    def is_playing(self):
        return self.player.is_playing()

    async def await_end(self):
        while not self.media_has_ended():
            await asyncio.sleep(0.5)
        return True

    def await_end_blocking(self):
        while not self.media_has_ended():
            time.sleep(0.5)
        return True

    def mp3_in_queue_or_playing(self, url):
        return url in self.queue or url == self.playing

    async def play_queue(self):
        while True:
            if not self.is_playing():
                if self.queue:
                    next_url = self.queue.pop(0)
                    self.on_media_start()
                    self.play_from_url(next_url)

                    print("queued:", len(self.queue), "slices")
                    await self.await_end()
                    if self.on_media_end:
                        self.on_media_end(next_url)

            await asyncio.sleep(0.5)

    def play_next_in_queue(self):
        """Immediately stop current playback and play the next item in queue."""
        if self.queue:
            if self.on_media_end is not None:
                self.on_media_end(self.playing)
            next_url = self.queue.pop(0)
            if self.on_media_start is not None:
                self.on_media_start()
            self.play_from_url(next_url)
            return
        print("No songs in queue")

    def _create_and_set_media(self, url):
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)


# # Async example usage
# async def main():
#     player = MediaPlayer()
#     player.enqueue("some_url_1")
#     player.enqueue("some_url_2")
#     player.enqueue("some_url_3")
#     await player.process_queue()


# if __name__ == "__main__":
#     asyncio.run(main())
