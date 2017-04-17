from base import BaseService, BaseReviewRot

class GerritService(BaseService):
    def __init__(self):
        NotImplementedError("Yooo")
    
    def request_reviews(self, fltr, value, user_name, repo_name=None):
        NotImplementedError("Yooo")
    
    def get_reviews(self, uname, repo_name, fltr, value):
        NotImplementedError("Yooo")
        
class GerritReviewRot(BaseReviewRot):
    def __init__(self, *args, **kwargs):
        super(GerritReviewRot, self).__init__(*args, **kwargs)
        
    def __str__(self):
         return "@%s filed '%s' %s since%s%s%s" % (self.user, self.title, self.url, self.time, self.comments)

