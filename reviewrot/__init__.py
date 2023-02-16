"""doublt under init module."""
import argparse
import collections
import datetime
import logging
from os.path import exists, expanduser, expandvars
import re
from shutil import copyfile

from dateutil.relativedelta import relativedelta
import requests
from reviewrot.basereview import Age
from reviewrot.gerritstack import GerritService
from reviewrot.githubstack import GithubService
from reviewrot.gitlabstack import GitlabService
from reviewrot.pagurestack import PagureService
from reviewrot.phabricatorstack import PhabricatorService
from reviewrot.utils import is_wip
from six import iteritems
from six.moves import input
import yaml


log = logging.getLogger(__name__)

# Valid values of choices for arguments
CHOICES = {
    "format": ["oneline", "indented", "json"],
    "sort": ["submitted", "updated", "commented"],
}

DEFAULT_SUBJECT = "review-rot notification"


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
        raise ValueError("requested git service %s is not valid" % (git))


def get_arguments(cli_arguments, config):
    """
    Parse the arguments provided in configuration file and command line arguments.

    Args:
         cli_arguments (argparse.Namespace): Arguments provided by command
                                             line interface
         config (dict): Configuration from file
    Returns:
          arguments (dict): Returns the parsed arguments
    """
    config_arguments = config.get("arguments", {})

    if config_arguments is None:
        raise ValueError(
            "Argument section in config can't be empty,"
            " remove the section or add arguments"
        )
    config_mailer = config.get("mailer", {})
    config_irc = config.get("irc", {})

    parsed_arguments = {}
    command_line_args = vars(cli_arguments)

    for arg in command_line_args:
        if command_line_args.get(arg) is not None:
            parsed_arguments[arg] = command_line_args.get(arg)

    for argument in config_arguments:
        # Explicitly commandline arguments cannot be specified
        # false or none.
        if (
            command_line_args.get(argument) is None
            or command_line_args.get(argument) is False
        ):
            config_value = config_arguments.get(argument)
            if is_valid_choice(argument, config_value):
                parsed_arguments[argument] = config_value
            else:
                log.warn(
                    "Invalid choice '%s' provided for '%s' in"
                    " config file" % (config_value, argument)
                )

    # --debug, --reverse and --insecure or --cacert flags are used to
    # specify arguments from command line. If not specified, value will
    # be False or None. In this case, if these arguments are specified in
    # config file, then the value will be taken from the config file.
    if config_arguments.get("debug"):
        parsed_arguments["debug"] = True

    if config_arguments.get("reverse"):
        parsed_arguments["reverse"] = True

    email_in_config = config_arguments.get("email")
    if email_in_config:
        parsed_arguments["email"] = [
            email.strip() for email in email_in_config.split(",")
        ]

    if "subject" not in parsed_arguments and "subject" in config_arguments:
        parsed_arguments["subject"] = config_arguments["subject"]

    irc_in_config = config_arguments.get("irc")
    if irc_in_config:
        parsed_arguments["irc"] = [
            channel.strip() for channel in irc_in_config.split(",")
        ]

    age_in_config = config_arguments.get("age")
    if age_in_config:
        values = age_in_config.split(" ")
        parsed_arguments["age"] = ParseAge.parse(values)

    insecure = cli_arguments.insecure or config_arguments.get("insecure")
    cacert = cli_arguments.cacert or config_arguments.get("cacert")

    if insecure and cacert:
        raise ValueError("Certificate file can't be used with insecure flag")

    if insecure:
        parsed_arguments["ssl_verify"] = False
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
    elif cacert:
        cacert = expanduser(expandvars(cacert))
        if not exists(cacert):
            raise IOError("No CA certificate file found at %s" % cacert)
        parsed_arguments["ssl_verify"] = cacert
    else:
        parsed_arguments["ssl_verify"] = True

    format = parsed_arguments.get("format")
    show_last_comment = parsed_arguments.get("show_last_comment")
    if format == "oneline" and show_last_comment is not None:
        raise ValueError(
            "{} format doesn't support last comment functionality".format(format)
        )

    irc = parsed_arguments.get("irc")
    email = parsed_arguments.get("email")
    if email and format:
        raise ValueError("No format should be specified when selecting email output")

    if email and any(
        property not in config_mailer for property in ["server", "sender"]
    ):
        raise ValueError(
            "Missing mailer configuration."
            " Check examples/sampleinput_email.yaml "
            "for correct configuration."
        )

    if irc and format:
        raise ValueError("No format should be specified when selecting irc output")

    if irc and any(property not in config_irc for property in ["server", "port"]):
        raise ValueError(
            "Missing irc configuration."
            " Check examples/sampleinput_irc.yaml "
            "for correct configuration."
        )

    return parsed_arguments


class ParseAge(argparse.Action):
    """Custom argument parsing class that handles the --age argument."""

    def __call__(self, parser, namespace, values, option_string=None):
        """TODO: docstring goes here."""
        setattr(namespace, self.dest, self.parse(values))

    @staticmethod
    def parse(values):
        """TODO: docstring goes here."""
        if len(values) < 2:
            raise ValueError("Missing arguments")

        if values[0] not in ["older", "newer"]:
            raise ValueError("Wrong or missing state, only older/newer is allowed")

        state = values[0]
        values = values[1:]

        regex = re.compile(r"^(?P<value>\d+)(?P<unit>y|m|d|h|min)$")
        parts = {}
        unit_mapping = {
            "y": "years",
            "m": "months",
            "d": "days",
            "h": "hours",
            "min": "minutes",
        }
        for v in values:
            part = regex.search(v)
            if part is None:
                raise ValueError("Invalid unit " + v)

            unit = unit_mapping[part.group("unit")]
            parts[unit] = int(part.group("value"))

        delta = relativedelta(**parts)
        date = datetime.datetime.now() - delta

        return Age(date=date, state=state)


def parse_cli_args(args):
    """
    Parsing of command line arguments.

    Args:
        args (list): arguments passed to review-rot on command line

    Returns:
        parsed arguments (argparse.Namespace): Returns the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Lists pull/merge/change requests for github, gitlab,"
        " pagure, gerrit and phabricator"
    )
    default_config = expanduser("~/.reviewrot.yaml")
    parser.add_argument(
        "-c", "--config", default=default_config, help="Configuration file to use"
    )
    parser.add_argument(
        "--age",
        default=None,
        nargs="+",
        action=ParseAge,
        help="Filter pull request based on their relative age",
        metavar=("{older,newer}", "#y #m #d #h #min"),
    )
    parser.add_argument(
        "-f",
        "--format",
        default=None,
        choices=CHOICES["format"],
        help="Choose from one of a few different styles",
    )
    parser.add_argument(
        "--show-last-comment",
        nargs="?",
        metavar="DAYS",
        default=None,
        const=0,
        type=int,
        help="Show text of last comment and "
        "filter out pull requests in which "
        "last comments are newer than "
        "specified number of days",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Display results with the most recent first",
    )
    # With --sort argument added,  --comment-sort is kept for backwards
    # compatibility. Use --sort commented instead.
    parser.add_argument("--comment-sort", action="store_true", help=argparse.SUPPRESS)
    # Default value is left as None to ensure that the argument passed here
    # takes precedence over the value in configuration arguments.
    parser.add_argument(
        "--sort",
        default=None,
        choices=CHOICES["sort"],
        help=(
            "Display results sorted by the chosen event " "time. Defaults to " "{}"
        ).format(CHOICES["sort"][0]),
    )
    parser.add_argument(
        "--debug", action="store_true", help="Display debug logs on console"
    )
    parser.add_argument(
        "--email", nargs="+", default=None, help="send output to list of email adresses"
    )
    parser.add_argument("--subject", help="Email subject text")
    parser.add_argument(
        "--irc",
        nargs="+",
        metavar="CHANNEL",
        default=None,
        help="send output to list of irc channels",
    )
    parser.add_argument(
        "--ignore-wip", help="Omit WIP PRs/MRs from output", action="store_true"
    )
    ssl_group = parser.add_argument_group("SSL")
    ssl_group.add_argument(
        "-k",
        "--insecure",
        default=False,
        action="store_true",
        help="Disable SSL certificate verification " "(not recommended)",
    )
    ssl_group.add_argument(
        "--cacert",
        default=None,
        help="Path to CA certificate to use for SSL " "certificate verification",
    )

    return parser.parse_args(args)


def is_valid_choice(argument, value):
    """
    Checks if value is valid choice or not for given argument.

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
    Loads the config file from the user's home directory or user specified location.

    Args:
         config_path (str): Path to the configuration file
    Returns:
        config(dict): Returns the configurations
    """
    if not exists(config_path):
        raise RuntimeError("No config file found at %s" % config_path)

    # read input from the config file for pull requests
    config = load_ordered_config(config_path)
    if isinstance(config, list):
        # convert to new format
        config = dict(git_services=config, arguments=None)
        prompt = "Would you like to rewrite the config file in new " "format [y/n] :"

        input_choice = input(prompt)

        answer = str(input_choice).lower().strip()
        if answer == "y" or answer == "":
            print
            # Take the backup of configuration file and
            # save the configurations in new format
            backup_path = config_path + ".backup"
            log.info("Creating back up at " + backup_path)
            copyfile(config_path, backup_path)
            log.info("Rewriting %r in new format!" % config_path)
            with open(config_path, "w") as f:
                f.write(yaml.dump(config, default_flow_style=False))

    return config


def load_ordered_config(config_path):
    """
    Loads the configuration in the same order as it's defined in yaml.

    So that, while saving it in new format, order is maintained
    Args:
          config_path (str): Path to the configuration file
    Returns:
          config(dict): Returns the configurations in the defined ordered
    """
    #  To load data from yaml in ordered dict format
    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

    def dict_representer(dumper, data):
        """TODO: docstring goes here."""
        return dumper.represent_mapping(_mapping_tag, iteritems(data))

    def dict_constructor(loader, node):
        """TODO: docstring goes here."""
        return collections.OrderedDict(loader.construct_pairs(node))

    yaml.add_representer(collections.OrderedDict, dict_representer)
    yaml.add_constructor(_mapping_tag, dict_constructor)

    #  format the output to print a blank scalar rather than null
    def represent_none(self, _):
        """TODO: docstring goes here."""
        return self.represent_scalar("tag:yaml.org,2002:null", "")

    yaml.add_representer(type(None), represent_none)

    # read input from home directory for pull requests
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def remove_wip(results):
    """
    Removes WIP reviews from results.

    Args:
        results (list): list of BaseReview instances

    Returns:
        res (list): list of BaseReview instances with WIP
                    reviews removed
    """
    return [result for result in results if not is_wip(str(result.title))]
