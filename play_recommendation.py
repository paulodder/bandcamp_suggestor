from bandcamp_suggestor import BandcampSuggestor
from media_player import MediaPlayer

player = MediaPlayer()
bc_suggestor = BandcampSuggestor("adriaanscholtens")
track, artist, stream_url = bc_suggestor.generate_suggestion()

print("playing", track, "by", artist)
player.stream_from_url(stream_url)
