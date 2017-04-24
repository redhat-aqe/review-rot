import logging
import datetime
from dateutil.relativedelta import relativedelta
from basereview import BaseService, BaseReview
from github import Github
from github.GithubException import UnknownObjectException

log = logging.getLogger(__name__)


class GithubService(BaseService):
    """
    This class represents Github. The reference can be found here:
    https://developer.github.com/v3/
    """
    def request_reviews(self, user_name, repo_name=None, state_=None,
                        value=None, duration=None, token=None, host=None):
        """
        Creates a github object.
        Requests pull requests for specified username and repo name.
        If repo name is not provided then requests pull requests
        for all repos for specified username/organization.

        Args:
            user_name (str): Github username or organization name
            repo_name (str): Github repository name for specified
                             username or organization
            state_ (str): The filter state for pull requests, e.g, older
                          or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month, hour,
                            minute) for requests to be older or newer than
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
        log.debug('Github instance created: %s', g)
        try:
            # get user object
            uname = g.get_user(user_name)
        except UnknownObjectException:
            log.exception('Invalid username/organizaton: %s', user_name)
            raise Exception('Invalid username/organizaton: %s' % user_name)
        response = []
        # if Repository name is explicitely provided
        if repo_name is not None:
            # get pull requests for specified username and repo name
            res = self.get_reviews(uname=uname, repo_name=repo_name,
                                   state_=state_, value=value,
                                   duration=duration)
            response.append(res)
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
                res = self.get_reviews(uname=uname, repo_name=repo.name,
                                       state_=state_, value=value,
                                       duration=duration)
                response.append(res)
        return response

    def get_reviews(self, uname, repo_name, state_=None,
                    value=None, duration=None):
        """
        Fetches pull requests for specified username and repo name.
        Formats the pull requests details and print it on console.

        Args:
            user_name (str): Github username or organization name
            repo_name (str): Github repository name for specified
                             username or organization
            state_ (str): The filter(state) for pull requests, e.g, older
                        or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year,
                            month, hour, minute) for requests to be
                            older or newer than
        Returns:
            res_ (list): Returns list of pull requests for specified
                         username and repo name
        """
        try:
            # get repository object for given user/organization and repo name
            repo = uname.get_repo(repo_name)
        except UnknownObjectException:
            log.exception('Repository %s not found for user %s',
                          repo_name, uname.login)
            raise Exception('Repository %s not found for user %s'
                            % (repo_name, uname.login))
        log.debug('Looking for pull requests for %s -> %s/%s ',
                  'github', uname.login, repo_name)
        # get list of open pull requests for a given repository
        pull_requests = repo.get_pulls()
        if not pull_requests:
            log.debug('No open pull requests found for %s/%s ',
                      uname.login, repo_name)
        res_ = []
        for pr in pull_requests:
            """
            find the relative time difference between now and
            pull request filed to retrieve relative information
            """
            rel_diff = relativedelta(datetime.datetime.now(),
                                     pr.created_at)
            """
            find the absolute time difference between now and
            pull request filed to retrieve absolute information
            """
            abs_diff = datetime.datetime.now() - pr.created_at
            if (state_ is not None and value is not None and
                    duration is not None):
                """
                check if pull request is older/newer than specified time
                interval
                """
                result = super(GithubService,
                               self).check_request_state(abs_diff, rel_diff,
                                                         state_, value,
                                                         duration)
                # skip the request if it doesn't match the specified criteria
                if not result:
                    log.debug("pull request '%s' is not %s than specified"
                              " time interval", pr.title, state_)
                    continue
            # format the time interval pull request has been filed since
            time = super(GithubService, self).format_duration(rel_diff)
            # fetch and format comments for pull request
            comments = []
            if(pr.comments == 1):
                comments.append('%s' % ', with 1 comment')
            elif(pr.comments > 1):
                comments.append('%s %s %s' % (', with', pr.comments,
                                              'comments'))
            comments = ' '.join(comments)
            # format and print the resultant pull request string
            res = GithubReview(user=pr.user.login,
                               title=pr.title,
                               url=pr.html_url,
                               time=time,
                               comments=comments)
            log.info(res)
            res_.append(res)
        return res_


class GithubReview(BaseReview):
    pass
