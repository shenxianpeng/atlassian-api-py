import requests
from .logger import get_logger


logger = get_logger(__name__)


class AtlassianAPI:
    default_headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def __init__(self, url, username=None, password=None, timeout=60, session=None):
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create_basic_session(self, username, password):
        self._session.auth = (username, password)

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

    def request(self, method='GET', path='', data=None, json=None, params=None):
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
            timeout=self.timeout)
        response.encoding = 'utf-8'
        logger.debug("HTTP: {0} -> {1} {2}".format(method, response.status_code, response.reason))
        return response

    def get(self, path, data=None, params=None):
        response = self.request("GET", path, data=data, params=params)
        if not response.text:
            return None
        try:
            return response.json()
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
