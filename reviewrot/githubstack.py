import yaml
import logging
import datetime
from dateutil.relativedelta import relativedelta
from base import BaseService, BaseReviewRot
from github import Github
from os.path import expanduser

class GithubService(BaseService):
    """
    This class represents Github. The reference can be found here: https://developer.github.com/v3/
    """
    def __init__(self):

        home = expanduser('~')        
        # get authenticated github object
        with open(home + '/.config.yaml', 'r') as f:
            config = yaml.load(f)
        self.g = Github(config['creds']['github']['token'])
        self.log = logging.getLogger(__name__)
    
    def request_reviews(self, user_name, repo_name=None, fltr=None, value=None, duration=None):
        # if Repository name is explicitely provided 
        if repo_name is not None:
            try:
                # get user object
                uname = self.g.get_user(user_name)

            except:
                self.log.info("Invalid user/organization: " + user_name)
                print ("Invalid user/organization: " + user_name)

            else:
                # list pull requests for specified username and repository name
                self.get_reviews(uname=uname, repo_name=repo_name, fltr=fltr, value=value, duration=duration)
        else:
            # get pull requests for all repositories for specified user/organization 
            try:
                # get user object
                uname = self.g.get_user(user_name)
            except:
                self.log.info("Invalid user/organization: " + user_name)
                print ("Invalid user/organization: " + user_name)

            else:
                # get all the respositories for specified user/organization
                repo_list = uname.get_repos()
                # list pull requests for all repositories for specified user/organization
                for repo in repo_list:
                    self.get_reviews(uname=uname, repo_name=repo.name, fltr=fltr, value=value, duration=duration)

    def get_reviews(self, uname, repo_name, fltr=None, value=None, duration=None):    
        try:
            # get repository object for given user/organization and repository name
            repo = uname.get_repo(repo_name)
            # get list of open pull requests for a given repository
            pull_requests = repo.get_pulls()
            for pr in pull_requests:
                # find the relative time difference between now and pull request filed
                rel_diff = relativedelta(datetime.datetime.now(), pr.created_at)
                if fltr is not None and value is not None and duration is not None:
                    # find the absolute time difference between now and pull request filed
                    abs_diff = datetime.datetime.now() - pr.created_at
                    # check for older/newer requests
                    result = self.check_request_state(abs_diff, rel_diff, fltr, value, duration)
                    if result == True:
                        continue
                # format time
                time = self.find_duration(rel_diff)
                if(pr.comments == 0): 
                    comments = ""
                elif(pr.comments == 1): 
                    comments = ", with 1 comment"
                else:
                    comments = ", with  " + str(pr.comments) + " comments "
                res = GithubReviewRot(user=pr.user.login, title=pr.title, url=pr.html_url, time=time, comments=comments)
                print res

        except Exception as e:
            print e
            #self.log.info("Invalid repository: " + str(uname.login) + "/" + repo_name)
            #print ("Invalid repository: " + str(uname.login) + "/" + repo_name)

    def check_request_state(self, abs_diff, rel_diff, fltr, value, duration):
        return super(GithubService, self).check_request_state(abs_diff, rel_diff, fltr, value, duration)

    def find_duration(self, rel_diff):
        return super(GithubService, self).find_duration(rel_diff)

class GithubReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        return super(GithubReviewRot, self).__init__(*args, **kwargs)

    def __str__(self):
        return super(GithubReviewRot, self).__str__()
