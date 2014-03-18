# TavernaPlayerClient.py

import requests
import json
import time
import sys
from IPython.display import HTML

class TavernaPlayerClient(object):
    
    def __init__(self, url):
        self.__url = url
        self.__auth = None
    
    def __init__(self, url, username, password) :
        self.__url = url
        self.__auth = (username, password)
        
    def getWorkflowDescription(self, workflowId):
        location = self.__url + '/runs/new?workflow_id=' + str(workflowId)
        workflow_description = requests.get(location, headers=headers(), auth=self.__auth)
        return workflow_description.json()['run']
    
    def startWorkflowRun(self, workflowId, inputDict):
        workflow_description = self.getWorkflowDescription(workflowId)
        expectedInputs = workflow_description.get('inputs_attributes', {})
        for expectedInput in expectedInputs:
            expectedInputName = expectedInput['name']
            if inputDict.hasKey(expectedInputName):
                expectedInput['value'] = inputDict[expectedInputName]
            else:
                if not expectedInput.hasKey('value'):
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
        return HTML(iframe_code)

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
    
def json_mime():
    return 'application/json'

def headers():
    return {'content-type':json_mime(), 'accept':json_mime()}



