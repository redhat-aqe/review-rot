from datetime import datetime
import hashlib
import logging
from six.moves import urllib


import requests

from reviewrot.basereview import BaseReview, BaseService, LastComment

log = logging.getLogger(__name__)


class PagureService(BaseService):
    def __init__(self):
        self.session = requests.session()
        self.instance = "https://pagure.io"
        self.header = None

    def request_reviews(self, user_name, repo_name=None, age=None,
                        show_last_comment=None, host=None, token=None,
                        ssl_verify=True, **kwargs):
        """
        Fetches merge requests by making API calls for specified
        username(namespace) and repo(project) name.
        Formats the merge requests details and print it on console.

        Args:
            user_name (str): Pagure username or organization name
            repo_name (str): Pagure repository name for specified
                             username or organization
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days
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
        try:
            response = self._call_api(url=request_url, ssl_verify=ssl_verify)
        except requests.exceptions.HTTPError:
            raise ValueError("No repo found. Please check the repo "
                             "name in config file.")
        res_ = []
        for res in response['requests']:
            # if namespace exists in response
            if res['project']['namespace']:
                repo_reference = '{}/{}'.format(
                    res['project']['namespace'], res['project']['name']
                )
            else:
                repo_reference = res['project']['name']

            last_comment = self.get_last_comment(res)

            # format pull request url
            url = 'https://pagure.io/{}/pull-request/{}'.format(
                repo_reference, res['id']
            )
            # fetch the date pull request was filed at
            created_date = datetime.utcfromtimestamp(
                int(res['date_created'])).strftime('%Y-%m-%d %H:%M:%S')
            updated_date = datetime.utcfromtimestamp(
                int(res['last_updated'])).strftime('%Y-%m-%d %H:%M:%S')
            # format the date pull request was filed at
            try:
                date = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S.%f')
                updated_time = datetime.strptime(updated_date,
                                                 '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                date = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S')
                updated_time = datetime.strptime(updated_date, '%Y-%m-%d %H:%M:%S')

            """ check if review request is older/newer than specified time
            interval"""
            result = self.check_request_state(date, age)
            if result is False:
                log.debug("pull request '%s' is not %s than specified"
                          " time interval", res['title'], age.state)
                continue

            if last_comment and show_last_comment:
                if self.has_new_comments(last_comment.created_at,
                                         show_last_comment):
                    log.debug("pull request '%s' has new "
                              "comments in last %s days",
                              res['title'], show_last_comment)
                    continue

            project_url = 'https://pagure.io/{}'.format(repo_reference)
            res = PagureReview(user=res['user']['name'],
                               title=res['title'],
                               url=url,
                               time=date,
                               updated_time=updated_time,
                               comments=len(res['comments']),
                               image=self._avatar(res['user']['name'], ssl_verify=ssl_verify),
                               last_comment=last_comment,
                               project_name=repo_reference,
                               project_url=project_url)
            log.debug(res)
            res_.append(res)
        return res_

    def get_last_comment(self, res):
        """
        Returns information about last comment of given
        pull request

        Args:
           res (dict): dictionary containing
           comments data of pull request

        Returns:
           last comment (LastComment): Returns namedtuple LastComment
           with data related to last comment
        """

        comments = res['comments']

        if comments:
            last_comment_date = datetime.utcfromtimestamp(
                int(comments[-1]['date_created']))
            return LastComment(
                author=str(comments[-1]['user']['name']),
                body=str(comments[-1]['comment']),
                created_at=last_comment_date)

    def _avatar(self, username, ssl_verify=True):
        """
        Return the avatar URL of a given pagure user.

        This method will first try to fetch the avatar URL from pagure API.
        However, this information has only recently been exposed. As a fallback,
        this method will construct the avatar URL based on the username. This
        provides an avatar, but it's not the user's avatar since that one is
        based on user's email address which is not publicly exposed.

        Args:
            username (str): user to fetch avatar URL for
            ssl_verify (bool): whether or not to verify the identity
                               cert of the pagure instance

        Returns:
           avatar_url (str): The avatar URL for the given user
        """
        request_url = "{}/api/0/user/{}".format(self.instance, username)
        log.debug("Looking for avatar URL for user %s", username)
        try:
            response = self._call_api(url=request_url, ssl_verify=ssl_verify)
        except requests.exceptions.HTTPError:
            raise ValueError("User {} not found!".format(username))

        avatar_query = {'s': 64, 'd': 'retro'}
        avatar_url = response.get('user', {}).get('avatar_url')
        if avatar_url:
            # Make sure we're getting the resolution we expect.
            url_parts = urllib.parse.urlparse(avatar_url)
            url_query = urllib.parse.parse_qs(url_parts.query)
            url_query.update(avatar_query)
            url_query = urllib.parse.urlencode(url_query, doseq=True)
            avatar_url = urllib.parse.urlunparse(url_parts[:4] + (url_query,) + url_parts[5:])
        else:
            log.debug("Pagure instance does not expose user's avatar URL. "
                      "Fallback to construct based on username")
            query = urllib.parse.urlencode(avatar_query)
            openid = u'http://%s.id.fedoraproject.org/' % username
            idx = hashlib.sha256(openid.encode('utf-8')).hexdigest()
            avatar_url = "https://seccdn.libravatar.org/avatar/%s?%s" % (idx, query)

        return avatar_url


class PagureReview(BaseReview):
    pass
