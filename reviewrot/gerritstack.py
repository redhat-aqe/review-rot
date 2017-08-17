import logging
import requests

from datetime import datetime

from reviewrot.basereview import BaseReview, BaseService

log = logging.getLogger(__name__)


class GerritService(BaseService):
    """
        This class represents Gerrit. The reference can be found here:
        https://gerrit-review.googlesource.com/Documentation/rest-api.html
    """
    def __init__(self):
        self.session = requests.session()
        self.header = {'Accept': 'application/json'}

    def request_reviews(self, host, repo_name, state_=None,
                        user_name=None, token=None, value=None,
                        duration=None, ssl_verify=True):
        """
        Creates a Gerrit object.
        Requests pull requests for specified repo name.
        Args:
            host (str): Gerrit Host URL
            repo_name (str): Gerrit repository name
            user_name(str): This will be None in case of Gerrit
            state_ (str): The filter state for pull requests, e.g, older
                          or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month, hour,
                            minute) for requests to be older or newer than
            token (str): This will be None in case of Gerrit
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
            response (list): Returns list of list of pull requests for
                             specified repo name
        """
        self.url = host
        reviews = None

        if self.check_host_url(ssl_verify) and \
                self.check_repo_exists(repo_name, ssl_verify):
            request_url = "{}/changes/?q=project:{}+status:open&" \
                          "o=DETAILED_ACCOUNTS".format(self.url, repo_name)
            log.debug('Looking for change requests for %s -> %s',
                      self.url, repo_name)
            review_response = self._call_api(url=request_url,
                                             ssl_verify=ssl_verify)
            reviews = self.format_response(review_response, state_, value,
                                           duration)
        return reviews

    def check_repo_exists(self, repo_name, ssl_verify):
        """
        Check if repo exist in gerrit
        Args:
            repo_name (str): Gerrit repository name
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
             true/false(bool): Returns true if repo exist else false
        """
        request_url = "{}/projects/{}".format(self.url, repo_name)
        log.debug('Checking if repo %s exists', repo_name)
        try:
            self._call_api(url=request_url, ssl_verify=ssl_verify)
            return True
        except ValueError:
            raise ValueError("No repo found. Please check the repo "
                             "name in config file.")

    def check_host_url(self, ssl_verify):
        """
        Check if host url is valid
        Args:
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
             true/false(bool): Returns true if url is valid else false
        """
        log.debug('Checking if host URL %s is correct', self.url)
        try:
            response = self.get_response(method='GET', url=self.url,
                                         ssl_verify=ssl_verify)
            if response.status_code == 200:
                return True
            else:
                raise ValueError('Host URL is incorrectly configured'
                                 ' in config file.')
        except (ValueError, requests.ConnectionError):
            raise ValueError('Host URL is incorrectly configured'
                             ' in config file.')
        except:
            raise

    def get_comments_count(self, change_id):
        """
        Check if host url is valid
        Args:
            change_id (int): pull/merge request id
        Returns:
             total_comments(int): Returns count of comments for the
                                  change id
        """
        request_url = "{}/changes/{}/comments".format(self.url, str(change_id))
        decoded_response = self._call_api(request_url, ignore_err=True)
        total_comments = 0
        for response in decoded_response:
            if response is not '/COMMIT_MSG':
                messages = decoded_response.get(response)
                total_comments = total_comments + len(messages)

        return total_comments

    def format_response(self, decoded_responses, state_, value, duration):
        """
        Formats the pull requests details and print it on console.
        Args:
            decoded_responses (list): Response from REST api call to Gerrit
            state_ (str): The filter state for pull requests, e.g, older
                          or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month, hour,
                            minute) for requests to be older or newer than

        Returns:
             res_(list): Returns list of pull requests for specified repo name.
        """
        res_ = []
        for decoded_response in decoded_responses:
            created_date = datetime.strptime(decoded_response['created'][:-3],
                                             "%Y-%m-%d %H:%M:%S.%f")
            result = self.check_request_state(created_date, state_, value,
                                              duration)
            if result is False:
                log.debug("Change request '%s' is not %s than specified "
                          "time interval", decoded_response['subject'], state_)
                continue
            owner = decoded_response['owner']
            change_number = decoded_response['_number']
            res = GerritReview(user=owner.get('username', owner.get('email')),
                               title=decoded_response['subject'],
                               url="{}/{}".format(self.url,
                                                  str(change_number)),
                               time=created_date,
                               comments=self.get_comments_count(
                                   decoded_response['id']),
                               # XXX - I don't know how to find gerrit avatars
                               # for now.  Can we figure this out later?
                               image=GerritReview.logo)
            res_.append(res)
        return res_


class GerritReview(BaseReview):
    # XXX - Here just until we figure out how to do gerrit avatars.
    logo = 'http://electric-cloud.com/wp-content/uploads/2014/09/EC-Gerrit.png'
    pass
