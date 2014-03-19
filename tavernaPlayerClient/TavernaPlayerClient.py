# TavernaPlayerClient.py

import requests
import json
import time
import sys
import urllib2

from IPython.display import HTML, display_html

class TavernaPlayerClient(object):
    
    def __init__(self, url, username, password) :
        if None in [url, username, password]:
            raise Exception('url, username and password must be specified')
        
        TavernaPlayerClient.check_url(url)
        self.__url = url

        if not isinstance(username, basestring):
            raise Exception('username must be a string')
        
        if not isinstance(password, basestring):
            raise Exception('password must be a string')
        
        self.__auth = (username, password)
    
    def getWorkflowDescriptions(self):
        location = self.__url + '/workflows'
        workflow_descriptions_response = requests.get(location, headers=headers(), auth=self.__auth)
        if workflow_descriptions_response.status_code >= 400:
            raise Exception('Unable to retrieve workflow descriptions')
        workflow_descriptions = workflow_descriptions_response.json()
        result = []
        for wd in workflow_descriptions:
            result.append(Workflow(wd['id'], wd['category'], wd['description'], wd['title']))
        return result
        
    def getWorkflowDescription(self, workflowId):
        if workflowId is None:
            raise Exception('workflowId must be specified')
        
        if not isinstance(workflowId, int):
            raise Exception('workflowId must be an integer')
        location = self.__url + '/runs/new?workflow_id=' + str(workflowId)
        workflow_description_response = requests.get(location, headers=headers(), auth=self.__auth)
        if workflow_description_response.status_code >= 400:
            raise Exception('Unable to retrieve workflow description for ' + str(workflowId) + ' : ' + str(workflow_description_response.status_code))
        
        try:
            workflow_description = workflow_description_response.json()
        except:
                raise Exception('Unable to read json of workflow description')
        
        try:
            run = workflow_description['run']
        except KeyError:
            raise Exception('Unable to extract information from workflow description')
        
        return run
    
    
    def runWorkflow(self, workflowId, inputDict):
        if workflowId is None:
            raise Exception('workflowId must be specified')
        
        if not isinstance(workflowId, int):
            raise Exception('workflowId must be an integer')
        
        if inputDict is None:
            inputDict = {}
        run_id = self.startWorkflowRun(workflowId, inputDict)
        self.showWorkflowRun(run_id)
        results = self.getResultsOfRun(run_id)
        return results
    
    def startWorkflowRun(self, workflowId, inputDict):
        if workflowId is None:
            raise Exception('workflowId must be specified')
        
        if not isinstance(workflowId, int):
            raise Exception('workflowId must be an integer')
        
        if inputDict is None:
            inputDict = {}
            
        workflow_description = self.getWorkflowDescription(workflowId)
        expectedInputs = workflow_description.get('inputs_attributes', {})
        for expectedInput in expectedInputs:
            expectedInputName = expectedInput['name']
            if inputDict.has_key(expectedInputName):
                expectedInput['value'] = inputDict[expectedInputName]
            else:
                if not expectedInput.has_key('value'):
                    raise Exception('No value specified for ' + expectedInputName)
        # All values should now be filled in
        new_run = {'run' : workflow_description}
        location = self.__url + '/runs'
        new_run_result = requests.post(location, headers=headers(), auth=self.__auth, data=json.dumps(new_run))
        if new_run_result.status_code >= 400:
            raise Exception('Unable to create run')
        if new_run_result.headers is None:
            raise Exception('Unable to locate new run')
        try:
            run_info = new_run_result.json()
            run_id = run_info['id']
            return run_id
            
        except KeyError:
            raise Exception('Unable to local new run')
        
    def showWorkflowRun(self, run_id):
        run_location = self.__url + '/runs/' + str(run_id) + '?embedded=true'
        iframe_code = '<iframe src="' + run_location + '" width=1200px height=900px></iframe>'
        h = HTML(iframe_code)
        display_html(h)

    def getResultsOfRun(self, run_id):
        while True:
            latest_run_info = requests.get(self.__url + '/runs/' + str(run_id), headers=headers(), auth=self.__auth)
            if latest_run_info.status_code >= 400:
                raise Exception('Error reading run information')
            latest_run = latest_run_info.json()
            if latest_run['state'] == 'finished':
                break
            elif latest_run['state'] == 'cancelled':
                raise Exception('run was cancelled')
            time.sleep(5)

        output_dict = {}
        finished_info = latest_run_info.json()
        outputs = finished_info['outputs']
        for o in outputs:
            output_name = o['name']
            output_path = o['path']
            output_mime = o['value_type']
            output_location = self.__url + output_path
            output_get = requests.get(output_location, headers={'accept':output_mime}, auth=self.__auth)
            print output_get.text
            print output_get
            output_dict[output_name] = output_get.text
        return output_dict

    @staticmethod
    def check_url(url):
        try:
            f = urllib2.urlopen(urllib2.Request(url))
            deadLinkFound = False
        except:
            raise Exception('Unable to contact ' + url)

    
def json_mime():
    return 'application/json'

def headers():
    return {'content-type':json_mime(), 'accept':json_mime()}



