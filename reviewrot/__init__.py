import collections
import logging
import os
import argparse
import re
from os.path import expanduser, expandvars
from shutil import copyfile
from six.moves import input
from six import iteritems

from reviewrot.gerritstack import GerritService
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
from reviewrot.phabricatorstack import PhabricatorService

import yaml

log = logging.getLogger(__name__)

CHOICES = {
    'duration': ['y', 'm', 'd', 'h', 'min'],
    'state': ['older', 'newer'],
    'format': ['oneline', 'indented', 'json'],
    'sort': ['submitted', 'updated', 'commented'],
}


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
    elif git == "gerrit":
        return GerritService()
    elif git == "phabricator":
        return PhabricatorService()
    else:
        raise ValueError('requested git service %s is not valid' % (git))


def get_arguments(cli_arguments, config):
    """
       Parse the arguments provided in configuration file
       and command line arguments
       Args:
            cli_arguments (argparse.Namespace): Arguments provided by command
                                                line interface
            config (dict): Configuration from file
       Returns:
             arguments (dict): Returns the parsed arguments
     """

    config_arguments = config.get('arguments', {})

    if config_arguments is None:
        raise ValueError(
            'Argument section in config can\'t be empty,'
            ' remove the section or add arguments'
        )
    config_mailer = config.get('mailer', {})
    config_irc = config.get('irc', {})

    parsed_arguments = {}
    command_line_args = vars(cli_arguments)
    grouped_arguments = {'state', 'duration', 'value'}
    logged_error = False

    for arg in command_line_args:
        if command_line_args.get(arg) is not None:
            parsed_arguments[arg] = command_line_args.get(arg)

    for argument in config_arguments:
        # Explicitly commandline arguments cannot be specified
        # false or none.
        if command_line_args.get(argument) is None or \
           command_line_args.get(argument) is False:
            # if argument is present in grouped_arguments,
            # all the associated arguments should also
            # be specified in the config file
            if argument not in grouped_arguments or \
                (argument in grouped_arguments and
                 grouped_arguments.issubset(config_arguments.keys())):
                config_value = config_arguments.get(argument)
                if is_valid_choice(argument, config_value):
                    parsed_arguments[argument] = config_value
                else:
                    log.warn("Invalid choice '%s' provided for '%s' in"
                             " config file" %
                             (config_value, argument))
            elif not logged_error:
                log.warn("Either no or all arguments (state, duration "
                         "and value) are required in config file")
                logged_error = True

    # --debug, --reverse and --insecure or --cacert flags are used to
    # specify arguments from command line. If not specified, value will
    # be False or None. In this case, if these arguments are specified in
    # config file, then the value will be taken from the config file.
    if config_arguments.get('debug'):
        parsed_arguments['debug'] = True

    if config_arguments.get('reverse'):
        parsed_arguments['reverse'] = True

    email_in_config = config_arguments.get('email')
    if email_in_config:
        parsed_arguments['email'] = [
            email.strip() for email in email_in_config.split(',')
        ]

    irc_in_config = config_arguments.get('irc')
    if irc_in_config:
        parsed_arguments['irc'] = [
            channel.strip() for channel in irc_in_config.split(',')
        ]

    parsed_arguments['ssl_verify'] = False if cli_arguments.insecure \
        else cli_arguments.cacert

    if parsed_arguments.get('ssl_verify') is None:
        if config_arguments.get('insecure'):
            parsed_arguments['ssl_verify'] = False
        elif 'cacert' in config_arguments:
            # expand ~, environment variables, etc if it's a path
            parsed_arguments['ssl_verify'] = config_arguments.get('cacert')
        else:
            parsed_arguments['ssl_verify'] = True

    if isinstance(parsed_arguments['ssl_verify'], str):
        parsed_arguments['ssl_verify'] = \
            expanduser(expandvars(parsed_arguments['ssl_verify']))
        if not os.path.exists(parsed_arguments['ssl_verify']):
            raise IOError("No certificate file found at %s "
                          % parsed_arguments['ssl_verify'])

    if (parsed_arguments.get('insecure') and
            parsed_arguments.get('cacert', None)):
        raise ValueError("Certificate file can't be used with insecure flag")

    format = parsed_arguments.get('format')
    show_last_comment = parsed_arguments.get('show_last_comment')
    if (format == 'oneline' and
            show_last_comment is not None):
        raise ValueError(
            '{} format doesn\'t support last comment functionality'.format(
                format
            )
        )

    irc = parsed_arguments.get('irc')
    email = parsed_arguments.get('email')
    if email and format:
        raise ValueError(
            'No format should be specified when selecting email output'
        )

    if email and any(property not in config_mailer for property in ['server', 'sender']):
            raise ValueError(
                'Missing mailer configuration.'
                ' Check examples/sampleinput_email.yaml '
                'for correct configuration.'
            )

    if irc and format:
        raise ValueError(
            'No format should be specified when selecting irc output'
        )

    if irc and any(property not in config_irc for property in ['server', 'port']):
        raise ValueError(
            'Missing irc configuration.'
            ' Check examples/sampleinput_irc.yaml '
            'for correct configuration.'
        )

    return parsed_arguments


def parse_cli_args(args):

    parser = argparse.ArgumentParser(
        description='Lists pull/merge/change requests for github, gitlab,'
                    ' pagure, gerrit and phabricator')
    default_config = os.path.expanduser('~/.reviewrot.yaml')
    parser.add_argument('-c', '--config',
                        default=default_config,
                        help='Configuration file to use')
    parser.add_argument('-s', '--state',
                        default=None,
                        choices=CHOICES['state'],
                        help="Pull requests state 'older' or 'newer'"
                        )
    parser.add_argument('-v', '--value',
                        default=None,
                        type=int,
                        help='Pull requests duration in terms of value(int)'
                        )
    parser.add_argument('-d', '--duration',
                        default=None,
                        choices=CHOICES['duration'],
                        help='Pull requests duration in terms of y=years,'
                             'm=months, d=days, h=hours, min=minutes')
    parser.add_argument('-f', '--format',
                        default=None,
                        choices=CHOICES['format'],
                        help='Choose from one of a few different styles')
    parser.add_argument('--show-last-comment',
                        nargs='?',
                        metavar="DAYS",
                        default=None,
                        const=0,
                        type=int,
                        help='Show text of last comment and '
                             'filter out pull requests in which '
                             'last comments are newer than '
                             'specified number of days')
    parser.add_argument('--reverse', action='store_true',
                        help='Display results with the most recent first')
    # With --sort argument added,  --comment-sort is kept for backwards
    # compatibility. Use --sort commented instead.
    parser.add_argument('--comment-sort', action='store_true',
                        help=argparse.SUPPRESS)
    # Default value is left as None to ensure that the argument passed here
    # takes precedence over the value in configuration arguments.
    parser.add_argument('--sort',
                        default=None,
                        choices=CHOICES['sort'],
                        help=('Display results sorted by the chosen event '
                              'time. Defaults to '
                              '{}').format(CHOICES['sort'][0]))
    parser.add_argument('--debug', action='store_true',
                        help='Display debug logs on console')
    parser.add_argument('--email', nargs="+",
                        default=None,
                        help='send output to list of email adresses')
    parser.add_argument('--irc', nargs='+',
                        metavar="CHANNEL",
                        default=None,
                        help='send output to list of irc channels')

    ssl_group = parser.add_argument_group('SSL')
    ssl_group.add_argument('-k', '--insecure',
                           default=False,
                           action='store_true',
                           help='Disable SSL certificate verification '
                                '(not recommended)')
    ssl_group.add_argument('--cacert',
                           default=None,
                           help='Path to CA certificate to use for SSL '
                                'certificate verification')

    parsed_args = parser.parse_args(args)
    options = (
        parsed_args.state,
        parsed_args.value,
        parsed_args.duration
    )
    if any(options) and not all(options):
        parser.error('Either no or all arguments are required')

    return parsed_args


def is_valid_choice(argument, value):
    """
       Checks if value is valid choice or not for given argument
       Args:
            value (str): argument value
            argument (str): argument as key
       Returns:
             Returns boolean value
     """
    if CHOICES.get(argument) is None or value in CHOICES.get(argument):
            return True
    return False


def load_config_file(config_path):
    """
       Loads the configuration file from the user's home directory
       or user specified location
       Args:
            config_path (str): Path to the configuration file
       Returns:
           config(dict): Returns the configurations
       """
    if not os.path.exists(config_path):
        raise RuntimeError("No config file found at %s" % config_path)

    # read input from the config file for pull requests
    config = load_ordered_config(config_path)
    if isinstance(config, list):
        # convert to new format
        config = dict(git_services=config, arguments=None)
        prompt = "Would you like to rewrite the config file in new " \
                 "format [y/n] :"

        input_choice = input(prompt)

        answer = str(input_choice).lower().strip()
        if answer == 'y' or answer == '':
            print
            # Take the backup of configuration file and
            # save the configurations in new format
            backup_path = config_path + '.backup'
            log.info("Creating back up at " + backup_path)
            copyfile(config_path, backup_path)
            log.info("Rewriting %r in new format!" % config_path)
            with open(config_path, 'w') as f:
                f.write(yaml.dump(config, default_flow_style=False))

    return config


def load_ordered_config(config_path):
    """
      Loads the configuration in the same order as it's defined in yaml file,
      so that, while saving it in new format, order is maintained
      Args:
            config_path (str): Path to the configuration file
      Returns:
            config(dict): Returns the configurations in the defined ordered
    """

    #  To load data from yaml in ordered dict format
    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

    def dict_representer(dumper, data):
        return dumper.represent_mapping(_mapping_tag, iteritems(data))

    def dict_constructor(loader, node):
        return collections.OrderedDict(loader.construct_pairs(node))

    yaml.add_representer(collections.OrderedDict, dict_representer)
    yaml.add_constructor(_mapping_tag, dict_constructor)

    #  format the output to print a blank scalar rather than null
    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', u'')

    yaml.add_representer(type(None), represent_none)

    # read input from home directory for pull requests
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def remove_wip(results):
    """
    Removes WIP reviews from results

    Args:
        results (list): list of BaseReview instances

    Returns:
        res (list): list of BaseReview instances with WIP
                    reviews removed
    """

    res = []
    for result in results:
        match = re.match(r'^(\[WIP\]\s*|WIP:\s*|WIP\s+)+\s*', str(result.title), re.IGNORECASE)
        if not match:
            res.append(result)

    return res
