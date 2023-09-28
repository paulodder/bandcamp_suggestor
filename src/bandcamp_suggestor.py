import random
import time
import json
import requests
import re
import numpy as np
import platform
import time

from src.utils import remove_links
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

CTRL_KEY = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL


class BandcampSuggestor:
    def __init__(self, username):
        self.username = username
        self.fan_id = None
        self.wishlist_items = None
        self.collection_items = None
        self._initialize_fan_id_and_older_than_token()

    def _initialize_fan_id_and_older_than_token(self):
        """Initialize fan_id and older_than_token as class attributes."""
        html_wishlist = self._fetch_wishlist_html(self.username)
        self.older_than_token = self._generate_older_than_token()
        self.fan_id = self._extract_fan_id(html_wishlist)

    def scrape_wishlist_items(self):
        """Scrape wishlist items if not already scraped."""
        if self.wishlist_items is None:
            # print("Scraping wishlist items...")
            self.wishlist_items = self._fetch_wishlist_items(
                self.fan_id, self.older_than_token
            )

    def scrape_collection_items(self):
        """Scrape wishlist items if not already scraped."""
        if self.collection_items is None:
            # print("Scraping collection items...")
            self.collection_items = self._fetch_collection_items(
                self.fan_id, self.older_than_token
            )

    def get_random_wishlist_item(self):
        """Retrieve a random wishlist item from the bandcamp wishlist"""
        self.scrape_wishlist_items()

        wishlist_item = self._get_random_wishlist_item()

        return self._get_track_artist_bandcamp_url_stream_url_for_item(
            wishlist_item
        )

    def get_random_collection_item(self):
        """Retrieve a random collection item from the bandcamp wishlist"""
        self.scrape_collection_items()

        collection_item = self._get_random_collection_item()

        return self._get_track_artist_bandcamp_url_stream_url_for_item(
            collection_item
        )

    def get_random_items(self, n=5):
        """
        Retrieve n random collection items from both the bandcamp wishlist
        and collection.
        """

        self.scrape_wishlist_items()
        self.scrape_collection_items()
        items = [
            self._get_track_artist_bandcamp_url_stream_url_for_item(x)
            for x in self._get_random_items(n)
        ]
        return items

    def _get_track_artist_bandcamp_url_stream_url_for_item(self, item):
        item_track_name = item["item_title"]
        item_band_name = item["band_name"]
        item_url = item["item_url"]

        tralbum_id = item["tralbum_id"]
        embed_url = self._construct_embed_url_from_tralbumid(tralbum_id)
        player_data = self._extract_player_data_from_embed_url(embed_url)

        stream_url = None
        if player_data is not None:
            _, _, stream_url = self._extract_title_artist_stream_url_from_data(
                player_data
            )

        return item_track_name, item_band_name, item_url, stream_url

    def generate_suggestions(self, bandcamp_url, print_info=True):
        """Generate track suggestions based on a bandcamp url"""
        (
            tracks,
            artists,
            bandcamp_urls,
            stream_urls,
        ) = self._get_suggestions_for(bandcamp_url, print_info=print_info)
        return tracks, artists, bandcamp_urls, stream_urls

    def fetch_info_from_bancamp_url(self, bandcamp_url):
        """Fetches info from the bandcamp track/album page"""
        bc_page = self._get_bandcamp_page(bandcamp_url)
        info = {
            "description": None,
            "duration": None,
            "tags": [],
            "country": None,
        }

        # Get important description
        full_description = self._extract_full_description(
            bc_page, bandcamp_url
        )

        if full_description is not None:
            description = (
                self._extract_most_important_paragraph_from_description(
                    full_description
                )
            )
            info["description"] = remove_links(description)

        tag_links = bc_page.find(
            "div", attrs={"class": "tralbum-tags"}
        ).find_all("a")
        tags = [x.text for x in tag_links]
        info["tags"] = tags[:-1]
        info["country"] = tags[-1]
        # breakpoint()
        return info

    def get_title_artist_stream_url_from_url(self, bandcamp_url):
        response = requests.get(bandcamp_url)
        bs = BeautifulSoup(response.content, features="html.parser")
        bs_script = bs.find("script", attrs={"data-tralbum": True})
        data_band = json.loads(bs_script.get("data-band"))
        data_tralbum = json.loads(bs_script.get("data-tralbum"))
        track = data_tralbum.get("trackinfo")[0]
        title = track["title"]
        artist = data_band["name"]
        stream_url = track["file"]["mp3-128"]
        return title, artist, stream_url

    def _get_bandcamp_page(self, bandcamp_url):
        response = requests.get(bandcamp_url)
        return BeautifulSoup(response.content, features="html.parser")

    def _extract_full_description(self, bandcamp_page, bandcamp_url):
        """Get the full description based on a bandcamp page"""
        info = json.loads(
            bandcamp_page.find(
                "script", attrs={"type": "application/ld+json"}
            ).text
        )
        if self._is_bandcamp_track_link(bandcamp_url):
            album_url = info["inAlbum"]["albumRelease"][0]["@id"]
            if not self._is_bandcamp_track_link(album_url):
                return self._extract_full_description(
                    self._get_bandcamp_page(album_url), album_url
                )

        return info.get("description")

    def _is_bandcamp_track_link(self, href):
        """Returns if the given href is a bandcamp track link"""
        return "/track" in href

    def _extract_most_important_paragraph_from_description(self, description):
        """Extract the first important paragraph from the full the description text"""
        paragraphs = np.array(re.split(r"\r\n ?\r\n", description))
        if len(paragraphs) > 1:
            p_scores = np.array([self._score_paragraph(p) for p in paragraphs])
            p_relevant = paragraphs[p_scores >= p_scores.mean()]
            return p_relevant[0]
        else:
            return paragraphs[0]

    def _score_paragraph(self, p):
        """Whack estimator based on the amount of newlines and punctuation marks"""
        return len(p) / max(1, len(re.findall(r"[.,:\n]", p)))

    def _fetch_wishlist_html(self, username):
        """Fetch wishlist HTML for the given username."""
        return BeautifulSoup(
            requests.get(f"https://bandcamp.com/{username}/wishlist").content,
            features="html.parser",
        )

    def _generate_older_than_token(self):
        """Generate an older_than_token."""
        return f"{int(time.time())}::a::"

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

    def _fetch_collection_items(self, fan_id, older_than_token):
        """Fetch collection items using fan_id and older_than_token."""
        resp = requests.post(
            "https://bandcamp.com/api/fancollection/1/collection_items",
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

    def _get_random_collection_item(self):
        """Return a random collection item."""
        return random.choice(self.collection_items)

    def _get_random_items(self, n):
        """Return n random items from wishlist or collection."""
        return random.sample(self.wishlist_items + self.collection_items, n)

    def _get_suggestions_for(self, url, print_info=True):
        """Get track and album suggestions for the given URL."""
        driver = self._init_selenium_driver()
        self._navigate_and_submit_url(driver, url)

        if print_info:
            print("Waiting for bc-explorer suggestions to load...")
        iframes = self._wait_and_scrape_iframes(driver)

        driver.quit()
        return self._extract_tracks_artists_and_urls(iframes)

    def _init_selenium_driver(self):
        """Initialize Selenium WebDriver with Chrome options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        return webdriver.Chrome(
            "/usr/local/bin/chromedriver",
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
        input_bar.send_keys(CTRL_KEY, "a")
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

    def _extract_tracks_artists_and_urls(self, iframes):
        """Extract track name, artist name, bandcamp and stream urls from iframes."""
        tracks = []
        artists = []
        bandcamp_urls = []
        stream_urls = []
        for iframe in iframes:
            embed_url = iframe.get("src")
            bandcamp_url = iframe.select_one("a").get("href")
            player_data = self._extract_player_data_from_embed_url(embed_url)

            if player_data is None:
                continue

            (
                track_title,
                track_artist,
                stream_url,
            ) = self._extract_title_artist_stream_url_from_data(player_data)

            if track_title is None:
                continue

            tracks.append(track_title)
            artists.append(track_artist)
            bandcamp_urls.append(bandcamp_url)
            stream_urls.append(stream_url)

        return tracks, artists, bandcamp_urls, stream_urls

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
