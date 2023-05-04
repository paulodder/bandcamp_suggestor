import time
import requests
from decouple import config

from src.bandcamp_suggestor import BandcampSuggestor
from src.media_player import MediaPlayer


def main(player, bc_suggestor):
    (
        source_track,
        source_band,
        source_url,
        source_stream_url,
    ) = bc_suggestor.get_random_wishlist_item()

    print(f"Searching based on {source_track} - {source_band}")
    player.play_text(
        f"Searching for new boemketel hits based on {source_track}, by {source_band}.",
    )

    if source_stream_url is None:
        player.play_text(
            f"I can't find the stream url for this track. Maybe you can get me a drink while I think in silence",
        )
    else:
        player.play_text(
            f"Let me remind you while I think..",
        )
        player.play_from_url(source_stream_url, sleep=False)

    # some elevator music for the wait
    # player.play_from_url("elevator_music.mp3", sleep=False)

    tracks, artists, stream_urls = bc_suggestor.generate_suggestions(
        source_url
    )

    for i, (track, artist, stream_url) in enumerate(
        zip(tracks, artists, stream_urls)
    ):
        player.pause()
        if i == 0:
            if source_stream_url is None:
                player.play_text(
                    f"It took me a while but I found another bangèr. I present to you: {track} by {artist}"
                )
            else:
                player.play_text(
                    f"Based on that, I recommend the following bangèr by {artist}, the track is called {track}"
                )
        else:
            player.play_text(
                f"We continue the party with {track}, by {artist}"
            )

        print("playing", track, "-", artist)
        player.play_from_url(stream_url)

        player.play_text(f"that was, {track}, by {artist}")

    player.play_text(
        f"That concludes all recommendations based on {source_track}, by {source_band}."
    )


def connection_is_active():
    attempts = 0
    while attempts < 20:
        try:
            requests.head("http://www.google.com/", timeout=1)
            return True
        except requests.ConnectionError:
            time.sleep(1)

    return False


if __name__ == "__main__":

    if not connection_is_active():
        print("ERROR: No internet connection was established")
        quit()

    player = MediaPlayer()
    bc_suggestor = BandcampSuggestor(config("BANDCAMP_USER"))

    while True:
        main(player, bc_suggestor)
