"""gerritstack module."""
from datetime import datetime
import logging

import requests
from reviewrot.basereview import BaseReview, BaseService, gravatar, LastComment

log = logging.getLogger(__name__)


class GerritService(BaseService):
    """
    This class represents Gerrit.

    The reference can be found here:
    https://gerrit-review.googlesource.com/Documentation/rest-api.html
    """

    def __init__(self):
        """TODO: docstring goes here."""
        self.session = requests.session()
        self.header = {"Accept": "application/json"}
        self.url = None
        self.host_exists = None
        self.ssl_verify = None

    def request_reviews(
        self,
        host,
        repo_name,
        age=None,
        user_name=None,
        token=None,
        show_last_comment=None,
        ssl_verify=True,
        reviewers_config=None,
    ):
        """
        Creates a Gerrit object.

        Requests pull requests for specified repo name.

        If reviewers_config argument is used, changes without users
        invited to review are skipped. Users can be excluded from the
        reviewers list, for example, to avoid having bots counted as
        reviewers.

        reviewers_config = {
            'ensure': bool,
            'excluded': List[str],  # List of user ID values
            'id_key': str,  # Reviewer ID key, AccountInfo FieldName
        }

        Reviewer ID keys are the same as AccountInfo FieldNames:
        https://gerrit-review.googlesource.com/Documentation/rest-api-accounts.html#account-info

        Users invited to review are included in the change response if
        DETAILED_LABELS option is used in the request. Otherwise,
        reviewers endpoint can be used:
        https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#list-reviewers

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
            reviewers_config (Optional[Dict]): Controls excluding changes
                based on invited reviewers.
        Returns:
            response (list): Returns list of list of pull requests for
                             specified repo name
        """
        self.ssl_verify = ssl_verify

        # If the request for reviews is on a different host than the previous
        # request, update the URL and check if the new host exists.
        if self.url != host:
            self.url = host
            self.host_exists = self.get_response(
                method="HEAD", url=self.url, ssl_verify=ssl_verify
            )

        # checks if specified repo exists
        repo_exists = self.check_repo_exists(repo_name, ssl_verify)

        if not self.host_exists or not repo_exists:
            return

        request_url = (
            "{}/changes/?q=project:{}+status:open"
            "&o=DETAILED_ACCOUNTS"
            "&o=DETAILED_LABELS"
        ).format(self.url, repo_name)
        log.debug("Looking for change requests for %s -> %s", self.url, repo_name)
        review_response = self._call_api(url=request_url, ssl_verify=ssl_verify)

        if not review_response:
            return []

        # Assume that reviewers should be enforced if there is some
        # config and ensure is not explicitly False.
        if reviewers_config and reviewers_config.get("ensure", True):
            review_response = self._filter_invited(review_response, **reviewers_config)

        return self.format_response(review_response, age, show_last_comment)

    def _filter_invited(self, changes, **kwargs):
        """Filter out changes without users invited to review.

        Arguments:
            changes (List[dict]): List of Gerrit changes.

        Keyword arguments:
            excluded (List[str]): List of reviewer ID values to exclude
                from reviewers list
            id_key (str): Reviewer ID key for values in excluded.

        Returns:
           (List[Dict]) List of changes with users invited to review.
        """
        excluded = kwargs.pop("excluded", None)
        id_key = kwargs.pop("id_key", None)

        def has_reviewers(change):
            reviewers = self._get_change_reviewers(
                change, excluded=excluded, id_key=id_key
            )

            if not reviewers:
                log.debug(
                    'No reviewers invited to "%s" in %s',
                    change["subject"],
                    change["project"],
                )

            return bool(reviewers)

        return [c for c in changes if has_reviewers(c)]

    def _get_change_reviewers(self, change, excluded=None, id_key=None):
        """Get list of users invited to review the change.

        Arguments:
            change (Dict): Gerrit change
            excluded (Optional[List[str]]): List of reviewer ID values
            id_key (Optional[str]): Reviewer ID key for excluded values

        Returns:
            (List(Dict)): List of reviewers
        """
        reviewers = change.get("reviewers", {}).get("REVIEWER", [])

        if reviewers and excluded:
            id_key = id_key or "username"
            reviewers = [r for r in reviewers if r.get(id_key) not in excluded]

        return reviewers

    def check_repo_exists(self, repo_name, ssl_verify):
        """
        Check if repo exist in gerrit.

        Args:
            repo_name (str): Gerrit repository name
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
             true/false(bool): Returns true if repo exist else false
        """
        request_url = "{}/projects/{}".format(self.url, repo_name)
        log.debug("Checking if repo %s exists", repo_name)
        try:
            self._call_api(url=request_url, ssl_verify=ssl_verify)
            return True
        except requests.exceptions.HTTPError:
            raise ValueError(
                "No repo found. Please check the repo " "name in config file."
            )

    def get_comments_count(self, comments_response):
        """
        Returns number of comments.

        Args:
            comments_response (dict): dictionary containing
           comments data of pull request

        Returns:
             total_comments(int): Returns count of comments for the
                                  change id
        """
        total_comments = 0
        for response in comments_response:
            if response != "/COMMIT_MSG":
                messages = comments_response.get(response)
                total_comments = total_comments + len(messages)

        return total_comments

    def get_last_comment(self, comments_response):
        """
        Returns information about last comment of given pull request.

        Args:
           comments_response (dict): dictionary containing
           comments data of gerrit review

        Returns:
           last comment (LastComment): Returns namedtuple LastComment
           with data related to last comment
        """
        comments = []
        for response in comments_response:
            if response != "/COMMIT_MSG":
                messages = comments_response.get(response)
                last_comment = messages[-1]
                # gerrit returns date in format
                # YYYY-MM-DD HH:mm:ss.000000000
                # datetime.strptime is able to handle miliseconds
                # only up to 6 digits
                last_comment_date = datetime.strptime(
                    last_comment["updated"][:-3], "%Y-%m-%d %H:%M:%S.%f"
                )

                author = (
                    last_comment["author"].get("username", None)
                    or last_comment["author"]["email"]
                )
                # add last comment from every commented file to list
                comments.append(
                    LastComment(
                        author=author,
                        body=last_comment["message"],
                        created_at=last_comment_date,
                    )
                )

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
            created_date = datetime.strptime(
                decoded_response["created"][:-3], time_format
            )
            updated_date = datetime.strptime(
                decoded_response["updated"][:-3], time_format
            )
            result = self.check_request_state(created_date, age)

            comments_request_url = "{}/changes/{}/comments".format(
                self.url, str(decoded_response["id"])
            )

            comments_response = self._call_api(comments_request_url)

            last_comment = self.get_last_comment(comments_response)

            if result is False:
                log.debug(
                    "Change request '%s' is not %s than specified " "time interval",
                    decoded_response["subject"],
                    age.state,
                )
                continue

            if last_comment and show_last_comment:
                if self.has_new_comments(last_comment.created_at, show_last_comment):
                    log.debug(
                        "Review '%s' had new comments in last %s days",
                        decoded_response["subject"],
                        show_last_comment,
                    )
                    continue

            owner = decoded_response["owner"]
            change_number = decoded_response["_number"]

            # Use the gerrit logo by default
            image = GerritReview.logo
            # Otherwise, if we have an owner email, use their gravatar.
            if owner.get("email"):
                image = gravatar(owner["email"])

            res = GerritReview(
                user=owner.get("username", owner.get("email")),
                title=decoded_response["subject"],
                url="{}/{}".format(self.url, str(change_number)),
                time=created_date,
                updated_time=updated_date,
                comments=self.get_comments_count(comments_response),
                last_comment=last_comment,
                project_name=decoded_response["project"],
                image=image,
            )
            res_.append(res)
        return res_


class GerritReview(BaseReview):
    """TODO: docstring goes here."""

    logo = "http://electric-cloud.com/wp-content/uploads/2014/09/EC-Gerrit.png"
    pass
