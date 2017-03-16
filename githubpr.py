import config
from os.path import expanduser
from github import Github

# get authenticated github object
g = Github(config.github['uname'], config.github['pwd'])

def main():
    home = expanduser('~')
    # read input from home directory for pull requests
    with open (home + '/.pull-requests') as f:
        request_list = f.read().splitlines()

    for request in request_list:
        # check if repository name is given for specified user/organization
        if '/' in request:
            # split usename and repository name
            user_name = request.split('/')[0]
            repo_name = request.split('/')[1]
            try:
                # get user object
                uname = g.get_user(user_name)

            except:
                print "Invalid user/organization: " + user_name

            else:
                # list pull requests for specified username and repository name
                get_pullrequest(uname, repo_name)
       
        # get pull requests for all repositories for specified user/organization 
        else:
            try:
                # get user object
                uname = g.get_user(request)
            except:
                print "Invalid user/organization: " + request

            else:
                # get all the respositories for specified user/organization
                repo_list = uname.get_repos()
                # list pull requests for all repositories for specified user/organization
                for repo in repo_list:
                    get_pullrequest(uname,repo.name)

def get_pullrequest(uname, repo_name):    
    try:
        #get repository object for given user/organization and repository name
        repo = uname.get_repo(repo_name)

        #get list of open pull requests for a given repository
        pull_requests = repo.get_pulls()

        for pr in pull_requests:
            user = pr.user.login
            title = pr.title
            url = pr.html_url
            days = str(pr.created_at.date())
            if(pr.comments == 0): 
                comments = ""
            elif(pr.comments == 1): 
                comments = ", with 1 comment"
            else:
                comments = ", with  " + str(pr.comments) + " comments "

            print "@" + user + " filed '" + title + "' " + url + " on " + days + comments

    except Exception as e:
        print "Invalid repository: " + str(uname.login) + "/" + repo_name

main()
