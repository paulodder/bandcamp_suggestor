import vlc
import time
from gtts import gTTS
from decouple import config


class MediaPlayer:
    def __init__(self):
        self.vlc_instance = vlc.Instance("--aout=alsa")
        self.player = self.vlc_instance.media_player_new()

    def play(self, sleep=True):
        self.player.play()

        if sleep:
            while self.player.get_state() != vlc.State.Ended:
                time.sleep(1)

    def pause(self):
        self.player.pause()

    def play_from_url(self, url, sleep=True):
        self._create_and_set_media(url)
        self.play(sleep=sleep)

    def play_text(self, text, sleep=True):
        tts = gTTS(text)
        voice_fname = config("PROJECT_DIR") + "voice.mp3"
        tts.save(voice_fname)
        self._create_and_set_media(voice_fname)
        self.play(sleep=sleep)

    def _create_and_set_media(self, url):
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)
