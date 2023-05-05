import time
from decouple import config

from src.utils import connection_is_active
from src.pi_buttons import RPButtons
from src.bandcamp_suggestor import BandcampSuggestor
from src.media_player import MediaPlayer


def main():
    try:
        player = MediaPlayer()

        if not connection_is_active():
            print("ERROR: No internet connection was established")
            player.play_from_url(config("PROJECT_DIR") + "mp3/no_internet.mp3")
            player.await_end()
            quit()

        bc_suggestor = BandcampSuggestor(config("BANDCAMP_USER"))
        buttons = RPButtons([23, 24])

        player.play_text(f"Welcome to Boemketel Radio.")
        player.await_end()

        while True:
            play_radio_for_random_wishlist_item(player, bc_suggestor, buttons)

    except Exception as e:
        print(e)
        player.play_from_url(config("PROJECT_DIR") + "mp3/error.mp3")
        player.await_end()
        return


def play_radio_for_random_wishlist_item(player, bc_suggestor, buttons):
    (
        source_track,
        source_band,
        source_url,
        source_stream_url,
    ) = bc_suggestor.get_random_wishlist_item()

    print(f"Searching based on {source_track} - {source_band}")
    player.play_text(
        f"Searching for new boemketel hits based on your bandcamp wishlist item: {source_track}, by {source_band}.",
    )
    if await_player_and_monitor_return_request(player, buttons):
        return

    if source_stream_url is None:
        player.play_text(
            f"Please get me a drink while I think in silence",
        )
        if await_player_and_monitor_return_request(player, buttons):
            return
    else:
        player.play_text(
            f"Let me remind you while I think..",
        )
        if await_player_and_monitor_return_request(player, buttons):
            return

        player.play_from_url(source_stream_url)

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

        if await_player_and_monitor_return_request(player, buttons):
            return

        print("playing", track, "-", artist)
        player.play_from_url(stream_url)

        if await_player_and_monitor_return_request(
            player, buttons, f"{track} by {artist}"
        ):
            return

        player.play_text(f"that was, {track}, by {artist}")
        if await_player_and_monitor_return_request(player, buttons):
            return

    player.play_text(
        f"That concludes all recommendations based on {source_track}, by {source_band}."
    )
    player.await_end()


def await_player_and_monitor_return_request(player, buttons, play_msg=None):
    while True:
        button_pressed = buttons.button_pressed()
        if button_pressed is not False:
            if button_pressed == 0 and player.is_playing():
                print("Pausing playback")
                player.pause()
            elif button_pressed == 0 and not player.is_playing():
                print("Resuming playback")
                if play_msg:
                    player2 = MediaPlayer()
                    player2.play_text(play_msg)
                    player2.await_end()
                player.play()
            elif button_pressed == 1:
                print("Next wishlist item")
                player.pause()
                return True
            time.sleep(0.5)

        if player.media_has_ended():
            return False
        time.sleep(0.1)


if __name__ == "__main__":
    while True:
        main()
