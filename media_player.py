import vlc


class MediaPlayer:
    def __init__(self):
        self.vlc_instance = vlc.Instance("--aout=alsa")
        self.player = self.vlc_instance.media_player_new()

    def stream_from_url(self, url):
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)
        self.play()

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()
