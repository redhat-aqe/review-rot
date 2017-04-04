from githubstack import GithubService
from gitlabstack import GitlabService
from pagurestack import PagureService
from gerritstack import GerritService

def get_git_service(git):
    if git == "github":
        return GithubService()
    elif git == "gitlab":
        return GitlabService()
    """
    elif git == "pagure":
        return PagureService()
    elif git == "gerrit":
        return GerritService()
    """

