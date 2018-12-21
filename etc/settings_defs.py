from typing import List


class AliceCloudConfig:
    def __init__(self, authorized_handler_url: str, authorized_user_ids: List[str]):
        self.authorized_handler_url = authorized_handler_url
        self.authorized_user_ids = authorized_user_ids
