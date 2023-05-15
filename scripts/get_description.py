from src.bandcamp_suggestor import BandcampSuggestor
from decouple import config

# from src.media_player import MediaPlayer

bc = BandcampSuggestor(config("BANDCAMP_USER"))
