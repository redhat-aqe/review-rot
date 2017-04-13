import os
import logging
import argparse
import yaml
from os.path import expanduser
from reviewrot import get_git_service


def main(fltr, value, duration):
    """
    Reads input configuration file.
    Calls appropriate git service with suitable inputs.

    fltr (str): The filter(state) for review requests, e.g, older or newer
    value (int): The value in terms of duration for requests
                 to be older or newer than
    duration (str): The duration in terms of period(year,month,hour,minute)
                    for requests to be older or newer than.
    """
    home = expanduser('~')

    path_to_config = os.path.join(home, '.reviewrot.yaml')
    if not os.path.exists(path_to_config):
        raise RuntimeError("No config '.reviewrot.yaml' provided. Please"
                           " specify it in home directory: %s" % home)
    # read input from home directory for pull requests
    with open(path_to_config, 'r') as f:
        config = yaml.load(f)

    for item in config:
        # get git service
        git_service = get_git_service(item['type'])
        """
        check if username and/or repository information is given for
        specified git service
        """
        if item['repos'] is not None:
            # for each input call specified git service
            for data in item['repos']:
                """
                split and format username and repository name to further
                request pull requests
                """
                res = format_user_repo_name(data)
                """
                get pull requests for specified git service, username
                and repository name
                """
                git_service.request_reviews(user_name=res['user_name'],
                                            repo_name=res['repo_name'],
                                            fltr=fltr,
                                            value=value,
                                            duration=duration,
                                            token=item['token'],
                                            host=item['host']
                                            )


def format_user_repo_name(data):
    """
    Takes input from configuration file for a specified git service.
    Split or fomat it as per required.
    Args:
        data (str): combination of username and/or reponame

    Returns:
        Dictionary representation of username and reponame
    """
    if '/' in data:
        # Splitting only once in case "/" is a value character in the data.
        user_name, repo_name = data.split('/', 1)

    else:
        user_name = data
        repo_name = None
    return {'user_name': user_name, 'repo_name': repo_name}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Lists pull/merge requests for github, gitlab,'
                    'pagure and gerrit')
    parser.add_argument('-s', '--state',
                        default=None,
                        choices=['older', 'newer'],
                        help="Pull requests state 'older' or 'newer'"
                        )
    parser.add_argument('-v', '--value',
                        default=None,
                        type=int,
                        help='Pull requests duration in terms of value(int)'
                        )
    parser.add_argument('-d', '--duration',
                        default=None,
                        choices=['y', 'm', 'd', 'h', 'min'],
                        help='Pull requests duration in terms of y=years,'
                             'm=months, d=days, h=hours, min=minutes')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    options = []
    for k, v in vars(args).items():
        if 'debug' not in k:
            options.append(v)
    # count occurence of None in argument list excluding arg for debug
    count = options.count(None)
    # check if either none or all arguments are none
    if count != 0 and count != 3:
        parser.error('Either none or all arguments are required')

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    main(fltr=args.state, value=args.value, duration=args.duration)
