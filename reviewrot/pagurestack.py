import datetime
import hashlib
import logging
import os

try:
    from urllib.parse import urlencode  # python3
except ImportError:
    from urllib import urlencode  # python2

import requests

from reviewrot.basereview import BaseReview, BaseService

log = logging.getLogger(__name__)


class PagureService(BaseService):
    def __init__(self):
        self.session = requests.session()
        self.instance = "https://pagure.io"
        self.header = None

    def request_reviews(self, user_name, repo_name=None, state_=None,
                        value=None, duration=None, host=None, token=None,
                        ssl_verify=True, **kwargs):
        """
        Fetches merge requests by making API calls for specified
        username(namespace) and repo(project) name.
        Formats the merge requests details and print it on console.

        Args:
            user_name (str): Pagure username or organization name
            repo_name (str): Pagure repository name for specified
                             username or organization
            state_ (str): The filter(state) for pull requests, e.g, older
                          or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month,
                            hour, minute) for requests to be older or
                            newer than
            token (str): Pagure token for authentication
                         (Commented for unauthenticated request)
            host (str): Pagure host name (This value is not yet supported.
                        The default behavior is to use public pagure instance)
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
            res_ (list): Returns list of pull requests for specified
                         namespace and/or repo name
        """
        # Authenticated pagure object can be uncommented for future use
        # self.header = {"Authorization": "token " + token}
        if repo_name is not None:
            namespace = user_name
            request_url = "{}/api/0/{}/{}/pull-requests".format(self.instance,
                                                                namespace,
                                                                repo_name)
            log.debug('Looking for pull requests for %s -> %s/%s',
                      'pagure.io', namespace, repo_name)

        else:
            # absence of namespace, directly query pull requests for repo
            repo_name = user_name
            request_url = "{}/api/0/{}/pull-requests".format(self.instance,
                                                             repo_name)
            log.debug('Looking for pull requests for %s -> %s',
                      'pagure.io', repo_name)
        log.debug('Calling API with request_url: %s', request_url)
        response = self._call_api(url=request_url, ssl_verify=ssl_verify)
        res_ = []
        for res in response['requests']:
            # if namespace exists in response
            try:
                repo_reference = os.path.join(res['project']['namespace'],
                                              res['project']['name'])
            except:
                repo_reference = res['project']['name']
            # format pull request url
            url = os.path.join('https://pagure.io/', repo_reference,
                               'pull-request', str(res['id']))
            # fetch the date pull request was filed at
            created_date = datetime.datetime.utcfromtimestamp(
                int(res['date_created'])).strftime('%Y-%m-%d %H:%M:%S')
            # format the date pull request was filed at
            try:
                date = datetime.datetime.strptime(created_date,
                                                  '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                date = datetime.datetime.strptime(created_date,
                                                  '%Y-%m-%d %H:%M:%S')
            """ check if review request is older/newer than specified time
            interval"""
            result = self.check_request_state(date,
                                              state_, value, duration)
            if result is False:
                log.debug("pull request '%s' is not %s than specified"
                          " time interval", res['title'], state_)
                continue
            res = PagureReview(user=res['user']['name'],
                               title=res['title'],
                               url=url,
                               time=date,
                               comments=len(res['comments']),
                               image=self._avatar(res['user']['name']))
            log.debug(res)
            res_.append(res)
        return res_

    @staticmethod
    def _avatar(username):
        """ Return the avatar of a given pagure user.

        Pagure avatars have a predictable URL structure.
        """
        query = urlencode({'s': 64, 'd': 'retro'})
        openid = u'http://%s.id.fedoraproject.org/' % username
        idx = hashlib.sha256(openid.encode('utf-8')).hexdigest()
        return "https://seccdn.libravatar.org/avatar/%s?%s" % (idx, query)


class PagureReview(BaseReview):
    pass