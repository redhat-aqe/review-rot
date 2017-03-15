import config
from github import Github

#The line below is commented out for future scope of private repo
#g = Github(config.github['uname'], config.github['pwd'])

g = Github()

repolist = []
repolist.append("Random-Queries-Using-Amazon-Web-Service")
repolist.append("Google-Charts")

for repo_name in repolist:
    try:
        #get Repository object for given user/organization and repo name
        #repo = g.get_user().get_repo(repo_name)
        repo = g.get_user("nirzari18").get_repo(repo_name)
    
        #Get list of open pull requests for a given repo
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
        print "Something is wrong with the repository: " + repo_name
