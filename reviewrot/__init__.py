from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService


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
    else:
        raise ValueError('requested git service %s is not valid' % (git))
