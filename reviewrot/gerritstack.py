import logging

from datetime import datetime

import requests

from reviewrot.basereview import BaseReview, BaseService

log = logging.getLogger(__name__)


class GerritService(BaseService):
    """
        This class represents Gerrit. The reference can be found here:
        https://gerrit-review.googlesource.com/Documentation/rest-api.html
    """
    def __init__(self):
        self.session = requests.session()
        self.header = None

    def request_reviews(self, host, repo_name, state_=None,
                        user_name=None, token=None, value=None,
                        duration=None, ssl_verify=True):
        self.url = host
        reviews = None

        if self.check_host_url(ssl_verify) and self.check_repo_exist(repo_name, ssl_verify):
            request_url = "{}/changes/?q=project:{}+status:open&o=DETAILED_ACCOUNTS".format(self.url, repo_name)
            log.debug('Looking for change requests for %s -> %s', self.url, repo_name)
            review_response = self._call_api(url=request_url, ssl_verify=ssl_verify)
            reviews = self.format_response(review_response, state_, value, duration)
        return reviews

    def check_repo_exist(self, repo_name, ssl_verify):
        request_url = "{}/projects/{}".format(self.url, repo_name)
        log.debug('Checking if repo %s exists', repo_name)
        try:
            self._call_api(url=request_url, ssl_verify=ssl_verify)
            return True
        except ValueError:
            raise ValueError("No repo found. Please check the repo name in ~/.reviewrot.yaml file.")

    def check_host_url(self, ssl_verify):
        log.debug('Checking if host URL %s is correct', self.url)
        try:
            response = self.get_response(method='GET', url=self.url, ssl_verify=ssl_verify)
            if response.status_code == 200:
                return True
            else:
                raise ValueError('Host URL is incorrectly configured in ~/.reviewrot.yaml file.')
        except:
            raise ValueError('Host URL is incorrectly configured in ~/.reviewrot.yaml file.')

    def get_comments_count(self, change_id):
        request_url = "{}/changes/{}/comments".format(self.url, str(change_id))
        decoded_response = self._call_api(request_url, ignore_error=True)
        total_comments = 0
        for response in decoded_response:
            if response is not '/COMMIT_MSG':
                total_comments = total_comments + len(decoded_response.get(response))

        return total_comments

    def format_response(self, decoded_responses, state_, value, duration):
        res_ = []
        for decoded_response in decoded_responses:
            created_date = datetime.strptime(decoded_response['created'][:-3], "%Y-%m-%d %H:%M:%S.%f")
            result = self.check_request_state(created_date, state_, value, duration)
            if result is False:
                log.debug("Change request '%s' is not %s than specified time interval", decoded_response['subject'], state_)
                continue
            owner = decoded_response['owner']
            res = GerritReview(user=owner.get('username', owner.get('email')),
                               title=decoded_response['subject'],
                               url="{}/{}".format(self.url,
                                                  str(decoded_response['_number'])),
                               time=created_date,
                               comments=self.get_comments_count(decoded_response['id']))
            res_.append(res)
        return res_


class GerritReview(BaseReview):
    pass
