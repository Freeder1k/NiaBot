from http import HTTPStatus

from aiohttp import ClientResponse


class HTTPNonSuccessException(Exception):
    def __init__(self, resp: ClientResponse):
        self.code: HTTPStatus = HTTPStatus(resp.status)
        self.resp: ClientResponse = resp
        super().__init__(f"Request returned with non-success code {resp.status}.")
