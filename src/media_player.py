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

    def get_volume(self):
        return self.player.audio_get_volume()

    def set_volume(self, volume):
        if volume < 0 or volume > 100:
            raise ValueError("Volume should be between 0 and 100")
        self.player.audio_set_volume(volume)

    def play_from_url(self, url, volume=100):
        if volume != self.get_volume():
            self.set_volume(volume)

        self._create_and_set_media(url)
        self.play()

    def play_text(self, text):
        tts = gTTS(text)
        voice_fname = config("PROJECT_DIR") + "mp3/voice.mp3"
        tts.save(voice_fname)
        self._create_and_set_media(voice_fname)
        self.play()

    def media_has_ended(self):
        return self.player.get_state() == vlc.State.Ended

    def is_playing(self):
        return self.player.is_playing()

    def await_end(self):
        while not self.media_has_ended():
            time.sleep(1)
        return True

    def _create_and_set_media(self, url):
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)
