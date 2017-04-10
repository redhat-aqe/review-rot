import argparse
import yaml
import logging
import logging.config
from reviewrot import get_git_service
from os.path import expanduser

def main(fltr, value, duration):
    """
    starts execution
    """
    #TODO: Implement StreamHandler
    # logging.config.fileConfig('log.conf')
    log = logging.getLogger(__name__)
    home = expanduser('~')
    # read input from home directory for pull requests
    with open(home + '/.config.yaml', 'r') as f:
            config = yaml.load(f)
    
    #print config
    for item in config['git']:
        git = item.keys()[0].lower()
        # get git service
        git_service = get_git_service(git)
        if item.values()[0] is not None:
            for request in item.values()[0]:
                # get username and repository name to further request pull requests
                res = get_user_repo_name(request)
                # get pull requests for specified username and repository name
                git_service.request_reviews(user_name=res["user_name"], repo_name= res["repo_name"], fltr= fltr, value=value, duration=duration)

def get_user_repo_name(request):
    if '/' in request:
        try:
            # split usename and repository name
            user_name = request.split('/')[0]
            repo_name = request.split('/')[1]
            return {"user_name": user_name, "repo_name": repo_name}

        except:
            log.info("Invalid user/organization: " + user_name)
            print ("Invalid user/organization: " + user_name)
    else:
        user_name = request
        repo_name = None
        return {"user_name": user_name, "repo_name": repo_name}
    
if __name__ == '__main__':
    #TODO: Implement argparse
    main(fltr=None, value=None, duration=None)
