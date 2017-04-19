from reviewrot.githubstack import GithubService

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
    else:
        raise ValueError('requested git service %s is not valid' % (git))
