from github import Github

g = Github("username", "password")

repolist = []
repolist.append("repository_name")
for repo in repolist:

    try:
        #get Repository object for given user/organization and repo name
        repo = g.get_user().get_repo(repo)
    
        #Get list of open pull requests for a given repo
        pullRequests = repo.get_pulls()
        
        for pr in pullRequests:
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
        print e
