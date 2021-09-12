class User:
    interests = []
    sources = []
    tele_handle = ""



    def __init__(self, handle, interest = [], source= []):
        self.interests = interest
        self.sources = source
        self.tele_handle = handle



    def set_sources(self, sources):
        self.sources = sources
    


    def set_interests(self, interests):
        self.interest = interests
    


    def get_dict (self):
        return {
            "sources" : self.sources,
            "interests": self.interests,
            "tele_handle": self.tele_handle
        }

    

    def get_interest (self):
        return self.interests
    


    def get_sources (self):
        return self.sources



    @staticmethod
    def from_dict(self, user):
        return User(user['tele_handle'], user['interests'], user['sources']) 