from typing import Optional, List
import requests

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

    def get_all_reels(self, filter_func: Optional[callable] = None):
        """
        Lấy tất cả các reel, có thể được lọc bởi một hàm điều kiện nếu được chỉ định.

        Args:
        - filter_func (Optional[callable]): Hàm lọc dùng để lọc danh sách reel. Mặc định là None.

        Yields:
        - dict: Các reel thỏa mãn điều kiện lọc.
        """
        while True:
            reels = self.get_next_reels()
            if len(reels) == 0:
                break

            if filter_func is not None:
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

    # Sử dụng đối tượng Reels để lấy và in các reel thỏa mãn điều kiện
    reels = Reels("7585796840", page_size=30)
    for reel in reels.get_all_reels(filter_func=lambda reels: filter_like_count(reels, 1000)):
        print(reel)
