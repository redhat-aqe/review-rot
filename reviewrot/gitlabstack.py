import os
import logging
import gitlab
import datetime
from dateutil.relativedelta import relativedelta
from base import BaseService, BaseReviewRot
from gitlab.exceptions import GitlabGetError

log = logging.getLogger(__name__)


class GitlabService(BaseService):
    """
    This class represents Gitlab. The reference can be found here:
     https://docs.gitlab.com/ee/api/
    """
    def request_reviews(self, user_name, repo_name=None, fltr=None,
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
            fltr (str): The filter(state) for pull requests, e.g, older
                        or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month,
                            hour, minute) for requests to be older or
                            newer than
            token (str): Gitlab token for authentication
            host (str): Gitlab host name for authentication
        """
        gl = gitlab.Gitlab(host, token)
        gl.auth()
        log.debug('Gitlab instance created: %s', gl)

        # if Repository name is explicitely provided
        if repo_name is not None:
            try:
                # get project object for given repo_name(project name)
                project = gl.projects.get(os.path.join(user_name, repo_name))
            except GitlabGetError as e:
                log.debug('Project %s not found for user %s',
                          repo_name, user_name)
                log.debug(e)
                raise Exception('Project %s not found for user %s'
                                % (repo_name, user_name))
            # get merge requests for specified username and project name
            self.get_reviews(uname=user_name, project=project, fltr=fltr,
                             value=value, duration=duration)

        else:
            # get user object
            groups = gl.groups.search(user_name)
            if len(groups) == 0:
                log.debug('Invalid user/group name: %s', user_name)
                raise Exception('Invalid user/group name: %s' % user_name)

            # get merge requests for all projects for specified group
            for group in groups:
                projects = gl.group_projects.list(group_id=group.id)
                if len(projects) == 0:
                    log.debug("No projects found for user/group name %s",
                              user_name)
                for project in projects:
                        self.get_reviews(uname=user_name, project=project,
                                         fltr=fltr, value=value,
                                         duration=duration)

    def get_reviews(self, uname, project, fltr=None,
                    value=None, duration=None):
        """
        Fetches merge requests for specified username(groupname)
        and repo(project) name.
        Formats the merge requests details and print it on console.

        Args:
            user_name (str): Gitlab namespace
            repo_name (str): Gitlab project name for specified
                             namespace
            fltr (str): The filter(state) for pull requests, e.g, older
                        or newer
            value (str): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month,
                            hour, minute) for requests to be older or
                            newer than.
        """
        log.debug('Looking for merge requests for %s -> %s',
                  uname, project.name)

        # get list of open merge requests for a given repository(project)
        merge_requests = project.mergerequests.list(project_id=project.id,
                                                    state='opened')
        if len(list(merge_requests)) == 0:
            log.debug('No open merge requests found for %s/%s ',
                      uname, project.name)
        for mr in merge_requests:
            try:
                mr_date = datetime.datetime.strptime(
                    mr.created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                mr_date = datetime.datetime.strptime(
                    mr.created_at, '%Y-%m-%dT%H:%M:%SZ')
            """
            find the relative time difference between now
            and merge request filed
            """
            rel_diff = relativedelta(datetime.datetime.now(), mr_date)
            if (fltr is not None and value is not None and
                    duration is not None):
                """
                find the absolute time difference between
                now and merge request filed
                """
                abs_diff = datetime.datetime.now() - mr_date
                """
                check if pull request is older/newer than specified time
                interval
                """
                result = self.check_request_state(abs_diff, rel_diff,
                                                  fltr=fltr, value=value,
                                                  duration=duration)
                # skip the request if it doesn't match the specified criteria
                if not result:
                    log.debug("merge request '%s' is not %s than specified"
                              " time interval", mr.title, fltr)
                    continue
            # format the time interval pull request has been filed since
            time = self.format_duration(rel_diff)
            # fetch and format comments for pull request
            comments = []
            if(mr.user_notes_count == 1):
                comments.append('%s' % ', with 1 comment')
            elif(mr.user_notes_count > 1):
                comments.append('%s %s %s' % (', with',
                                              str(mr.user_notes_count),
                                              'comments'))
            comments = ''.join(comments)
            # format and print the resultant pull request string
            res = GitlabReviewRot(user=str(mr.author.username),
                                  title=str(mr.title),
                                  url=str(mr.web_url),
                                  time=time,
                                  comments=comments)
            log.info(res)

    def check_request_state(self, abs_diff, rel_diff, fltr, value, duration):
        return super(GitlabService,
                     self).check_request_state(abs_diff, rel_diff,
                                               fltr, value, duration)

    def format_duration(self, rel_diff):
        return super(GitlabService, self).format_duration(rel_diff)


class GitlabReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        return super(GitlabReviewRot, self).__init__(*args, **kwargs)

    def __str__(self):
        return super(GitlabReviewRot, self).__str__()
