import config
import datetime
from dateutil.relativedelta import relativedelta
from os.path import expanduser
from github import Github

# get authenticated github object
g = Github(config.github['token'])

def main(state, val):
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
                get_pullrequest(uname, repo_name, state, val)
       
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
                    get_pullrequest(uname,repo.name, state, val)

def get_pullrequest(uname, repo_name, state, val):    
    try:
        # get repository object for given user/organization and repository name
        repo = uname.get_repo(repo_name)
        
        # get list of open pull requests for a given repository
        pull_requests = repo.get_pulls()

        for pr in pull_requests:
            user = pr.user.login
            title = pr.title
            url = pr.html_url

            # find the relative time difference between now and pull request filed
            rel_diff = relativedelta(datetime.datetime.now(), pr.created_at)
            time = find_duration(rel_diff)
            if state is not None and val is not None:
                # find the absolute time difference between now and pull request filed
                abs_diff = datetime.datetime.now() - pr.created_at

                # check for older/newer requests
                result = check_request_state(abs_diff, rel_diff, state, val)
                if result == 'skip':
                    continue
            if(pr.comments == 0): 
                comments = ""
            elif(pr.comments == 1): 
                comments = ", with 1 comment"
            else:
                comments = ", with  " + str(pr.comments) + " comments "
            
            print "@" + user + " filed '" + title + "' " + url + " since" + time + comments

    except Exception as e:
        print "Invalid repository: " + str(uname.login) + "/" + repo_name

def find_duration(rel_diff):
    time_list = ['year', 'month', 'day', 'hour', 'minute']
    time_dict = {'year': rel_diff.years, 'month': rel_diff.months, 'day': rel_diff.days, 'hour': rel_diff.hours, 'minute':rel_diff.minutes}
    for k,v in time_dict.items():
        if v == 0:
            if k in time_list:
                time_list[time_list.index(k)] = ""
        elif v == 1:
            if k in time_list:
                time_list[time_list.index(k)] = " " + str(v) + " " + k
        else:
            if k in time_list:
                time_list[time_list.index(k)] = " " + str(v) + " " + k + "s"

    return "%s%s%s%s%s" % (time_list[0], time_list[1], time_list[2], time_list[3], time_list[4])

def check_request_state(abs_diff, rel_diff, state, val): 
    if 'y' in val:
        if state == 'older' and rel_diff.years < int(val.strip('y')):
            return 'skip'
        elif state == 'newer' and rel_diff.years > int(val.strip('y')):
            return 'skip'
    if 'm' in val:
        # find the absolute time difference in months
        abs_month = (rel_diff.years*12) + rel_diff.months
        if state == 'older' and abs_month < int(val.strip('m')):
            return 'skip'
        elif state == 'newer' and abs_month > int(val.strip('m')):
            return 'skip'
    if 'd' in val:
        if state == 'older' and abs_diff.days < int(val.strip('d')):
            return 'skip'
        elif state == 'newer' and abs_diff.days > int(val.strip('d')):
            return 'skip'
    if 'h' in val:
        # find the absolute time difference in hours
        abs_hour = (abs_diff.total_seconds)/3600
        if state == 'older' and diff.years < int(val.strip('h')):
            return 'skip'
        elif state == 'newer' and abs_hour > int(val.strip('h')):
            return 'skip'
    if 'min' in val:
        # find the absolute time difference in minutes
        abs_min = ((abs_diff.total_seconds)/60)
        if state == 'older' and abs_min < int(val.strip('min')):
            return 'skip'
        elif state == 'newer' and abs_min > int(val.strip('min')):
            return 'skip'
    return ''

main(state=None, val=None)
