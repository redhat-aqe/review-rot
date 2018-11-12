import collections
import logging
import os
import platform
from os.path import expanduser, expandvars
from shutil import copyfile
from select import select
import sys

from reviewrot.gerritstack import GerritService
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService

import yaml

log = logging.getLogger(__name__)


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
    else:
        raise ValueError('requested git service %s is not valid' % (git))


def get_arguments(cli_arguments, config_arguments, choices):
    """
       Parse the arguments provided in configuration file
       and command line arguments
       Args:
            cli_arguments (argparse.Namespace): Arguments provided by command
                                                line interface
            config_arguments (dict): Arguments specified in yaml file
            choices (dict): valid values of choices for arguments
       Returns:
             arguments (dict): Returns the parsed arguments
     """
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
                if is_valid_choice(argument, config_value, choices):
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

    parsed_arguments['ssl_verify'] = False if cli_arguments.insecure \
        else cli_arguments.cacert

    if parsed_arguments.get('ssl_verify') is None:
        if config_arguments.get('insecure'):
            parsed_arguments['ssl_verify'] = not \
                config_arguments.get('insecure')
        elif 'cacert' in config_arguments:
            # expand ~, environment variables, etc if it's a path
            parsed_arguments['ssl_verify'] = config_arguments.get('cacert')
        else:
            parsed_arguments['ssl_verify'] = True


    if isinstance(parsed_arguments['ssl_verify'], str):
        parsed_arguments['ssl_verify'] = \
            expanduser(expandvars(parsed_arguments['ssl_verify']))
        if not os.path.exists(parsed_arguments['ssl_verify'] ):
            raise IOError("No certificate file found at %s" % parsed_arguments['ssl_verify'])

    if parsed_arguments.get('insecure') and parsed_arguments.get('cacert', None):
        raise ValueError("Certificate file can't be used with insecure flag")

    return parsed_arguments


def is_valid_choice(argument, value, choices):
    """
       Checks if value is valid choice or not for given argument
       Args:
            value (str): argument value
            choices (dict): valid values of choices for arguments
            argument (str): argument as key
       Returns:
             Returns boolean value
     """
    if choices.get(argument) is None or value in choices.get(argument):
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

        input_choice = raw_input(prompt)

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
        return dumper.represent_mapping(_mapping_tag, data.iteritems())

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
        config = yaml.load(f)
    return config
