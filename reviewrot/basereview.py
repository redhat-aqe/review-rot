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

    def check_request_state(self, abs_diff, rel_diff,
                            state_, value, duration):
        """
        Checks if the review request is older or newer than specified
        time interval.
        Args:
            abs_diff (timedelta): absolute time difference between now and
                                  review request filed (used to retrieve and
                                  calculate absolute information e.g, days,
                                  hours, minutes)
            rel_diff (relativedelta): relative time difference between now and
                                  review request filed (used to retrieve and
                                  calculate absolute information e.g, month,
                                  year)
            state_ (str): state for pull requests, e.g, older
                          or newer
            value (int): The value in terms of duration for requests
                         to be older or newer than
            duration (str): The duration in terms of period(year, month, hour
                            minute) for requests to be older or newer than

        Returns:
            True if the review request is older or newer than
            specified time interval, False otherwise
        """
        if state_ not in ('older', 'newer'):
            raise ValueError('Invalid state value: %s' % state_)
        if duration == 'y':
            """ use rel_diff to retrieve absolute year since
            value of absolute and relative year is same."""
            if state_ == 'older' and rel_diff.years < value:
                return False
            elif state_ == 'newer' and rel_diff.years > value:
                return False
        elif duration == 'm':
            """ use rel_diff to calculate absolute time difference
            in months """
            abs_month = (rel_diff.years*12) + rel_diff.months
            if state_ == 'older' and abs_month < value:
                return False
            elif state_ == 'newer' and abs_month > value:
                return False
        elif duration == 'd':
            """ use abs_diff to retrieve absolute time difference
            in days """
            if state_ == 'older' and abs_diff.days < value:
                return False
            elif state_ == 'newer' and abs_diff.days > value:
                return False
        elif duration == 'h':
            """ use abs_diff to calculate absolute time difference
            in hours """
            abs_hour = abs_diff.total_seconds()/3600
            if state_ == 'older' and abs_hour < value:
                return False
            elif state_ == 'newer' and abs_hour > value:
                return False
        elif duration == 'min':
            """ use abs_diff to calculate absolute time difference
            in minutes """
            abs_min = abs_diff.total_seconds()/60
            if state_ == 'older' and abs_min < value:
                return False
            elif state_ == 'newer' and abs_min > value:
                return False
        else:
            raise ValueError("Invalid duration type: %s" % duration)
        return True


<<<<<<< 5a55812d964174b20c510e4819c4469427259c8d
class BaseReview(object):
=======
class BaseReviewRot(object):
>>>>>>> Added basic structure and script for reviewrot
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
