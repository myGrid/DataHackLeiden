# TavernaPlayerClient.py

import requests
import json

class TavernaPlayerClient(object):
    
    def __init__(self, url):
        self.__url = url
        self.__auth = None
    
    def __init__(self, url, username, password) :
        self.__url = url
        self.__auth = (username, password)
        
    def get_workflow_description(self, workflowId):
        location = self.__url + '/runs/new?workflow_id=' + str(workflowId)
        workflow_description = requests.get(location, headers=headers(), auth=self.__auth)
        return workflow_description.json()
    
    
def json_mime():
    return 'application/json'

def headers():
    return {'content-type':json_mime(), 'accept':json_mime()}


