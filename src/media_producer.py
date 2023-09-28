from pydub import AudioSegment
from pathlib import Path
from gtts import gTTS
from decouple import config
import requests


class MediaProducer:
    def text_to_mp3(self, text, fpath):
        tts = gTTS(text, lang="en", tld="com.au")
        tts.save(fpath)
        return fpath

    def url_to_mp3(self, url, fpath):
        response = requests.get(url)
        with open(fpath, "wb") as f:
            f.write(response.content)
        return fpath

    def combine_music_and_speech(
        self,
        music_path,
        speech_path,
        output_path,
        duck_db=-10.0,
        position="start",
        clip=False,
    ):
        """
        Combine music with speech and duck the music so the message is clear
        args:
        - music_path: mp3 of music
        - speech_path: mp3 of speech
        - output_fpath: mp3 of combined output
        - duck_db: amount of db to duck the music
        - position: where to place text in song ["start", "middle", "end"]
        - clip: whether to return only the slice where speech overlays the music
        """
        # Load the audio files
        music = AudioSegment.from_file(music_path)
        speech = AudioSegment.from_file(speech_path)

        # Get the length of the speech in milliseconds
        music_length = len(music)
        music_middle = music_length // 2
        speech_length = len(speech)

        # Split the music into two parts: during and after the speech
        if position == "start":
            before_speech = AudioSegment.empty()
            during_speech = music[:speech_length]
            after_speech = music[speech_length:]
        elif position == "middle":
            before_speech = music[:music_middle]
            during_speech = music[music_middle : music_middle + speech_length]
            after_speech = music[:music_middle]
        elif position == "end":
            before_speech = music[:-speech_length]
            during_speech = music[-speech_length:]
            after_speech = AudioSegment.empty()

        # Lower the volume of the music during the speech
        during_speech = during_speech + duck_db

        # Overlay the speech onto the 'during' music, then append 'after' music
        if clip:
            output = speech.overlay(during_speech)
        else:
            output = (
                before_speech + speech.overlay(during_speech) + after_speech
            )
        # Save the result
        output.export(output_path, format="mp3")
        return output_path

    def merge_mp3s(self, mp3_paths, output_fpath):
        "Merge multiple mp3s sequentially"

        # Initialize an empty AudioSegment to store the merged audio
        merged_audio = AudioSegment.empty()

        for mp3_path in mp3_paths:
            # Load the mp3 file
            audio = AudioSegment.from_file(mp3_path)

            # Append the current audio to the merged_audio
            merged_audio += audio

        # Export the merged audio as a new mp3 file
        merged_audio.export(output_fpath, format="mp3")
        return output_fpath

    def compress_audio(self, source_fpath, output_fpath, bitrate="64k"):
        audio = AudioSegment.from_file(source_fpath, format="mp3")
        audio.export(output_fpath, format="mp3", bitrate=bitrate)


if __name__ == "__main__":
    mp = MediaProducer()
    t_fname = "speech.mp3"
    m_fname = "music.mp3"
    mp.text_to_mp3("This is a message that you should hear well", t_fname)
    mp.url_to_mp3(
        "https://t4.bcbits.com/stream/4028cbaf56419bb343fb62590bf41b8e/mp3-128/822241906?p=0&ts=1691079497&t=2a27f64ae24dd3d44a11a405b4652643ece56a35&token=1691079497_d975dbfdc7880636ab176f74d877957dc523ca84",
        m_fname,
    )

    mp.music_with_ducking(m_fname, t_fname, "combined.mp3")
