import logging
from datetime import datetime
import requests
from reviewrot.basereview import BaseReview, BaseService, LastComment

log = logging.getLogger(__name__)


class GerritService(BaseService):
    """
        This class represents Gerrit. The reference can be found here:
        https://gerrit-review.googlesource.com/Documentation/rest-api.html
    """
    def __init__(self):
        self.session = requests.session()
        self.header = {'Accept': 'application/json'}
        self.url = None
        self.host_exists = None

    def request_reviews(self, host, repo_name, age=None,
                        user_name=None, token=None, show_last_comment=None,
                        ssl_verify=True):
        """
        Creates a Gerrit object.
        Requests pull requests for specified repo name.
        Args:
            host (str): Gerrit Host URL
            repo_name (str): Gerrit repository name
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            user_name(str): This will be None in case of Gerrit
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days
            token (str): This will be None in case of Gerrit
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
            response (list): Returns list of list of pull requests for
                             specified repo name
        """
        reviews = None

        # If the request for reviews is on a different host than the previous
        # request, update the URL and check if the new host exists.
        if self.url != host:
            self.url = host
            self.host_exists = self.get_response(method='HEAD', url=self.url,
                                                 ssl_verify=ssl_verify)

        # checks if specified repo exists
        repo_exists = self.check_repo_exists(repo_name, ssl_verify)

        if self.host_exists and repo_exists:
            request_url = "{}/changes/?q=project:{}+status:open&" \
                          "o=DETAILED_ACCOUNTS".format(self.url, repo_name)
            log.debug('Looking for change requests for %s -> %s',
                      self.url, repo_name)
            review_response = self._call_api(url=request_url,
                                             ssl_verify=ssl_verify)
            reviews = self.format_response(review_response, age, show_last_comment)
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
        except requests.exceptions.HTTPError:
            raise ValueError("No repo found. Please check the repo "
                             "name in config file.")

    def get_comments_count(self, comments_response):
        """
        Returns number of comments

        Args:
            comments_response (dict): dictionary containing
           comments data of pull request

        Returns:
             total_comments(int): Returns count of comments for the
                                  change id
        """
        total_comments = 0
        for response in comments_response:
            if response != '/COMMIT_MSG':
                messages = comments_response.get(response)
                total_comments = total_comments + len(messages)

        return total_comments

    def get_last_comment(self, comments_response):
        """
        Returns information about last comment of given
        pull request

        Args:
           comments_response (dict): dictionary containing
           comments data of gerrit review

        Returns:
           last comment (LastComment): Returns namedtuple LastComment
           with data related to last comment
        """

        comments = []
        for response in comments_response:
            if response != '/COMMIT_MSG':
                messages = comments_response.get(response)
                last_comment = messages[-1]
                # gerrit returns date in format
                # YYYY-MM-DD HH:mm:ss.000000000
                # datetime.strptime is able to handle miliseconds
                # only up to 6 digits
                last_comment_date = datetime.strptime(
                    last_comment['updated'][:-3],
                    "%Y-%m-%d %H:%M:%S.%f")

                author = (last_comment['author'].get('username', None)
                          or last_comment['author']['email'])
                # add last comment from every commented file to list
                comments.append(LastComment(
                    author=author,
                    body=last_comment['message'],
                    created_at=last_comment_date))

        if comments:
            # find last comment in list of comments
            return max(comments, key=lambda c: c.created_at)

    def format_response(self, decoded_responses, age, show_last_comment):
        """
        Formats the pull requests details and print it on console.
        Args:
            decoded_responses (list): Response from REST api call to Gerrit
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days

        Returns:
             res_(list): Returns list of pull requests for specified repo name.
        """
        res_ = []
        for decoded_response in decoded_responses:

            time_format = "%Y-%m-%d %H:%M:%S.%f"
            created_date = datetime.strptime(decoded_response['created'][:-3],
                                             time_format)
            updated_date = datetime.strptime(decoded_response['updated'][:-3],
                                             time_format)
            result = self.check_request_state(created_date, age)

            comments_request_url = "{}/changes/{}/comments".format(
                self.url, str(decoded_response['id']))

            comments_response = self._call_api(comments_request_url)

            last_comment = self.get_last_comment(comments_response)

            if result is False:
                log.debug("Change request '%s' is not %s than specified "
                          "time interval", decoded_response['subject'], age.state)
                continue

            if last_comment and show_last_comment:
                if self.has_new_comments(last_comment.created_at,
                                         show_last_comment):
                    log.debug("Review '%s' had new comments in last %s days",
                              decoded_response['subject'], show_last_comment)
                    continue

            owner = decoded_response['owner']
            change_number = decoded_response['_number']
            res = GerritReview(user=owner.get('username', owner.get('email')),
                               title=decoded_response['subject'],
                               url="{}/{}".format(self.url,
                                                  str(change_number)),
                               time=created_date,
                               updated_time=updated_date,
                               comments=self.get_comments_count(
                                   comments_response),
                               last_comment=last_comment,
                               project_name=decoded_response['project'],
                               # XXX - I don't know how to find gerrit avatars
                               # for now.  Can we figure this out later?
                               image=GerritReview.logo)
            res_.append(res)
        return res_


class GerritReview(BaseReview):
    # XXX - Here just until we figure out how to do gerrit avatars.
    logo = 'http://electric-cloud.com/wp-content/uploads/2014/09/EC-Gerrit.png'
    pass
