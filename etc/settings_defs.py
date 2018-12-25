from typing import List


class AliceCloudConfig:
    def __init__(self, authorized_user_ids: List[str], hass_handler_url: str, hass_auth_token: str):
        self.authorized_user_ids = authorized_user_ids
        self.hass_handler_url = hass_handler_url
        self.hass_auth_token = hass_auth_token
