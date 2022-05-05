"""githubstack module."""
import logging

from github import Github
from github.GithubException import UnknownObjectException
from reviewrot.basereview import BaseReview, BaseService, LastComment

log = logging.getLogger(__name__)


class GithubService(BaseService):
    """
    This class represents Github.

    The reference can be found here:
    https://developer.github.com/v3/
    """

    def request_reviews(
        self,
        user_name,
        repo_name=None,
        age=None,
        show_last_comment=None,
        token=None,
        host=None,
        **kwargs
    ):
        """
        Creates a github object.

        Requests pull requests for specified username and repo name.
        If repo name is not provided then requests pull requests
        for all repos for specified username/organization.

        Args:
            user_name (str): Github username or organization name
            repo_name (str): Github repository name for specified
                             username or organization
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days
            token (str): Github token for authentication
            host (str): Github host name (This value is not yet supported.
                        Default behavior is to use public github instance.)
        Returns:
            response (list): Returns list of list of pull requests for
                             specified username and reponame or all reponame
                             for given username
        """
        # get authenticated github object
        g = Github(token)
        log.debug("Github instance created: %s", g)
        try:
            # get user object
            uname = g.get_user(user_name)
        except UnknownObjectException:
            log.exception("Invalid username/organizaton: %s", user_name)
            raise Exception("Invalid username/organizaton: %s" % user_name)
        response = []
        # if Repository name is explicitely provided
        if repo_name is not None:
            # get pull requests for specified username and repo name
            res = self.get_reviews(
                uname=uname,
                repo_name=repo_name,
                age=age,
                show_last_comment=show_last_comment,
            )
            # extend incase of a non empty result
            if res:
                response.extend(res)
        else:
            # get all of the respositories for specified user/organization
            repo_list = uname.get_repos()
            if not repo_list:
                log.debug("No repositories found for user name %s", user_name)
            """
            list pull requests for all of the repositories for specified
            user/organization
            """
            for repo in repo_list:
                res = self.get_reviews(
                    uname=uname,
                    repo_name=repo.name,
                    age=age,
                    show_last_comment=show_last_comment,
                )
                # extend incase of a non empty result
                if res:
                    response.extend(res)
        return response

    def get_reviews(self, uname, repo_name, age=None, show_last_comment=None):
        """
        Fetches pull requests for specified username and repo name.

        Formats the pull requests details and print it on console.

        Args:
            user_name (str): Github username or organization name
            repo_name (str): Github repository name for specified
                             username or organization
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days
        Returns:
            res_ (list): Returns list of pull requests for specified
                         username and repo name
        """
        try:
            # get repository object for given user/organization and repo name
            repo = uname.get_repo(repo_name)
        except UnknownObjectException:
            log.exception("Repository %s not found for user %s", repo_name, uname.login)
            raise Exception(
                "Repository %s not found for user %s" % (repo_name, uname.login)
            )
        log.debug(
            "Looking for pull requests for %s -> %s/%s ",
            "github",
            uname.login,
            repo_name,
        )
        # get list of open pull requests for a given repository
        pull_requests = repo.get_pulls()
        if not pull_requests:
            log.debug("No open pull requests found for %s/%s ", uname.login, repo_name)
        res_ = []

        for pr in pull_requests:
            last_comment = self.get_last_comment(pr)

            """ check if review request is older/newer than specified time
            interval"""
            result = self.check_request_state(pr.created_at, age)

            if result is False:
                # skip the current pull request
                log.debug(
                    "review request '%s' is not %s than specified" " time interval",
                    pr.title,
                    age.state,
                )
                continue

            if last_comment and show_last_comment:
                if self.has_new_comments(last_comment.created_at, show_last_comment):
                    log.debug(
                        "Pull request '%s' had " "new comments in last %s days",
                        pr.title,
                        show_last_comment,
                    )
                    continue

            res = GithubReview(
                user=pr.user.login,
                title=pr.title,
                url=pr.html_url,
                time=pr.created_at,
                updated_time=pr.updated_at,
                comments=pr.review_comments + pr.comments,
                image=pr.user.avatar_url,
                last_comment=last_comment,
                project_name=repo.full_name,
                project_url=repo.html_url,
            )
            log.debug(res)
            res_.append(res)
        return res_

    def get_last_comment(self, pr):
        """
        Returns information about last comment of given pull request.

        Args:
            pr (github.PullRequest.PullRequest): Github pull request

        Returns:
            last comment (LastComment): Returns namedtuple LastComment
            with data related to last comment
        """
        review_comments = pr.get_comments()
        issue_comments = pr.get_issue_comments()

        last_review_comment = None
        last_issue_comment = None
        last_comment = None

        if review_comments.totalCount > 0:
            last_review_comment = review_comments.reversed[0]

        if issue_comments.totalCount > 0:
            last_issue_comment = issue_comments.reversed[0]

        # check which is newer if pr has both types of comments
        if last_issue_comment and last_review_comment:
            if last_issue_comment.created_at > last_review_comment.created_at:
                last_comment = last_issue_comment
            else:
                last_comment = last_review_comment

        # if pr has only one type of comment
        else:
            last_comment = last_issue_comment or last_review_comment

        if last_comment:
            return LastComment(
                author=last_comment.user.login,
                body=last_comment.body,
                created_at=last_comment.created_at,
            )


class GithubReview(BaseReview):
    """TODO: docstring goes here."""

    pass
