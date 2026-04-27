import discum
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
GUILD_ID = os.getenv("GUILD_ID", "your-guild-id")  # Guild (server) ID
CHANNEL_ID = os.getenv("CHANNEL_ID", "your-channel-id")  # Channel ID
REMOTE_SERVER_URL = os.getenv("REMOTE_SERVER_URL", "https://your-api-endpoint.com")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", "/path/to/chromedriver")  # Path to ChromeDriver

# Class for Token Management
class TokenManager:
    def __init__(self, driver_path):
        self.driver_path = driver_path

    def extract_token(self):
        """Extract Tokens from localStorage."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(executable_path=self.driver_path, options=chrome_options)
        try:
            driver.get("https://discord.com/login")
            time.sleep(3)  # Wait for the login page to load
            token = driver.execute_script("return localStorage.getItem('token');")
            if token:
                print("[SUCCESS] Token Extracted:", token[:20], "...")
                return token
            else:
                print("[INFO] No token found.")
        finally:
            driver.quit()

# Class for Scraping Members
class Scraper:
    def __init__(self, guild_id, channel_id, token):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.token = token

    def scrape_members(self):
        """Scrape members from the guild."""
        client = discum.Client(token=self.token, log=False)
        client.gateway.fetchMembers(self.guild_id, self.channel_id, keep="all")

        @client.gateway.command
        def scraper(resp):
            if client.gateway.finishedMemberFetching(self.guild_id):
                client.gateway.close()

        client.gateway.run()
        members = client.gateway.session.guild(self.guild_id).members
        print(f"[SUCCESS] Scraped {len(members)} members.")
        return members

# Main Function
def main():
    token_manager = TokenManager(CHROME_DRIVER_PATH)
    token = token_manager.extract_token()
    if not token:
        print("[ERROR] No token found.")
        return

    scraper = Scraper(GUILD_ID, CHANNEL_ID, token)
    members = scraper.scrape_members()

    # Send members to server
    try:
        response = requests.post(REMOTE_SERVER_URL, json={"members": members})
        if response.status_code == 200:
            print("[SUCCESS] Data sent to server.")
        else:
            print(f"[ERROR] Failed to send data: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Server communication failed: {e}")

if name == "__main__":
    main()