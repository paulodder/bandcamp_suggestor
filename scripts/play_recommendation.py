import time
import traceback
import sys
import random
from decouple import config

from src.utils import connection_is_active
from src.bandcamp_suggestor import BandcampSuggestor
from src.media_player import MediaPlayer

try:
    from src.pi_buttons import RPButtons

    IS_RASPBERYY_PI = True
except (ImportError, RuntimeError):
    import keyboard

    # TODO: fix so it only works when wanted
    # print("press p to pause/play, press n for next wishlist item")

    IS_RASPBERYY_PI = False


def main(bandcamp_url=None):
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
            play_radio_for_wishlist_item(
                player, bc_suggestor, buttons, bandcamp_url
            )

    except Exception as e:
        print(traceback.format_exc())
        player.play_from_url(config("PROJECT_DIR") + "mp3/error.mp3")
        player.await_end()
        return


def play_radio_for_wishlist_item(
    player, bc_suggestor, buttons=None, wishlist_url=None
):
    if wishlist_url is None:
        if random.random() > 0.9:
            fetch_fn = bc_suggestor.get_random_collection_item
            source_text = "your bandcamp purchase"
        else:
            fetch_fn = bc_suggestor.get_random_wishlist_item
            source_text = "your bandcamp wishlist item"
        (
            source_track,
            source_band,
            source_url,
            source_stream_url,
        ) = fetch_fn()
    else:
        (
            source_track,
            source_band,
            source_stream_url,
        ) = bc_suggestor.get_title_artist_stream_url_from_url(wishlist_url)
        source_url = wishlist_url
        source_text = ""

    print(f"Searching based on {source_track} - {source_band}")
    player.play_text(
        f"Searching for new boomkètèl hits based on {source_text}: {source_track}, by {source_band}.",
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


def monitor_keyboard():
    # TODO: fix so it only works when wanted
    # if keyboard.is_pressed("p"):
    #     return 0
    # if keyboard.is_pressed("n"):
    #     return 1
    return False


def await_player_and_monitor_return_request(
    player, buttons=None, play_msg=None
):
    if IS_RASPBERYY_PI:
        input_monitor_fn = buttons.button_pressed
    else:
        input_monitor_fn = monitor_keyboard

    while True:
        button_pressed = input_monitor_fn()
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
                print("Next wishlist player")
                item.pause()
                return True
            time.sleep(0.5)

        if player.media_has_ended():
            return False
        time.sleep(0.1)


def get_args():
    if len(sys.argv) > 1:
        if "bandcamp.com" in sys.argv[1]:
            return {"bandcamp_url": sys.argv[1]}
        else:
            raise Exception(
                "please provide a valid bandcamp album or track link"
            )
    return {"bandcamp_url": None}


if __name__ == "__main__":
    args = get_args()
    while True:
        main(args["bandcamp_url"])
