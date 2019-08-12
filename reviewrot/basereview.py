import datetime
import hashlib
import json
import logging
import time
import textwrap

from collections import OrderedDict, namedtuple

from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)

LastComment = namedtuple('LastComment', ('author', 'body', 'created_at'))
Age = namedtuple('Age', ('date', 'state'))


def gravatar(email):
    """ Return the url to the public gravatar for an email. """
    digest = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
    default = "?default=retro"
    return "https://www.gravatar.com/avatar/" + digest + default


class BaseService(object):
    def check_request_state(self, created_at, age):
        """
        Checks if the review request is older or newer than specified
        time interval.
        Args:
            created_at (str): the date review request was filed
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
        Returns:
            True if the review request is older/newer than
            specified date, False otherwise
        """

        if age is None:
            return True

        if (age.state == 'newer' and created_at > age.date) or \
                (age.state == 'older' and created_at < age.date):
            return True

        return False

    def has_new_comments(self, last_activity, days):
        """
        Checks if the comment has been added in the last days
        Args:
            last_activity (datetime.datetime): When was the last comment added
            days (int) Number of days
        Returns:
            Boolean stating whether the comment has been added
            in the last days
        """
        today = datetime.datetime.now()

        if last_activity and days:
            delta = today - last_activity
            return delta.days < days

        return False

    def _decode_response(self, response):
        """
        Remove Gerrit's prefix and convert to JSON.
        Args:
            response (Response): Content is decoded from response object
        Returns:
            Converted JSON content
        Raises:
            ValueError if the content is not in proper json format.
        """
        gerrit_json_prefix = ")]}\'\n"
        content = response.content.strip()
        try:
            if response.encoding:
                content = content.decode(response.encoding)
            if content.startswith(gerrit_json_prefix):
                content = content[len(gerrit_json_prefix):]
            return json.loads(content)
        except ValueError:
            raise ValueError('Invalid json content: %s' % content)

    def _call_api(self, url, method='GET', ssl_verify=True):
        """
        Method used to call the API.
        It returns the raw JSON returned by the API or raises an exception
        if something goes wrong.
        Args:
            url(str): URL for git based service
            method (str): the URL to call, can be GET, POST, DELETE, UPDATE...
                          Defaults to GET
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
            raw JSON returned by API
        """
        decoded_response = ''
        response = self.get_response(method, url, ssl_verify)
        try:
            # fails for gerrit services
            decoded_response = response.json()
        except ValueError:
            decoded_response = self._decode_response(response)
        return decoded_response

    def get_response(self, method, url, ssl_verify):
        """
        Method used to make request.
        Args:
            method (str): the URL to call, can be GET, POST, DELETE, UPDATE...
                          Defaults to GET
            url(str): URL for git based service
            ssl_verify (bool/str): Whether or not to verify SSL certificates,
                                   or a path to a CA file to use.
        Returns:
            Output returned by request module
        """
        response = self.session.request(
            method=method, url=url,
            headers=self.header, verify=ssl_verify)
        response.raise_for_status()
        return response


class BaseReview(object):
    def __init__(self, user=None, title=None, url=None,
                 time=None, updated_time=None, comments=None, image=None,
                 last_comment=None, project_name=None, project_url=None):
        self.user = user
        self.title = title
        self.url = url
        self.time = time
        self.updated_time = updated_time
        self.comments = comments
        self.image = image
        self.last_comment = last_comment
        self.project_name = project_name
        self.project_url = project_url

    @staticmethod
    def format_duration(created_at):
        """
        Formats the duration the review request is pending for
        Args:
            created_at (str): the date review request was filed

        Returns:
            a string of duration the review request is pending for
        """
        """
        find the relative time difference between now and
        review request filed to retrieve relative information
        """
        rel_diff = relativedelta(datetime.datetime.utcnow(),
                                 created_at)

        time_dict = OrderedDict([
            ('year', rel_diff.years),
            ('month', rel_diff.months),
            ('day', rel_diff.days),
            ('hour', rel_diff.hours),
            ('minute', rel_diff.minutes)
        ])

        result = []
        for k, v in time_dict.items():
            # add minutes only if it is the only
            # information available
            if k == 'minute' and result:
                continue
            if v == 1:
                result.append('%s %s' % (v, k))
            elif v > 1:
                result.append('%s %ss' % (v, k))

        if not result:
            return 'less than 1 minute'

        return ' '.join(result)

    @property
    def since(self):
        return self.format_duration(created_at=self.time)

    def format(self, style, i, N, show_last_comment=None):
        """
        Format the result in a given style.
        Args:
            style(str): the name of the style.
            i(int): position in a list.
            N(int): length of the list.
            show_last_comment (int): show last_comment text in output
        Return:
            formatted_string(str): Formatted string as per style
        """
        lookup = {
            'oneline': self._format_oneline(i, N),
            'indented': self._format_indented(i, N, show_last_comment),
            'json': self._format_json(i, N, show_last_comment),
            'irc': self._format_irc(),
        }
        return lookup[style]

    def _format_oneline(self, i, N):
        """
        Format the result in oneline style.
        Args:
            i(int): Not used in this method, added to have same parameters
                    in all the formatting methods
            N(int): Not used in this method, added to have same parameters
                    in all the formatting methods
        Return:
            formatted_string(str): Formatted string as per style
        """

        string = "{} filed '{}' {} {} ago".format(
            self.user, self.title, self.url, self.since
        )

        if self.comments == 1:
            string += ", {} comment".format(self.comments)
        elif self.comments > 1:
            string += ", {} comments".format(self.comments)

        if self.last_comment:
            string += ", last comment by {} {} ago".format(
                self.last_comment.author,
                self.format_duration(self.last_comment.created_at),
            )

        return string

    def _format_indented(self, i, N, show_last_comment):
        """
        Format the result in indented style.
        Args:
            i(int): Not used in this method, added to have same parameters
                    in all the formatting methods
            N(int): Not used in this method, added to have same parameters
                    in all the formatting methods
            show_last_comment (int): show last_comment text in output
        Return:
            formatted_string(str): Formatted string as per style
        """

        string = "{} filed '{}'\n\t{}\n\t{} ago".format(
            self.user, self.title, self.url, self.since
        )

        if self.comments == 1:
            string += "\n\t{} comment".format(self.comments)
        elif self.comments > 1:
            string += "\n\t{} comments".format(self.comments)

        if self.last_comment:
            string += ", last comment by {} {} ago".format(
                self.last_comment.author,
                self.format_duration(self.last_comment.created_at),
            )

        if show_last_comment and self.last_comment:
            # Wrap and indent lines to fit in a terminal, preserving newlines
            lines = self.last_comment.body.split('\n')
            lines = sum([textwrap.wrap(line) for line in lines], [])
            comment = "\n".join(lines)
            comment = textwrap.indent(comment, '\t\t')
            string += "\n{}".format(comment)

        return string

    def _format_json(self, i, N, show_last_comment):
        """
        Format the result in json style.
        Args:
            i(int): position in a list.
            N(int): length of the list.
            show_last_comment (bool): show last_comment text in output
        Return:
            formatted_string(str): Formatted string as per style
        """
        # Include a comma after every entry, except the last.
        suffix = ',' if i < N - 1 else ''
        return json.dumps(self.__json__(show_last_comment), indent=2) + suffix

    def _format_irc(self):
        """
        Format the result for irc output
        Return:
            formatted_string(str): Formatted string as per style
        """

        # \x02 is bold
        # \x0312 is blue color
        string = "\x02{}\x02 filed \x02'{}'\x02 \x0312{}\x03 {} ago".format(
            self.user, self.title, self.url, self.since
        )

        if self.comments == 1:
            string += ", {} comment".format(self.comments)
        elif self.comments > 1:
            string += ", {} comments".format(self.comments)

        if self.last_comment:
            string += ", last comment by \x02{}\x02 {} ago".format(
                self.last_comment.author,
                self.format_duration(self.last_comment.created_at),
            )

        return string

    def __json__(self, show_last_comment):
        data = {
            'user': self.user,
            'title': self.title,
            'url': self.url,
            'relative_time': self.since,
            'time': time.mktime(self.time.timetuple()),
            'updated_time': time.mktime(self.updated_time.timetuple()),
            'comments': self.comments,
            'type': type(self).__name__,
            'image': self.image,
        }
        if self.last_comment:
            data['last_comment'] = {
                'author': self.last_comment.author,
                'created_at':
                    time.mktime(self.last_comment.created_at.timetuple())
                }
            if show_last_comment is not None:
                data['last_comment']['body'] = self.last_comment.body

        return data
