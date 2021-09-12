class Product:
    category = ""
    date = ""
    description = ""
    pictures = []
    source = ""
    title = ""
    link = ""
    sent_users = []

    def __init__(self, category, source) -> None:
        self.category = category
        self.source = source
        self.pictures = []
        self.sent_users = []

    def get_dict (self) -> dict:
        return {
            "category" : self.category,
            "description" : self.description,
            "pictures" : self.pictures,
            "source" : self.source,
            "title" : str(self.title),
            "link" : self.link,
            "sent_users": self.sent_users
        }
    

    def from_dict (self):
        return Product()
