# Workflow.py

class Workflow(object):
    
    def __init__(self, client, identifier, category, description, title):
        if None in [identifier, category]:
            raise Exception('identifier and category must be specified')
        self.__client = client
        self.identifier = identifier
        self.category = category
        self.description = description
        self.title = title
