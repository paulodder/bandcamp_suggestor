import time
from decouple import config

from src.utils import connection_is_active
from src.bandcamp_suggestor import BandcampSuggestor
from src.media_player import MediaPlayer

try:
    from src.pi_buttons import RPButtons

    IS_RASPBERYY_PI = True
except (ImportError, RuntimeError):
    IS_RASPBERYY_PI = False


def main():
    try:
        player = MediaPlayer()

        if not connection_is_active():
            print("ERROR: No internet connection was established")
            player.play_from_url(config("PROJECT_DIR") + "mp3/no_internet.mp3")
            player.await_end()
            quit()

        bc_suggestor = BandcampSuggestor(config("BANDCAMP_USER"))
        buttons = RPButtons([23, 24]) if IS_RASPBERYY_PI else None

        player.play_text(f"Welcome to Boomkètèl Radio.")
        player.await_end()

        while True:
            play_radio_for_random_wishlist_item(player, bc_suggestor, buttons)

    except Exception as e:
        print(e)
        player.play_from_url(config("PROJECT_DIR") + "mp3/error.mp3")
        player.await_end()
        return


def play_radio_for_random_wishlist_item(player, bc_suggestor, buttons=None):
    (
        source_track,
        source_band,
        source_url,
        source_stream_url,
    ) = bc_suggestor.get_random_wishlist_item()

    print(f"Searching based on {source_track} - {source_band}")
    player.play_text(
        f"Searching for new boomkètèl hits based on your bandcamp wishlist item: {source_track}, by {source_band}.",
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

    (
        tracks,
        artists,
        bandcamp_urls,
        stream_urls,
    ) = bc_suggestor.generate_suggestions(source_url)

    for i, (track, artist, bandcamp_url, stream_url) in enumerate(
        zip(tracks, artists, bandcamp_urls, stream_urls)
    ):
        player.pause()

        description = bc_suggestor.fetch_important_description(bandcamp_url)
        print("track:", track)
        print("artist:", artist)
        print("bandcamp_url:", bandcamp_url)
        if description is not None:
            print(f"reading description")
            print(description)
            read_text = (
                description + f". This track by {artist} is called {track}"
            )
        elif i == 0:
            if source_stream_url is None:
                read_text = f"It took me a while but I found another bangèr. I present to you: {track}, by {artist}"
            else:
                read_text = f"Based on that, I recommend the following bangèr by {artist}, the track is called {track}"
        else:
            read_text = f"We continue the party with {track}, by {artist}"

        player.play_text(read_text)

        if await_player_and_monitor_return_request(player, buttons):
            return

        print("playing")
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


def await_player_and_monitor_return_request(
    player, buttons=None, play_msg=None
):
    while True:
        if IS_RASPBERYY_PI:
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
