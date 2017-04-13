from collections import OrderedDict


class BaseService(object):

    def format_duration(self, rel_diff):
        """
        Formats the duration the review request is pending for
        Args:
            rel_diff (relativedelta): duration the review request is pending
                                      for

        Returns:
            a string of duration the review request is pending for
        """
        time_dict = OrderedDict([
            ('year', rel_diff.years),
            ('month', rel_diff.months),
            ('day', rel_diff.days),
            ('hour', rel_diff.hours),
            ('minute', rel_diff.minutes),
        ])

        result = []
        for k, v in time_dict.items():
            if v == 1:
                result.append('%s %s' % (v, k))
            elif v > 1:
                result.append('%s %ss' % (v, k))

        return ' '.join(result)

    def check_request_state(self, abs_diff, rel_diff, state_, value, duration):
        """
        Checks if the review request is older or newer than specified
        time interval.
        Args:
            abs_diff (relativedelta): absolute time difference between now and
                                      review request filed

            rel_diff (str): relative time difference between now and
                            review request filed

            state_ (str): state for pull requests, e.g, older
                        or newer
            value (int): The value in terms of duration for requests
                      to be older or newer than
            duration (str): The duration in terms of period(year, month,
                         hour, minute) for requests to be older or newer than

        Returns:
            True if the review request is older or newer than
            specified time interval, False otherwise
        """
        if duration == 'y':
            if state_ == 'older' and rel_diff.years < value:
                return False
            elif state_ == 'newer' and rel_diff.years > value:
                return False
        if duration == 'm':
            # find the absolute time difference in months
            abs_month = (rel_diff.years*12) + rel_diff.months
            if state_ == 'older' and abs_month < value:
                return False
            elif state_ == 'newer' and abs_month > value:
                return False
        if duration == 'd':
            if state_ == 'older' and abs_diff.days < value:
                return False
            elif state_ == 'newer' and abs_diff.days > value:
                return False
        if duration == 'h':
            # find the absolute time difference in hours
            abs_hour = abs_diff.total_seconds()/3600
            if state_ == 'older' and abs_hour < value:
                return False
            elif state_ == 'newer' and abs_hour > value:
                return False
        if duration == 'min':
            # find the absolute time difference in minutes
            abs_min = abs_diff.total_seconds()/60
            if state_ == 'older' and abs_min < value:
                return False
            elif state_ == 'newer' and abs_min > value:
                return False
        return True


class BaseReviewRot(object):
    def __init__(self, user=None, title=None, url=None,
                 time=None, comments=None):
        self.user = user
        self.title = title
        self.url = url
        self.time = time
        self.comments = comments

    def __str__(self):
        return ("@%s filed '%s' %s since %s%s" % (self.user, self.title,
                                                  self.url, self.time,
                                                  self.comments))
