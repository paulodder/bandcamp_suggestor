import time
import random
import asyncio
from decouple import config
from pathlib import Path
from collections import defaultdict
from pydub.utils import mediainfo
from src.media_producer import MediaProducer
from src.bandcamp_suggestor import BandcampSuggestor
from src.utils import (
    get_date_str,
    clear_directory_recursive,
    generate_paths,
    save_json,
    change_suffix,
)
from src.constants import (
    first_time_greeting,
    short_continue,
    mid_continue,
    long_continue,
)
from src.song_filter import SongFilter


class RadioGenerator:
    def __init__(self, bc_user=None):
        self.mp = MediaProducer()
        self.bc_user = config("BANDCAMP_USER") if bc_user is None else bc_user
        self.bc = BandcampSuggestor(self.bc_user)
        self.tag_filter = SongFilter(Path(config("PROJECT_DIR")) / "tags.json")
        self.mp3_path = Path(config("MP3_DIR"))
        self.tmp_dir = self.mp3_path / "tmp"
        self.tmp_dir.mkdir(exist_ok=True, parents=True)
        self.slice_dir = Path(config("MP3_DIR")) / "slices"
        self.slice_dir.mkdir(exist_ok=True, parents=True)

    async def continuous_generate_radio(self, mp_queue, min_slices=5):
        """Checks if there are enough radio slices lined up. If not, generates
        more slices. Run in a separate process"""
        tasks = []
        while True:
            existing_slices = self._get_existing_slices()

            for _ in range(min_slices - len(existing_slices)):
                print("* generating slice *")
                radio_fpath = generate_paths(self.slice_dir, ["bkradio"])[
                    "bkradio"
                ]
                tracklist, times = self.generate_radio(
                    radio_fpath, n_source_songs=1, n_recs_per_song=2
                )
                # print("TRACKLIST\n", tracklist)
                # print("TIMES\n", times)

                info_fpath = change_suffix(radio_fpath, ".json")
                save_json(info_fpath, {"tracklist": tracklist, "times": times})

                mp_queue.put(radio_fpath)

            await asyncio.sleep(15)

    def generate_radio(
        self,
        output_fpath,
        n_source_songs=3,
        n_recs_per_song=2,
        intro_speech=False,
    ):
        comb_fpaths = []
        time_start = 0
        if intro_speech:
            intro_speech_fpath = self.generate_intro_speech()
            comb_fpaths.append(intro_speech_fpath)
            time_start = self._get_mp3_duration(intro_speech_fpath)

        source_songs = self.bc.get_random_items(n_source_songs)
        tracklist = []
        all_times = []

        for i, song in enumerate(source_songs):
            # paths = self._create_paths(i)
            slice_fpath, tracklist_slice, times = self.generate_slice_for_song(
                song,
                n_recs_per_song=n_recs_per_song,
                time_start=time_start,
            )

            all_times += times
            tracklist += tracklist_slice

            # Append the combined path for each slice
            comb_fpaths.append(slice_fpath)

        # Merging all slices into the final combined MP3 file
        self.mp.merge_mp3s(comb_fpaths, output_fpath)

        # clear_directory_recursive(self.tmp_dir, include_topdir=True)
        return tracklist, all_times

    def generate_intro_speech(self, min_since_last_use=None):
        intro_speech_fpath = generate_paths(self.tmp_dir, ["intro-speech"])[
            "intro-speech"
        ]

        if min_since_last_use is None:
            text = f"This is {self.bc_user}'s boomkètèl radio for the {get_date_str()}."
        elif min_since_last_use == -1:
            text = first_time_greeting
        elif min_since_last_use < 20:
            text = random.choice(mid_continue)
        elif min_since_last_use > 21600:
            text = random.choice(long_continue)
        else:
            text = random.choice(mid_continue)

        self.mp.text_to_mp3(
            text,
            intro_speech_fpath,
        )
        return intro_speech_fpath

    def generate_slice_for_song(self, song, n_recs_per_song=3, time_start=0):
        """
        song should be the following tuple: (track, band, url, stream_url)
        """
        # source_songs = self.bc.get_random_items(1)
        (
            source_track,
            source_band,
            source_url,
            source_stream_url,
        ) = song
        # print(f"{'based on: ':<10}{source_track} - {source_band}")
        src_artist_track_str = f"{source_band} - {source_track}"

        # tracklist_msg = f'{"based on: ":<10}<a href="{source_url}">{source_track} - {source_band}</a>\n'
        # song_infos = []
        tracklist = []

        comb_fpaths = []
        fpaths = generate_paths(self.tmp_dir, ["speech", "music", "combined"])

        text = f"We're gonna listen to some tunes based on {source_track}, by {source_band}."
        self.mp.text_to_mp3(text, fpaths["speech"])

        if source_stream_url is not None:
            self.mp.url_to_mp3(source_stream_url, fpaths["music"])
            self.mp.combine_music_and_speech(
                fpaths["music"],
                fpaths["speech"],
                fpaths["combined"],
                position="middle",
                clip=True,
            )
            comb_fpaths.append(fpaths["combined"])
        else:
            comb_fpaths.append(fpaths["speech"])

        time = time_start + self._get_mp3_duration(comb_fpaths[0])
        times = []

        suggestions = self.bc.generate_suggestions(
            source_url, print_info=False
        )

        tracks, artists, bandcamp_urls, stream_urls = suggestions

        j = 0
        while j < n_recs_per_song:
            # song_info = {
            #     "based_on": {
            #         "artist_track": src_artist_track_str,
            #         "url": source_url,
            #     }
            # }
            bc_info = self.bc.fetch_info_from_bancamp_url(bandcamp_urls[j])

            if not self.tag_filter.is_song_allowed(bc_info["tags"]):
                j += 1
                # print("filtering track based on tags")
                continue
            # print(f"{artists[j]} - {tracks[j]}", end="")

            fpaths = generate_paths(
                self.tmp_dir,
                ["speech", "speech-end", "music", "combined"],
            )

            description = bc_info["description"]
            text = ""
            if description is not None and len(description.split()) <= 75:
                text = description + ". "
            text += f"This track by {artists[j]} is called {tracks[j]}"
            self.mp.text_to_mp3(text, fpaths["speech"])
            self.mp.url_to_mp3(stream_urls[j], fpaths["music"])
            self.mp.combine_music_and_speech(
                fpaths["music"],
                fpaths["speech"],
                fpaths["combined"],
                position="start",
            )

            end_text = f"We listened to {tracks[j]}, by {artists[j]}."
            # if j == n_recs_per_song - 1:
            #     end_text += " That concludes today's boomkètèl radio, hope you enjoyed this selection of tracks, see you next time!"
            self.mp.text_to_mp3(end_text, fpaths["speech-end"])
            self.mp.combine_music_and_speech(
                fpaths["combined"],
                fpaths["speech-end"],
                fpaths["combined"],
                position="end",
                duck_db=-2.0,
            )

            comb_fpaths.append(fpaths["combined"])

            # song_info["time_start"].append(round(time))
            times.append(round(time))
            song_length = self._get_mp3_duration(fpaths["combined"])
            time += song_length

            # song_info["artist_track"] = f"{artists[j]} - {tracks[j]}"
            # song_info["url"] = bandcamp_urls[j]
            # song_info[
            #     "message"
            # ] = f'{song_info["artist_track"]}\n<a href="{song_info["url"]}">bandcamp link</a>'

            tracklist.append(
                f'{artists[j]} - {tracks[j]}\n<a href="{bandcamp_urls[j]}">bandcamp link</a>'
            )
            # time_str = f"{self._seconds2minutes_seconds(times[-2])}"
            # print(f" ({time_str})")
            # print(f"{'':<4}{bandcamp_urls[j]}")
            # if bc_info["tags"]:
            # print(f"{'':<4}{', '.join(bc_info['tags'])}")

            # song_infos.append(song_info)
            j += 1

        slice_fpath = generate_paths(self.tmp_dir, ["slice"])["slice"]
        self.mp.merge_mp3s(comb_fpaths, slice_fpath)

        # print(song_infos)

        return slice_fpath, tracklist, times

    def _get_mp3_duration(self, file_path, round=False):
        duration = float(mediainfo(file_path)["duration"])
        if round is True:
            return round(duration)
        return duration

    def _seconds2minutes_seconds(self, time_seconds):
        minutes = time_seconds // 60
        seconds = time_seconds % 60
        duration = f"{minutes:02}:{seconds:02}"
        return duration

    def _get_existing_slices(self):
        return list(self.slice_dir.glob("*_bkradio_*.mp3"))

    # def _create_paths(self, suffixes=["speech", "music", "combined"]):
    #     paths = {}
    #     timestamp = str(int(time.time()))
    #     unique_str = f"{timestamp}{random.randint(0, 9999)}"
    #     for suffix in suffixes:
    #         paths[suffix] = self.tmp_dir / f"{unique_str}_{suffix}.mp3"
    #     return paths
