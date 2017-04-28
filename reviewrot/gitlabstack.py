import os
import logging
import gitlab
import datetime
from reviewrot.basereview import BaseService, BaseReview
from gitlab.exceptions import GitlabGetError

log = logging.getLogger(__name__)


class GitlabService(BaseService):
    """
    This class represents Gitlab. The reference can be found here:
     https://docs.gitlab.com/ee/api/
    """
    def request_reviews(self, user_name, repo_name=None, state_=None,
                        value=None, duration=None, token=None, host=None):
        """
        Creates a gitlab object.
        Requests merge requests for specified username and repo name.
        If repo name is not provided then requests merge requests
        for all repos for specified username/organization.

        Args:
            user_name (str): Gitlab namespace
            repo_name (str): Gitlab project name for specified
                          namespace
            state_ (str): The state for pull requests, e.g, older
                        or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month,
                            hour, minute) for requests to be older or
                            newer than
            token (str): Gitlab token for authentication
            host (str): Gitlab host name for authentication

        Returns:
            response (list): Returns list of list of pull requests for
                             specified user(group) name and projectname or all
                             projectname for given groupname
        """
        gl = gitlab.Gitlab(host, token)
        gl.auth()
        log.debug('Gitlab instance created: %s', gl)
        response = []
        # if Repository name is explicitely provided
        if repo_name is not None:
            try:
                # get project object for given repo_name(project name)
                project = gl.projects.get(os.path.join(user_name, repo_name))
            except GitlabGetError:
                log.exception('Project %s not found for user %s',
                              repo_name, user_name)
                raise Exception('Project %s not found for user %s'
                                % (repo_name, user_name))
            # get merge requests for specified username and project name
            res = self.get_reviews(uname=user_name, project=project,
                                   state_=state_, value=value,
                                   duration=duration)
            # append incase of a non empty result
            if res:
                response.append(res)

        else:
            # get user object
            groups = gl.groups.search(user_name)
            if not groups:
                log.debug('Invalid user/group name: %s', user_name)
                raise Exception('Invalid user/group name: %s' % user_name)

            # get merge requests for all projects for specified group
            for group in groups:
                projects = gl.group_projects.list(group_id=group.id)
                if not projects:
                    log.debug("No projects found for user/group name %s",
                              user_name)
                for project in projects:
                    res = self.get_reviews(uname=user_name, project=project,
                                           state_=state_, value=value,
                                           duration=duration)
                # append incase of a non empty result
                if res:
                    response.append(res)
        return response

    def get_reviews(self, uname, project, state_=None,
                    value=None, duration=None):
        """
        Fetches merge requests for specified username(groupname)
        and repo(project) name.
        Formats the merge requests details and print it on console.

        Args:
            user_name (str): Gitlab namespace
            repo_name (str): Gitlab project name for specified
                             namespace
            state_ (str): The state for pull requests, e.g, older
                        or newer
            value (str): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month,
                            hour, minute) for requests to be older or
                            newer than.

        Returns:
            res_ (list): Returns list of pull requests for specified
                         user(group) name and project name
        """
        log.debug('Looking for merge requests for %s -> %s',
                  uname, project.name)

        # get list of open merge requests for a given repository(project)
        merge_requests = project.mergerequests.list(project_id=project.id,
                                                    state='opened')
        if not merge_requests:
            log.debug('No open merge requests found for %s/%s ',
                      uname, project.name)
        res_ = []
        for mr in merge_requests:
            try:
                mr_date = datetime.datetime.strptime(
                    mr.created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                mr_date = datetime.datetime.strptime(
                    mr.created_at, '%Y-%m-%dT%H:%M:%SZ')
            """ check if review request is older/newer than specified time
            interval"""
            result = self.check_request_state(mr_date,
                                              state_, value, duration)
            if result is False:
                log.debug("merge request '%s' is not %s than specified"
                          " time interval", mr.title, state_)
                continue
            # format the time interval pull request has been filed since
            time = self.format_duration(created_at=mr_date)
            res = GitlabReview(user=mr.author.username,
                               title=mr.title,
                               url=mr.web_url,
                               time=time,
                               comments=mr.user_notes_count)
            log.info(res)
            res_.append(res)
        return res_


class GitlabReview(BaseReview):
    pass
