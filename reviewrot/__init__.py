from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
# from reviewrot.gerritstack import GerritService


def get_git_service(git):
    """
    Returns git service as per requested.

    Args:
        git (str): String indicating git service requested.

    Returns:
        Returns desired git service
    """
    if git == "github":
        return GithubService()
    elif git == "gitlab":
        return GitlabService()
    elif git == "pagure":
        return PagureService()
    else:
        raise ValueError('requested git service %s is not valid' % (git))
    """
    elif git == "gerrit":
        return GerritService()
    """
