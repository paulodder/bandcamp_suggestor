import time

from bandcamp_suggestor import BandcampSuggestor
from media_player import MediaPlayer

player = MediaPlayer()
bc_suggestor = BandcampSuggestor("adriaanscholtens")
source_track, source_band, source_url = bc_suggestor.get_random_wishlist_item()
player.play_text(
    f"Searching new boemketel hits based on your wishlist item: {source_track}, by {source_band}",
    sleep=False,
)

# some elevator music for the wait
# player.play_from_url("elevator_music.mp3", sleep=False)

tracks, artists, stream_urls = bc_suggestor.generate_suggestions(source_url)

for track, artist, stream_url in zip(tracks, artists, stream_urls):
    player.pause()
    time.sleep(1)
    print("announcing", track, "-", artist)
    player.play_text(
        f"The following bangèr is by {artist}, the track is called {track}"
    )

    print("playing", track, "-", artist)
    player.play_from_url(stream_url)

    player.play_text(f"that was, {track}, by artist")
