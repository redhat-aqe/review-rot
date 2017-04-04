from base import BaseService, BaseReviewRot
from libpagure import Pagure
#pg = Pagure()
#print pg.api_version()
#print pg.error_codes()
class PagureService(BaseService):
    def __init__(self):
        NotImplementedError("Yooo")
    
    def request_reviews(self, user_name, fltr, value, repo_name=None):
        NotImplementedError("Yooo")
    
    def get_reviews(self, uname, repo_name, fltr, value):
        NotImplementedError("Yooo")

class PagureReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        super(PagureReviewRot, self).__init__(*args, **kwargs)

    def __str__(self):
         return "@%s filed '%s' %s since%s%s%s" % (self.user, self.title, self.url, self.time, self.comments)

