# Workflow.py

class Workflow(object):
    
    def __init__(self, client, identifier, category, description, title):
        if None in [identifier, category]:
            raise Exception('identifier and category must be specified')
        self.__run_template = None
        self.__client = client
        self.identifier = identifier
        self.category = category
        self.description = description
        self.title = title
        
    def getRunTemplate(self):
        if self.__run_template is None:
            self.__run_template = self.__client.getRunTemplate(self.identifier)
        return self.__run_template

    def run(self, runName, inputDict):
        return self.__client.runWorkflow(self.identifier, runName, inputDict)