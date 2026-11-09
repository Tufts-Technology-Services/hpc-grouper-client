from urllib.parse import urljoin
import os
import logging
import requests


logger = logging.getLogger('grouper_client')

VERIFY_CERTS = os.getenv('GROUPER_VERIFY_CERTS', 'True').lower() in ['true', '1', 'yes']
CONNECT_TIMEOUT = int(os.getenv('GROUPER_CONNECT_TIMEOUT', '10'))
READ_TIMEOUT = int(os.getenv('GROUPER_READ_TIMEOUT', '60'))
TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)
RETRIES = int(os.getenv('GROUPER_RETRIES', '3'))


class AbstractClient:
    url = None
    refresh_token = None
    token = None

    def renew_token(self, refresh_token):
        raise NotImplementedError

    def _get_headers(self, additional_headers=None, skip_auth=False):
        headers = {
            'Accept': 'application/json'
        }
        if not skip_auth:
            headers['Authorization'] = f'Bearer {self.token}'
        if additional_headers is not None:
            headers.update(additional_headers)
        return headers

    def _send(self, http_method, endpoint, headers=None, skip_auth=False, retries=RETRIES, **request_kwargs):
        """
        Send a request and return requests' Response, retrying as Grouper needs.

        A response refused as unauthorised (401 or 403) means the token has expired: it is renewed
        and the request sent again. A request that times out is sent again as it was. Either way
        there are at most `retries` more attempts, and the answer is the last attempt's. Any other
        HTTP error is raised at once, as requests' HTTPError.

        The headers are built afresh for every attempt, so a retry carries the renewed token.
        """
        url = urljoin(self.url, endpoint)
        while True:
            if not skip_auth and self.token is None and self.refresh_token is not None:
                self.renew_token(self.refresh_token)
            attempt_headers = self._get_headers(dict(headers or {}), skip_auth=skip_auth)
            logger.debug("%s %s: %s", http_method, url, request_kwargs)
            try:
                r = requests.request(http_method, url, headers=attempt_headers, verify=VERIFY_CERTS,
                                     timeout=TIMEOUT, **request_kwargs)
                logger.debug("Response status: %s", r.status_code)
                logger.debug("Response body: %s", r.text)
                r.raise_for_status()
                return r
            except requests.exceptions.HTTPError as e:
                expired = e.response is not None and e.response.status_code in (401, 403)
                if not (expired and not skip_auth and self.refresh_token is not None and retries > 0):
                    raise
                logger.info("%s %s was refused (%s); renewing the token and retrying, %s retries left",
                            http_method, url, e.response.status_code, retries)
                self.renew_token(self.refresh_token)
            except requests.exceptions.Timeout as e:
                if retries == 0:
                    raise
                logger.error("Timeout: %s", e)
                logger.info("Retrying %s request to %s, retries left: %s", http_method, url, retries)
            retries -= 1

    def _send_get_request(self, endpoint, params=None, retries=RETRIES):
        return self._send('GET', endpoint, retries=retries, params=params if params is not None else {}).json()

    def _send_post_request(self, endpoint, payload, headers=None, skip_auth=False):
        return self._send_body('POST', endpoint, payload, headers, skip_auth)

    def _send_put_request(self, endpoint, payload, headers=None, skip_auth=False):
        return self._send_body('PATCH', endpoint, payload, headers, skip_auth)

    def _send_patch_request(self, endpoint, payload, headers=None, skip_auth=False):
        return self._send_body('PATCH', endpoint, payload, headers, skip_auth)

    def _send_body(self, http_method, endpoint, payload, headers=None, skip_auth=False, retries=RETRIES):
        # list of valid http methods
        if http_method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            raise ValueError(f'Invalid http method: {http_method}')
        headers = dict(headers or {})
        headers.update({'Content-Type': 'application/json'})
        return self._send(http_method, endpoint, headers=headers, skip_auth=skip_auth, retries=retries,
                          json=payload).json()

    def _send_delete_request(self, endpoint, body=None, retries=RETRIES):
        if body is not None:
            return self._send_body('DELETE', endpoint, body, retries=retries)
        r = self._send('DELETE', endpoint, retries=retries)
        return {'status': r.status_code}
