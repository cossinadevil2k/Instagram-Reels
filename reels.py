from typing import Optional

import requests


class Reels:

    def __init__(self, user_id: str, page_size: int = 30, max_id: Optional[str] = None):
        self.user_id = user_id
        self.page_size = page_size
        self.max_id = max_id
        self.next_max_id = None

        self.session = requests.Session()
        self.session.headers.update({
            'authority': 'www.instagram.com',
            'content-type': 'application/x-www-form-urlencoded',
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
            'x-ig-app-id': '936619743392459',
            'origin': 'https://www.instagram.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.instagram.com/',
            'accept-language': 'en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7'
        })

        self.session.get("https://www.instagram.com/")

    @property
    def __csrf_token(self):
        return self.session.cookies.get_dict()['csrftoken']

    def __get_reel_tray(self):
        url = f"https://www.instagram.com/api/v1/clips/user/"
        payload = {
            'target_user_id': self.user_id,
            'page_size': self.page_size,
            'max_id': self.max_id,
            'include_feed_video': True
        }

        self.session.headers.update({
            'x-csrftoken': self.__csrf_token
        })

        response = self.session.post(url, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Error while getting reel tray")

    def __parse_reel_tray(self, data):
        self.next_max_id = data['paging_info']['max_id']
        return data['items']

    def get_reels(self):
        data = self.__get_reel_tray()
        return self.__parse_reel_tray(data)

    def get_next_reels(self):
        if self.next_max_id is None:
            return self.get_reels()

        self.max_id = self.next_max_id
        return self.get_reels()

    def get_all_reels(self):
        while True:
            reels = self.get_next_reels()
            if len(reels) == 0:
                break
            yield from reels
        



if __name__ == "__main__":
    reels = Reels("7585796840", page_size=12)
    for reel in reels.get_all_reels():
        print(reel)