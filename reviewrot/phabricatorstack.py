import logging
from phabricator import Phabricator
import datetime
import re
from reviewrot.basereview import BaseService, BaseReview, LastComment
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

log = logging.getLogger(__name__)


class PhabricatorService(BaseService):
    """
        This class represents Phabricator Service for Review Rot.
    """
    def request_reviews(self, host, token, user_names=None, age=None, show_last_comment=None,
                        **kwargs):
        """
        Returns revision requests for specified username and repo name.
        If user_names are not provided then requests pulls all open
        revisions
        Args:
            host (str): The host Phabricator server url
            token (str): Phabricator token for authentication
                            (Looks like 'api-1234567890x')
            user_names (lst(str)): Phabricator user names we want to query
            age (Age): Contains the filter state for pull requests,
                       e.g, older or newer and date
            show_last_comment (int): Show text of last comment and
                                     filter out pull requests in which
                                     last comments are newer than
                                     specified number of days
        Returns:
            response (list): Returns list of list of pull requests for
                             specified username and reponame or all reponame
                             for given username
        Note:
            We will use the list 'raw_response' to keep track of the
            raw queries we make to phabricator. We do this to keep
            API calls minimal, and first search through raw_response
            before making another API call.
        """
        # Create Phabricator object with token
        phab = Phabricator(host=urljoin(host, "/api/"), token=token)
        phab.update_interfaces()
        # Create response list
        response = []
        # Create raw response list to keep track of users we've come across
        raw_response = []
        if user_names:
            # Find open reviews for all users (aka the list user_names)

            # Generate a list of user phids based on their username
            # Also begin keeping track of queried users in raw_response
            user_phids, raw_response = self.generate_phids(user_names, phab)

            # Query phabricator based on all users passed
            reviews = self.differential_query(status='status-open',
                                              responsibleUsers=user_phids,
                                              phab=phab)
        else:
            # Find all open reviews
            reviews = self.differential_query(status='status-open',
                                              responsibleUsers=[], phab=phab)

        # Format and go through all reviews for a user
        res = self.get_reviews(phab=phab, reviews=reviews,
                               raw_response=raw_response,
                               host=host,
                               age=age,
                               show_last_comment=show_last_comment)
        # extend in case of non-empty results
        # If we've come across a revision that's dated < duration
        # (i.e. too far in the past) we would have skipped it and
        # returned nothing
        if res:
            response.extend(res)

        return response

    def get_reviews(self, phab, reviews, raw_response,
                    host, age=None, show_last_comment=None):
        """
        Fetches pull requests for specified username and repo name.
        Formats the pull requests details and print it on console.
        Args:
                phab (object): This is the Phabricator object to make API calls
                reviews (dict): The list of open reviews that we are looking at
                raw_response (lst(dict)): The raw data in the query, to use be used
                                          later to minimize API calls
                host (str): The host Phabricator server url
                age (Age): Contains the filter state for pull requests,
                           e.g, older or newer and date
                show_last_comment (int): Show text of last comment and
                                             filter out pull requests in which
                                             last comments are newer than
                                             specified number of days
        Returns:
                response (list): Returns list of pull requests for specified
                                 username and repo name
        """

        response = []
        for review in reviews:
            # Check if there is a last comment
            comments = self.get_comments(id=review['id'], phab=phab)
            last_comment = self.get_last_comment(comments=comments, phab=phab,
                                                 raw_response=raw_response)

            # Get and convert the date created and last modified to datetime

            date_created = self.time_from_epoch(review['dateCreated'])
            date_modified = self.time_from_epoch(review['dateModified'])

            result = self.check_request_state(date_created, age)

            # Check if review should be looked at
            if result is False:
                # Skip the current review
                log.debug("review request '%s' is not %s than specified"
                          " time interval", review['title'], age.state)
                continue

            if last_comment and show_last_comment:
                # If our reviews last comment is newer than show_last_comment, skip
                if self.has_new_comments(last_comment.created_at,
                                         show_last_comment):
                    log.debug("Pull request '%s' had "
                              "new comments in last %s days",
                              review['title'], show_last_comment)
                    continue
            # Query the author to get relevant information and
            # update raw_response if needed
            author_data, raw_response = self.author_data(
                review['authorPHID'],
                raw_response,
                phab)

            # Remove any fluff if the URL has it (i.e. www.google.com/api
            # to www.google.com)
            match = re.search(r'(.*)\/api', host)
            host_cleaned = match.groups()[0] if match else host

            # As the Phabricator does not work with project as much
            # it was better to keep all project names as 'Phabricator'
            # and link them back to the host URL.
            res = PhabricatorReview(user=author_data['userName'],
                                    title=review['title'],
                                    url=review['uri'],
                                    time=date_created,
                                    updated_time=date_modified,
                                    comments=len(comments),
                                    image=author_data['image'],
                                    last_comment=last_comment,
                                    project_name="Phabricator",
                                    project_url=host_cleaned)
            log.debug(res)
            response.append(res)
        return response

    def generate_phids(self, user_names, phab):
        """
        Helper function to generate the phids from the usernames passed into
        the config file
        Args:
                user_names (lst(str)): The list of usernames
                phab (object): This is the Phabricator object to make API calls
        Returns:
                list_of_phids (lst): A list of all phids associated with the users
                raw_response (lst(dict)): The raw data in the query, to use be used
                                          later to minimize API calls
        """
        list_of_phids = []
        raw_response = []
        query = (self.user_query_usernames(user_names, phab))
        for user in query:
            raw_response.append(user)
            list_of_phids.append(user['phid'])
        return list_of_phids, raw_response

    def get_comments(self, id, phab):
        """
        Helper function to make API call to get all comments for a revision
        Args:
                id (str): The ID number for rhe revision
                phab (object): This is the Phabricator object to make API calls
                                (>=0.7.0)

        Returns:
                list_of_all_comments (lst): Returns an list representation of all comments
        """
        # Make API call to get a timeline of review (all events)
        timeline = phab.differential.getrevisioncomments(ids=[int(id)])[id]
        # Create a list to return
        list_of_all_comments = []
        for event in timeline:
            if (event['action'] == 'comment'):
                list_of_all_comments.append(event)
        return list_of_all_comments

    def get_last_comment(self, comments, phab, raw_response):
        """
        Helper function to get the last comment from a list of comments
        Args:
                comments (lst(str)): An list of comments
                                        associated with a revision
                phab (object): This is the Phabricator object to make API calls
                                (>=0.7.0)
                raw_response (lst(dict)): The raw response received from
                                            individual user.query calls.
                                            Keep updating and passing this
                                            list as we call user.query
        Returns:
                LastComment (object): Returns the LastComment object
                                      that can be used in ReviewRot
        """
        if len(comments) > 0:
            # Get the username for the last comment
            author, raw_response = self.author_data(author_phid=comments[0]['authorPHID'],
                                                   phab=phab,
                                                   raw_response=raw_response)
            # Convert the timestamp to datetime
            createdAt = self.time_from_epoch(comments[0]['dateCreated'])

            # Return the last comment
            return LastComment(author=author['userName'],
                               body=comments[0]['content'],
                               created_at=createdAt)

    def author_data(self, author_phid, raw_response, phab):
        """
        Helper function to look up data related to authors (i.e. for last
        comment or individual review). Keeps updating users seen in
        raw_response
        Args:
                author_phid (str): The phid for the author queried
                raw_response (lst(dict)): The raw response received from
                                            individual user.query calls.
                                            Keep updating and passing this
                                            list as we call user.query
                phab (object): This is the Phabricator object to make API calls
                                (>=0.7.0)
        Returns:
                new_user/user (dict): The user that was queried
                raw_response (lst(dict)): The updated (or same) list
                                          that holds all the users
                                          we've seen
        """
        for user in raw_response:
            if user['phid'] == author_phid:
                return user, raw_response

        new_user = self.user_query_ids([author_phid], phab)[0]
        raw_response.append(new_user)
        return new_user, raw_response

    def user_query_usernames(self, usernames, phab):
        """
        Helper function to query users based on usernames
        Args:
                usernames (lst(str)): The list of users to query for
                phab (object): This is the Phabricator object to make API calls
                               (>=0.7.0)

        Returns:
                return (dict): Returns the JSON response to phab.user.query(...)
        Note:
            This is a frozen method (i.e. will eventually
            depreciate). The updated method (user.search)
            does not return the users avatar URL (needed
            for PhabricatorReview)
        """
        return phab.user.query(usernames=usernames)

    def user_query_ids(self, phids, phab):
        """
        Helper function to query users based on phids
        Args:
                phids (lst(str)): The list of phids to query for
                phab (object): This is the Phabricator object to make API calls
                               (>=0.7.0)

        Returns:
                return (dict): Returns the JSON response to phab.user.query(...)
        Note:
            This is a frozen method (i.e. will eventually
            depreciate). The updated method (user.search)
            does not return the users avatar URL (needed
            for PhabricatorReview)
        """
        return phab.user.query(phids=phids)

    def differential_query(self, status, responsibleUsers, phab):
        """
        Helper function to query differentials
        Args:
                status (str): The list of open reviews
                                that we are looking at
                responsibleUsers (lst(str)): The filter(state)
                                             for pull requests,
                                             e.g, older or newer
                phab (object): This is the Phabricator
                               object to make API calls
                                (>=0.7.0)

        Returns:
                return (dict): Returns the JSON response
                             to phab.differential.query(...)
        Note:
            This is a frozen method (i.e. will eventually
            depreciate). The updated method
            (differential.revision.search) does not
            support filtering based on status
            (see trello note below)
            https://trello.com/c/yDQZramE/504-do-not-use-phabricator-deprecated-methods
        """
        return phab.differential.query(status=status,
                                       responsibleUsers=responsibleUsers)
    def time_from_epoch(self, epoch):
        """
        Helper function to convert epoch time to datetime object
        Args:
                epoch (int): epoch time

        Returns:
                return (datetime.datetime): Returns datetime object representing
                                            the epoch time.
        """
        return datetime.datetime.fromtimestamp(
                float(epoch))

class PhabricatorReview(BaseReview):
    pass
