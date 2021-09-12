import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

user_collection = "users"
project_collection = "projects"

class Firestore:
    _instance = None

    @staticmethod 
    def getInstance():
        if Firestore._instance == None:
            Firestore()
        return Firestore._instance



    def __init__(self):
        if Firestore._instance != None:
            raise Exception("This class is a singleton!")
        else:
            firebase_admin.initialize_app(
                credential={
                    firebase_admin.credentials.Certificate({
                        "type":os.environ["SERVICE_ACCOUNT"],
                        "projectId":  os.environ["PROJECT_ID"],
                        "private_key": os.environ["PRIVATE_KEY"].replace('\\n', '\n'),
                        "client_email": os.environ["CLIENT_EMAIL"],
                        "token_uri":os.environ["TOKEN_URI"]
                    })
            })
            
               
            db = firestore.client()
            Firestore._instance = db
    


    @staticmethod
    def update (collection, document, dict):
        collection = collection.replace("/", "_")
        document = document.replace("/", "_")
        Firestore.getInstance().collection(collection).document(document).set(dict)
        Firestore.getInstance().collection(collection).document(document).update({
                u'timestamp': firestore.SERVER_TIMESTAMP
            })




    @staticmethod
    def create_user (id: str, profile: dict):
        Firestore.getInstance().collection(user_collection).document(id).set(profile)
        Firestore.getInstance().collection(user_collection).document(id).update({
                u'timestamp': firestore.SERVER_TIMESTAMP
            })



    @staticmethod
    def check_user (id: str):
        user_list = [str(x.id) for x in Firestore.getInstance().collection(user_collection).stream()]
        if id in user_list:
            print ("User verified")
            return True
        return False
    


    @staticmethod
    def get_user (id: str):
        return Firestore.getInstance().collection(user_collection).document(id).get().to_dict()
    


    @staticmethod
    def update_user (id: str, profile: dict):
        Firestore.getInstance().collection(user_collection).document(id).set(profile)
        Firestore.getInstance().collection(user_collection).document(id).update({
                u'timestamp': firestore.SERVER_TIMESTAMP
            })



    @staticmethod
    def add_projects (project_name: str, project_info: dict):
        project_name = project_name.replace("/", "_")
        Firestore.getInstance().collection(project_collection).document(project_name).set(project_info)
        Firestore.getInstance().collection(project_collection).document(project_name).update({
                u'timestamp': firestore.SERVER_TIMESTAMP
            })



    @staticmethod
    def get_projects():
        return Firestore.getInstance().collection(project_collection).stream()

    

    @staticmethod
    def update_sent_projects(project_name: str, id: str):
        Firestore.getInstance().collection(project_collection).document(project_name).update({
                u'sent_users': firestore.ArrayUnion([id])})
    


