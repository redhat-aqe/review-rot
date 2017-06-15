from datetime import datetime
import logging
import requests
import json
from reviewrot.basereview import BaseService, BaseReview

log = logging.getLogger(__name__)

class GerritService(BaseService):
    """
        This class represents Gerrit. The reference can be found here:
        https://gerrit-review.googlesource.com/Documentation/rest-api.html
    """
    def __init__(self):
        self.session = requests.session()
        self.header = None

    def request_reviews(self,host,repo_name, state_=None,user_name=None,token=None,
                        value=None, duration=None,ssl_verify=True):
        self.url = host;

        if repo_name is not None:
            request_url = "{}/changes/?q=project:{}+status:open&o=DETAILED_ACCOUNTS".format(self.url,repo_name)
            log.debug('Looking for change requests for %s -> %s', self.url, repo_name) 
            review_response = self._call_api(url=request_url, ssl_verify=ssl_verify)
            return self.format_response(review_response,state_,value,duration)

    def get_comments_count(self,change_id):
        request_url = "{}/changes/{}/comments".format(self.url,str(change_id))
        decoded_response = self._call_api(request_url)
        total_comments = 0
        for response in decoded_response:
            if response is not '/COMMIT_MSG':
                total_comments = total_comments + len(decoded_response.get(response))            
   
        return total_comments
                 
    def format_response(self, decoded_responses,state_,value,duration):
        res_ = []
        for decoded_response in decoded_responses:
            created_date = datetime.strptime(decoded_response['created'][:-3] , "%Y-%m-%d %H:%M:%S.%f")
            result = self.check_request_state(created_date, state_, value, duration)
            if result is False:
                log.debug("Change request '%s' is not %s than specified time interval", decoded_response['subject'], state_)
                continue
            owner = decoded_response['owner']
            res = GerritReview(user=owner.get('username', owner.get('email')),
                               title=decoded_response['subject'],
                               url=self.url + '/' + str(decoded_response['_number']),
                               time= created_date,
                               comments=self.get_comments_count(decoded_response['id']))
            res_.append(res)
        return res_

class GerritReview(BaseReview):
    pass