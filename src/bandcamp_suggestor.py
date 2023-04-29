import random
import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


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

    def generate_suggestion(self):
        """Generate a random track suggestion."""
        self.scrape_wishlist_items()

        wishlist_item = self._get_random_wishlist_item()
        item_url = wishlist_item["item_url"]

        tracks, albums = self._get_suggestions_for(item_url)
        return self._get_random_track(tracks)

    def _fetch_wishlist_html(self, username):
        """Fetch wishlist HTML for the given username."""
        return BeautifulSoup(
            requests.get(f"https://bandcamp.com/{username}/wishlist").content
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
        return self._extract_tracks_and_albums(iframes)

    def _init_selenium_driver(self):
        """Initialize Selenium WebDriver with Chrome options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        return webdriver.Chrome(options=chrome_options)

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
        return BeautifulSoup(driver.page_source).select("iframe")

    def _extract_tracks_and_albums(self, iframes):
        """Extract track and album URLs from the iframes."""
        hrefs = [iframe.select_one("a").get("href") for iframe in iframes]
        tracks, albums = [], []
        for href in hrefs:
            if "/track" in href:
                tracks.append(href)
            elif "/album" in href:
                albums.append(href)
        return tracks, albums

    def _get_random_track(self, tracks):
        """Return a random track from the list of tracks."""
        return random.choice(tracks)
