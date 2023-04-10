import requests
import json
from types import SimpleNamespace
from .logger import get_logger

logger = get_logger(__name__)
logger.disabled = True


class AtlassianAPI:
    default_headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def __init__(
        self, url, username=None, password=None, timeout=60, session=None, token=None
    ):
        self.url = url.strip("/")
        self.username = username
        self.password = password
        self.timeout = int(timeout)
        if session is None:
            self._session = requests.Session()
        else:
            self._session = session
        if username and password:
            try:
                self._create_basic_session(username, password)
            except Exception as e:
                logger.error(e)
        elif token is not None:
            self._create_token_session(token)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create_basic_session(self, username, password):
        self._session.auth = (username, password)

    def _create_token_session(self, token):
        self._update_header("Authorization", "Bearer {token}".format(token=token))

    def _update_header(self, key, value):
        """
        Update header for exist session
        :param key:
        :param value:
        :return:
        """
        self._session.headers.update({key: value})

    @staticmethod
    def _response_handler(response):
        try:
            return response.json()
        except ValueError:
            logger.debug("Received response with no content.")
            return None
        except Exception as e:
            logger.error(e)
            return None

    def close(self):
        return self._session.close()

    def request(self, method="GET", path="", data=None, json=None, params=None):
        if path:
            url = self.url + path
        else:
            url = self.url
        response = self._session.request(
            method=method,
            url=url,
            data=data,
            json=json,
            params=params,
            timeout=self.timeout,
        )
        response.encoding = "utf-8"
        logger.debug(f"HTTP: {method} -> {response.status_code} {response.reason}")
        return response

    def get(self, path, data=None, params=None):
        response = self.request("GET", path, data=data, params=params)
        if not response.text:
            return None
        try:
            data = response.text
            result = json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
            return result
        except Exception as e:
            logger.error(e)
            return response.text

    def post(self, path, data=None, json=None, params=None):
        response = self.request("POST", path, data=data, json=json, params=params)
        return self._response_handler(response)

    def put(self, path, data=None, json=None, params=None):
        response = self.request("PUT", path, data=data, json=json, params=params)
        return self._response_handler(response)

    def delete(self, path, data=None, json=None, params=None):
        response = self.request("DELETE", path, data=data, json=json, params=params)
        return self._response_handler(response)
