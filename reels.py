from typing import Optional, List, Dict
import requests
import json

class Reels:

    def __init__(self, user_id: str, page_size: int = 30, max_id: Optional[str] = None):
        """
        Khởi tạo đối tượng Reels với các thông số đầu vào.

        Args:
        - user_id (str): ID của người dùng Instagram.
        - page_size (int): Số lượng reel trên mỗi trang. Mặc định là 30.
        - max_id (Optional[str]): ID tối đa của reel, được sử dụng để phân trang. Mặc định là None.
        """
        
        self.user_id = user_id
        self.page_size = page_size
        self.max_id = max_id

        self._next_max_id: Optional[str] = None
        self._more_available: bool = True

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

        # Gửi GET request đến trang chủ Instagram để lấy CSRF token
        self.session.get("https://www.instagram.com/")

    @property
    def __csrf_token(self):
        """
        Lấy giá trị CSRF token từ cookies của session.

        Returns:
        - str: CSRF token.
        """
        return self.session.cookies.get_dict()['csrftoken']

    def __get_reel_tray(self):
        """
        Gửi POST request để lấy thông tin về reel tray từ Instagram API.

        Returns:
        - dict: Dữ liệu JSON chứa thông tin về reel tray.
        """
        url = f"https://www.instagram.com/api/v1/clips/user/"
        payload = {
            'target_user_id': self.user_id,
            'page_size': self.page_size,
            'max_id': self.max_id,
            'include_feed_video': True
        }

        # Cập nhật header với CSRF token
        self.session.headers.update({
            'x-csrftoken': self.__csrf_token
        })

        # Gửi POST request và trả về dữ liệu JSON nếu thành công
        response = self.session.post(url, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Error while getting reel tray")

    def __parse_reel_tray(self, data: dict) -> list:
        """
        Phân tích dữ liệu từ reel tray để trích xuất danh sách reel.

        Args:
        - data (dict): Dữ liệu JSON từ reel tray.

        Returns:
        - list: Danh sách các reel.
        """
        if data['status'] != 'ok':
            raise Exception("Error while parsing reel tray")

        if data['paging_info']['more_available'] is False:
            self._more_available = False
        else:
            self._next_max_id = data['paging_info']['max_id']

        return data['items']

    def get_reels(self):
        """
        Lấy danh sách reel từ reel tray.

        Returns:
        - list: Danh sách các reel.
        """
        data = self.__get_reel_tray()
        return self.__parse_reel_tray(data)

    def get_next_reels(self):
        """
        Lấy danh sách reel tiếp theo nếu có.

        Returns:
        - list: Danh sách các reel tiếp theo hoặc danh sách trống nếu không còn.
        """
        if self._more_available is False:
            return []

        self.max_id = self._next_max_id
        return self.get_reels()

    def get_all_reels(self, filter_funcs: Optional[List[callable]] = None):

        """
        Lấy tất cả các reel, có thể được lọc bởi một hàm điều kiện nếu được chỉ định.

        Args:
        - filter_funcs (Optional[List[callable]]): Danh sách các hàm điều kiện.

        Returns:
        - Generator: Generator chứa các reel.
        """
        while True:
            reels = self.get_next_reels()
            if len(reels) == 0:
                break

            if filter_funcs is not None:
                for filter_func in filter_funcs:
                    reels = filter_func(reels)
                

            yield from reels

if __name__ == "__main__":

    def filter_like_count(reels: List[dict], like_count: int):
        """
        Hàm lọc reel theo số lượt thích.

        Args:
        - reels (List[dict]): Danh sách các reel.
        - like_count (int): Ngưỡng số lượt thích.

        Returns:
        - List[dict]: Danh sách các reel thỏa mãn điều kiện.
        """
        _reels = []
        for reel in reels:
            if reel['media']['like_count'] >= like_count:
                _reels.append(reel)
        return _reels



    #filter text , like_count, play_count, code
    def filter_data(reels: List[dict]):
        """
        Hàm lọc reel theo số lượt thích, số lượt xem và caption, code.
        """
        _reels = []
        for reel in reels:
            try:
                caption = reel['media'].get('caption')
                if caption is not None:
                    caption = caption['text']
                like_count = reel['media'].get('like_count', 0)
                play_count = reel['media'].get('play_count', 0)
                code = reel['media'].get('code', '')
                _reels.append({
                    'caption': caption,
                    'like_count': like_count,
                    'play_count': play_count,
                    'code': code
                })
            except:
                open('error.json', 'a').write(json.dumps(reel, indent=4))

        return _reels
    
    

    reels = Reels("31051275986", page_size=30)
    for reel in reels.get_all_reels(filter_funcs=[
        lambda reels: filter_like_count(reels, 1000),
        lambda reels: filter_data(reels)
]):
        pass
