# python3 -m pip install selenium
# import selenium
# python3 -m pip install webdriver-manager
# https://sites.google.com/a/chromium.org/chromedriver/downloads
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

# for getting the top hits for a search term
# pip install youtube_search
# from youtube_search import YoutubeSearch
# or just get these ones
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time




class QuoteHandler():
    def __init__(self):
        # accessing the page holding comments (here: youtube)
        # self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        self.scroll_pause_sec = 2
        self.num_cycles = 7
        self.max_find_elem_attempts = 3
        self.base_url = "https://www.youtube.com"

    # do a search on youtube and return the n top hits for that term
    # code used from: https://pypi.org/project/youtube-search/
    def get_videos(self, search_term, n=1):
        # get all videos related to this term
        encoded_search = urllib.parse.quote(search_term)
        query_prefix = "/results?search_query="
        url = self.base_url + query_prefix + encoded_search + "&pbj=1"
        # go over all links to actual videos
        links = self.get_video_links(soup)
        if links is None:
            print("No results for this search term")
            return []
        elif len(links) < n:
            # set the maximum number of links to the total number found
            n = len(links)

        # return full urls to the top n videos
        urls = [self.base_url + link for link in links[:n]]
        return urls

    # get all the links to videos hidden in a single html page
    # code used from: https://pypi.org/project/youtube-search/
    def get_video_links(self, url):
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        links = []
        # look for video boxes
        for video in soup.select(".yt-uix-tile-link"):
            # get the links to videos
            if video["href"].startswith("/watch?v="):
                video_info = {
                    "title": video["title"],
                    "link": video["href"],
                    "id": video["href"][video["href"].index("=")+1:]
                }
                video_link = video["href"]
                links.append(video_link)
        # return all video links on this page
        return links

    def get_comments(self, page_url):
        # go to the given page
        self.driver.get(page_url)

        # pause the video
        video = self.driver.find_element_by_css_selector("video")
        # self.driver.execute_script("arguments[0].play();", video)
        self.driver.execute_script("arguments[0].pause();", video)

        # get the video's title
        elems = self.find_elements('//*[@id="container"]/h1/yt-formatted-string')
        title = elems[0].text

        # we know there's always exactly one HTML element, so let's access it
        html = self.driver.find_element_by_tag_name('html')
        # first time needs to not jump to the very end in order to start
        html.send_keys(Keys.PAGE_DOWN)  # doing it twice for good measure
        html.send_keys(Keys.PAGE_DOWN)  # one time sometimes wasn't enough
        # adding extra time for initial comments to load
        # if they fail (because too little time allowed), the whole script breaks
        time.sleep(self.scroll_pause_sec * 3)
        # and now for loading the hidden comments by scrolling down and up
        for i in range(self.num_cycles):
            html.send_keys(Keys.END)
            time.sleep(self.scroll_pause_sec)

        comment_elems = self.find_elements('//*[@id="content-text"]')
        all_comments = [elem.text for elem in comment_elems]

        return all_comments

    # waits for a given element to get loaded, and returns it when it exists
    def find_elements(self, xpath):
        attempt = 0
        # reload the page until we find the element
        while attempt < self.max_find_elem_attempts:
            try:
                elems = self.driver.find_elements_by_xpath(xpath)
                # sometimes you find the element, but the content in it is not yet loaded
                if len(elems) == 0:
                    attempt += 1
                    time.sleep(1)
                else:
                    return elems
            # wait for the page to fully load
            except NoSuchElementException:
                attempt += 1
                time.sleep(1)
        # TODO decide what to do when we cant find this element
        print("Could not find element: " + xpath)
        exit(0)
        return None

    # gets the user channel that posted the most videos related to the given search term
    def get_channel(self, search_term):
        # search for youtube videos with this term
        encoded_search = urllib.parse.quote(search_term)
        query_prefix = "/results?search_query="
        url = self.base_url + query_prefix + encoded_search
        # grab all the content of the html page
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        # make a list of users that posted these videos
        all_users = []
        user_prefix = "/user/"
        # get all hyperlinks in the page
        for link_box in soup.find_all('a'):
            link = link_box.get("href")
            # check if the link points to a youtube channel
            if link != None and link.startswith(user_prefix):
                # add the user to the others
                user = link[len(user_prefix):]
                all_users.append(user)
        # get the most occuring user in the list
        user = max(set(all_users), key=all_users.count)

        channel_url = self.base_url + user_prefix + user
        return channel_url



if __name__ == '__main__':
    qh = QuoteHandler()
    search_term = "tom scott"

    # find by channel
    channel_url = qh.get_channel(search_term)
    sort_by_pop_postfix = "/videos?view=0&sort=p&flow=grid"
    page_urls = qh.get_video_links(channel_url + sort_by_pop_postfix)
    urls = ["https://www.youtube.com" + link for link in page_urls]

    # find by video
    video_urls = qh.get_videos(search_term)
    urls = video_urls
    
    comments = qh.get_comments(urls[0])
    print(comments)