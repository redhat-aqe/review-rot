"""gitlabstack module."""
import datetime
import logging
import os

import gitlab
from gitlab.exceptions import GitlabGetError, GitlabListError
from requests.exceptions import SSLError
from reviewrot.basereview import BaseReview, BaseService, LastComment

log = logging.getLogger(__name__)


class GitlabService(BaseService):
    """
    This class represents Gitlab.

    The reference can be found here:
    https://docs.gitlab.com/ee/api/
    """

    def request_reviews(
        self,
        user_name,
        repo_name=None,
        age=None,
        show_last_comment=None,
        token=None,
        host=None,
        ssl_verify=True,
        **kwargs
    ):
        """
        Creates a gitlab object.

        Requests merge requests for specified username and repo name.
        If repo name is not provided then requests merge requests
        for all repos for specified username/organization.

        Args:
            user_name (str): Gitlab namespace
            repo_name (str): Gitlab project name for specified
                          namespace
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days
            token (str): Gitlab token for authentication
            host (str): Gitlab host name for authentication
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
            response (list): Returns the list of pull requests for
                             specified user(group) name and projectname or all
                             projectname for given groupname
        """
        gl = gitlab.Gitlab(host, token, ssl_verify=ssl_verify)
        try:
            gl.auth()
        except SSLError as e:
            log.exception("Error during authentification: %s", str(e))

        log.debug("Gitlab instance created: %s", gl)
        response = []
        # if Repository name is explicitly provided
        if repo_name is not None:
            try:
                # get project object for given repo_name(project name)
                project = gl.projects.get(os.path.join(user_name, repo_name))
            except GitlabGetError:
                log.exception("Project %s not found for user %s", repo_name, user_name)
                raise Exception(
                    "Project %s not found for user %s" % (repo_name, user_name)
                )

            # get merge requests for specified username and project name
            res = self.get_reviews(
                uname=user_name,
                project=project,
                age=age,
                show_last_comment=show_last_comment,
                image=(
                    project.avatar_url
                    or gl.groups.get(project.namespace["id"]).avatar_url
                ),
            )
            # extend in case of a non empty result
            if res:
                response.extend(res)

        else:
            # get group object
            group = gl.groups.get(user_name)
            if not group:
                log.debug("Invalid user/group name: %s", user_name)
                raise Exception("Invalid user/group name: %s" % user_name)

            # get projects list for specified group
            group_projects = group.projects.list(all=True, simple=True)

            if not group_projects:
                log.debug("No projects found for user/group name %s", user_name)

            # get merge requests for all projects for specified group
            for group_project in group_projects:
                project = gl.projects.get(group_project.id)
                res = self.get_reviews(
                    uname=user_name,
                    project=project,
                    age=age,
                    image=project.avatar_url or group.avatar_url,
                )

                # extend in case of a non empty result
                if res:
                    response.extend(res)
        return response

    def get_reviews(self, uname, project, age=None, show_last_comment=None, image=None):
        """
        Fetches merge requests for specified username(groupname) and repo(project) name.

        Formats the merge requests details and print it on console.

        Args:
            uname (str): Gitlab namespace
            project (str): Gitlab project name for specified
                           namespace
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days

        Returns:
            res_ (list): Returns list of pull requests for specified
                         user(group) name and project name
        """
        log.debug("Looking for merge requests for %s -> %s", uname, project.name)

        try:
            # get list of open merge requests for a given repository(project)
            merge_requests = project.mergerequests.list(
                project_id=project.id, state="opened"
            )

        # merge requests are not available for this project
        except GitlabListError:
            merge_requests = []

        if not merge_requests:
            log.debug("No open merge requests found for %s/%s ", uname, project.name)
        res_ = []
        for mr in merge_requests:
            last_comment = self.get_last_comment(mr)

            try:
                mr_date = datetime.datetime.strptime(
                    mr.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                mr_updated_date = datetime.datetime.strptime(
                    mr.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                )

            except ValueError:
                mr_date = datetime.datetime.strptime(
                    mr.created_at, "%Y-%m-%dT%H:%M:%SZ"
                )
                mr_updated_date = datetime.datetime.strptime(
                    mr.updated_at, "%Y-%m-%dT%H:%M:%SZ"
                )

            """ check if review request is older/newer than specified time
            interval"""
            result = self.check_request_state(mr_date, age)

            if result is False:
                log.debug(
                    "merge request '%s' is not %s than specified" " time interval",
                    mr.title,
                    age.state,
                )
                continue

            if last_comment and show_last_comment:
                if self.has_new_comments(last_comment.created_at, show_last_comment):
                    log.debug(
                        "merge request '%s' has new " "comments  in last %s days",
                        mr.title,
                        show_last_comment,
                    )
                    continue

            res = GitlabReview(
                user=mr.author["username"],
                title=mr.title,
                url=mr.web_url,
                time=mr_date,
                updated_time=mr_updated_date,
                comments=mr.user_notes_count,
                image=image or GitlabReview.logo,
                last_comment=last_comment,
                project_name=project.name,
                project_url=project.web_url,
            )

            log.debug(res)
            res_.append(res)
        return res_

    def get_last_comment(self, mr):
        """
        Returns information about last comment of given merge request.

        Args:
            mr (gitlab.v4.objects.ProjectMergeRequest): Gitlab merge request

        Returns:
            last comment (LastComment): Returns namedtuple LastComment
            with data related to last comment
        """
        for note in mr.notes.list(iterator=True):
            if not note.system:
                return LastComment(
                    author=note.author["username"],
                    body=note.body,
                    created_at=datetime.datetime.strptime(
                        note.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                )


class GitlabReview(BaseReview):
    """TODO: docstring goes here."""

    # XXX - Here just until we figure out how to do gitlab avatars.
    logo = "https://docs.gitlab.com/assets/images/gitlab-logo.svg"
    pass
