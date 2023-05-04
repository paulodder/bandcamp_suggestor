import vlc
import time
from gtts import gTTS
from decouple import config


class MediaPlayer:
    def __init__(self):
        self.vlc_instance = vlc.Instance("--aout=alsa")
        self.player = self.vlc_instance.media_player_new()

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def play_from_url(self, url):
        self._create_and_set_media(url)
        self.play()

    def play_text(self, text):
        tts = gTTS(text)
        voice_fname = config("PROJECT_DIR") + "voice.mp3"
        tts.save(voice_fname)
        self._create_and_set_media(voice_fname)
        self.play()

    def media_has_ended(self):
        return self.player.get_state() == vlc.State.Ended

    def is_playing(self):
        return self.player.is_playing()

    def await_end():
        while not self.media_has_ended():
            time.sleep(1)
        return True

    def _create_and_set_media(self, url):
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)
