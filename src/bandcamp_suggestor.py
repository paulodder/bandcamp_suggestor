import random
import time
import json
import requests

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# from pyvirtualdisplay import Display


class BandcampSuggestor:
    def __init__(self, username):
        self.username = username
        self.fan_id = None
        self.wishlist_items = None
        self._initialize_fan_id_and_older_than_token()

    def _initialize_fan_id_and_older_than_token(self):
        """Initialize fan_id and older_than_token as class attributes."""
        html = self._fetch_wishlist_html(self.username)
        self.older_than_token = self._extract_older_than_token(html)
        self.fan_id = self._extract_fan_id(html)

    def scrape_wishlist_items(self):
        """Scrape wishlist items if not already scraped."""
        if self.wishlist_items is None:
            print("Scraping wishlist items...")
            self.wishlist_items = self._fetch_wishlist_items(
                self.fan_id, self.older_than_token
            )

    def get_random_wishlist_item(self):
        """Retrieve a random wishlist item from the bandcamp wishlist"""
        self.scrape_wishlist_items()

        wishlist_item = self._get_random_wishlist_item()

        item_track_name = wishlist_item["item_title"]
        item_band_name = wishlist_item["band_name"]
        item_url = wishlist_item["item_url"]
        item_featured_track = None

        tralbum_id = wishlist_item["tralbum_id"]
        embed_url = self._construct_embed_url_from_tralbumid(tralbum_id)
        player_data = self._extract_player_data_from_embed_url(embed_url)

        stream_url = None
        if player_data is not None:
            _, _, stream_url = self._extract_title_artist_stream_url_from_data(
                player_data
            )

        return item_track_name, item_band_name, item_url, stream_url

    def generate_suggestions(self, bandcamp_url):
        """Generate track suggestions based on a bandcamp url"""

        tracks, artists, stream_urls = self._get_suggestions_for(bandcamp_url)
        return tracks, artists, stream_urls

    def _fetch_wishlist_html(self, username):
        """Fetch wishlist HTML for the given username."""
        return BeautifulSoup(
            requests.get(f"https://bandcamp.com/{username}/wishlist").content,
            features="html.parser",
        )

    def _extract_older_than_token(self, html):
        """Extract older_than_token from wishlist HTML."""
        lis = html.select(
            ".collection-item-container.track_play_hilite.initial-batch"
        )
        return lis[0].get("data-token")

    def _extract_fan_id(self, html):
        """Extract fan_id from wishlist HTML."""
        return (
            html.select_one("button.follow-unfollow").get("id").split("_")[-1]
        )

    def _fetch_wishlist_items(self, fan_id, older_than_token):
        """Fetch wishlist items using fan_id and older_than_token."""
        resp = requests.post(
            "https://bandcamp.com/api/fancollection/1/wishlist_items",
            headers={"User-Agent": "Mozilla/5.0"},
            json={
                "fan_id": fan_id,
                "older_than_token": older_than_token,
                "count": 2000,
            },
        )
        return resp.json()["items"]

    def _get_random_wishlist_item(self):
        """Return a random wishlist item."""
        return random.choice(self.wishlist_items)

    def _get_suggestions_for(self, url):
        """Get track and album suggestions for the given URL."""
        driver = self._init_selenium_driver()
        self._navigate_and_submit_url(driver, url)
        print("Waiting for bc-explorer suggestions to load...")
        iframes = self._wait_and_scrape_iframes(driver)
        driver.quit()
        return self._extract_tracks_artists_and_stream_urls(iframes)

    def _init_selenium_driver(self):
        """Initialize Selenium WebDriver with Chrome options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--enable-audio")
        # display = Display(visible=0, size=(800, 600))
        # display.start()
        return webdriver.Chrome(
            "/usr/lib/chromium-browser/chromedriver",
            options=chrome_options,
        )

    def _navigate_and_submit_url(self, driver, url):
        """Navigate to the website and submit the given URL."""
        driver.get("https://bc-explorer.app")
        input_bar = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//input[contains(@aria-label,'bandcamp') and contains(@aria-label,'explore')]",
                )
            )
        )
        input_bar.click()
        input_bar.send_keys(Keys.CONTROL, "a")
        input_bar.send_keys(Keys.BACKSPACE)
        input_bar.send_keys(url)
        submit_button = driver.find_element(
            By.XPATH, "//button[contains(@kind, 'secondaryFormSubmit')]"
        )
        submit_button.click()

    def _wait_and_scrape_iframes(self, driver):
        """Wait for iframes to load and scrape them."""
        WebDriverWait(driver, 60).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//iframe"))
        )
        time.sleep(1)  # make sure all iframes are loaded
        return BeautifulSoup(
            driver.page_source, features="html.parser"
        ).select("iframe")

    def _extract_tracks_artists_and_stream_urls(self, iframes):
        """Extract stream_urls, track and artist names from the iframes."""
        embed_urls = [iframe.get("src") for iframe in iframes]
        stream_urls = []
        tracks = []
        artists = []
        for embed_url in embed_urls:
            player_data = self._extract_player_data_from_embed_url(embed_url)

            (
                track_title,
                track_artist,
                stream_url,
            ) = self._extract_title_artist_stream_url_from_data(player_data)

            if track_title is None:
                continue

            tracks.append(track_title)
            artists.append(track_artist)
            stream_urls.append(stream_url)

        return tracks, artists, stream_urls

    def _extract_title_artist_stream_url_from_data(self, player_data):
        if self._is_album_dict(player_data):
            featured_track = self._get_featured_track_from_album(
                player_data["tracks"], player_data["featured_track_id"]
            )
        else:
            featured_track = player_data["tracks"][0]

        try:
            track_title = featured_track["title"]
            track_artist = featured_track["artist"]
            stream_url = featured_track["file"]["mp3-128"]
        except TypeError:
            return None, None, None

        return track_title, track_artist, stream_url

    def _extract_player_data_from_embed_url(self, embed_url):
        response = requests.get(embed_url)
        player = BeautifulSoup(response.content, features="html.parser")
        try:
            player_data = json.loads(
                player.find("script", attrs={"data-player-data": True}).get(
                    "data-player-data"
                )
            )
        except AttributeError:
            return None
        return player_data

    def _construct_embed_url_from_tralbumid(self, tralbum_id):
        return f"https://bandcamp.com/EmbeddedPlayer/album={tralbum_id}/"

    def _is_album_dict(self, player_data):
        """Returns a boolean indicating if the player plays is an album"""
        return "featured_track_id" in player_data

    def _get_featured_track_from_album(self, track_list, featured_track_id):
        """Returns the featured track from the album tracks"""
        for track in track_list:
            if track["id"] == featured_track_id:
                return track

    # def _get_random_track(self, tracks):
    #     """Return a random track from the list of tracks."""
    #     return random.choice(tracks)
