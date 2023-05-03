import time
from decouple import config

from src.bandcamp_suggestor import BandcampSuggestor
from src.media_player import MediaPlayer

player = MediaPlayer()
bc_suggestor = BandcampSuggestor(config("BANDCAMP_USER"))
(
    source_track,
    source_band,
    source_url,
    source_stream_url,
) = bc_suggestor.get_random_wishlist_item()

print(f"Searching based on {source_track} - {source_band}")
player.play_text(
    f"Searching for new boemketel hits based on {source_track}, by {source_band}. Let me remind you while I think..",
    sleep=True,
)

# some elevator music for the wait
# player.play_from_url("elevator_music.mp3", sleep=False)

player.play_from_url(source_stream_url, sleep=False)

tracks, artists, stream_urls = bc_suggestor.generate_suggestions(source_url)

for i, (track, artist, stream_url) in enumerate(
    zip(tracks, artists, stream_urls)
):
    player.pause()
    time.sleep(1)
    if i == 0:
        player.play_text(
            f"Based on that, I recommend the following bangèr by {artist}, the track is called {track}"
        )
    else:
        player.play_text(f"We continue the party with {track}, by {artist}")

    print("playing", track, "-", artist)
    player.play_from_url(stream_url)

    player.play_text(f"that was, {track}, by {artist}")
