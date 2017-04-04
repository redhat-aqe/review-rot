import yaml
import logging
import gitlab
import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from base import BaseService, BaseReviewRot
from os.path import expanduser

class GitlabService(BaseService):
    """
    This class represents Gitlab. The reference can be found here: https://docs.gitlab.com/ee/api/
    """
    def __init__(self):

        home = expanduser('~')
        # get authenticated gitlab object
        with open(home + '/.pull-requests.yaml', 'r') as f:
            config = yaml.load(f)
        self.gl = gitlab.Gitlab(config['creds']['gitlab']['host'], config['creds']['gitlab']['token'])
        self.gl.auth()
        self.log = logging.getLogger(__name__)


    def request_reviews(self, user_name, repo_name=None, fltr=None, value=None):

        # if Repository name is explicitely provided 
        if repo_name is not None:
            # get project object for given repo_name(project name)
            project = self.gl.projects.get(user_name + '/' + repo_name)
            # list merge requests for specified username and project name
            self.get_reviews(uname=user_name, project=project, fltr=fltr, value=value)

        else:
            # get merge requests for all projects for specified group 
            try:
                # get user object
                groups = self.gl.groups.search(user_name)
                for group in groups:
                    projects = self.gl.group_projects.list(group_id=group.id)
                    for project in projects:
                        self.get_reviews(uname=user_name, project=project, fltr=fltr, value=value)

            except Exception as e:
                print e
                #self.log.info("Invalid user group: " + user_name)

    def get_reviews(self, uname, project, fltr=None, value=None):
        try:
            # get list of open merge requests for a given repository(project)
            merge_requests = project.mergerequests.list(project_id=project.id, state='opened')
            for mr in merge_requests:
                try:
                    mr_date = datetime.datetime.strptime(mr.created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    mr_date = datetime.datetime.strptime(mr.created_at, '%Y-%m-%dT%H:%M:%SZ')
                # find the relative time difference between now and merge request filed
                rel_diff = relativedelta(datetime.datetime.now(), mr_date)
                if fltr is not None and value is not None:
                    # find the absolute time difference between now and merge request filed
                    abs_diff = datetime.datetime.now() - mr_date
                    # check for older/newer requests
                    result = self.check_request_state(abs_diff, rel_diff, fltr, value)
                    if result == True:
                        continue
                # format time
                time = self.find_duration(rel_diff)
                if(mr.user_notes_count == 0):
                    comments = ""
                elif(mr.user_notes_count == 1):
                    comments = ", with 1 comment"
                else:
                    comments = ", with  " + str(mr.user_notes_count) + " comments "
                
                res = GitlabReviewRot(user=str(mr.author.username), title=str(mr.title), url=str(mr.web_url), time=time, comments=comments)
                print res

        except Exception as e:
            print e
            #self.log.info("Invalid repository: " + str(uname.login) + "/" + repo_name)
            #print ("Invalid repository: " + str(uname.login) + "/" + repo_name)

    def check_request_state(self, abs_diff, rel_diff, fltr, value):
        return super(GitlabService, self).check_request_state(abs_diff, rel_diff, fltr, value)

    def find_duration(self, rel_diff):
        return super(GitlabService, self).find_duration(rel_diff)

class GitlabReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        return super(GitlabReviewRot, self).__init__(*args, **kwargs)

    def __str__(self):
        return super(GitlabReviewRot, self).__str__()
