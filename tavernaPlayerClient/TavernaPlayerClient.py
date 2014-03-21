# TavernaPlayerClient.py
#  Taverna Player Client for running Taverna Workflows from IPython Notebook.
#-----------------------------------------------------------------------------
#  Copyright (c) 2014, Alan R. Wiliams myGrid Team, <support@mygrid.org.uk>

import requests
import json
import time
import sys
import urllib2
import Workflow

from IPython.display import HTML, display_html

class TavernaPlayerClient(object):
    """
    Main class for the Taverna Player Client 
    """
    
    def __init__(self, url, username, password) :
        """
        Parameters
        ----------
        url : URL, Taverna Player Portal URL
        username: string, username for the Taverna Player portal
        password: string, password for the Taverna Player portal  
    
        Returns
        -------
        TavernaPlayerClient object
        
        Raises
        ------
        Exception('url, username and password must be specified')
        Exception('username must be a string')
        Exception('password must be a string')
        """
        if None in [url, username, password]:
            raise Exception('url, username and password must be specified')
        
        TavernaPlayerClient.check_url(url)
        self.__url = url

        if not isinstance(username, basestring):
            raise Exception('username must be a string')
        
        if not isinstance(password, basestring):
            raise Exception('password must be a string')
        
        self.__auth = (username, password)
    
    def getWorkflows(self):
        """Returns a list of workflows available on Taverna Player sorted by their identifier 
        
        Raises
        ------   
        Exception('Unable to retrieve workflow descriptions')
        """       
        location = self.__url + '/workflows'
        workflow_descriptions_response = requests.get(location, headers=headers(), auth=self.__auth)
        if workflow_descriptions_response.status_code >= 400:
            raise Exception('Unable to retrieve workflow descriptions')
        workflow_descriptions = workflow_descriptions_response.json()
        result = []
        for wd in workflow_descriptions:
            result.append(Workflow(self, wd['id'], wd['category'], wd['description'], wd['title']))
        return sorted(result, key=lambda w: w.identifier)
        
    def getRunTemplate(self, workflowId):
        """
        Parameters
        ----------
        workflowId: integer, Workflow ID of the workflows available on the Taverna Player Portal
        
        Returns
        -------
        Returns a RunTemplate object
        
        Raises
        ------
        Exception('workflowId must be specified')
        Exception('workflowId must be an integer')
        Exception('Unable to read json of workflow description')
        """
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
        """Runs the specified workflow
        Parameters
        ----------
        workflowId: integer, Workflow ID of the workflows available on the Taverna Player Portal
        inputDict: dictionary object, input values provided by the user
        
        Returns
        -------
        Results of the run
        
        Raises
        ------
        Exception('workflowId must be specified')
        Exception('workflowId must be an integer')
        """
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
        """Starts a new instance of a Workflow Run 
        
        Parameters
        ----------
        workflowId: integer, Workflow ID of the workflows available on the Taverna Player Portal
        inputDict: dictionary object, input values provided by the user
        
        Returns
        -------
        Workflow ID
        
        Raises
        ------
        Exception('workflowId must be specified')
        Exception('workflowId must be an integer')
        Exception('No value specified for ' + expectedInputName)
        Exception('Unable to create run')
        Exception('Unable to locate new run')
        """
        if workflowId is None:
            raise Exception('workflowId must be specified')
        
        if not isinstance(workflowId, int):
            raise Exception('workflowId must be an integer')
        
        if inputDict is None:
            inputDict = {}
            
        workflow_description = self.getRunTemplate(workflowId)
        expectedInputs = workflow_description.get('inputs_attributes', {})
        for expectedInput in expectedInputs:
            expectedInputName = expectedInput['name']
            # If the user did not specify the input values, the default ones will be used
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
            raise Exception('Unable to locate new run')
        
    def showWorkflowRun(self, run_id):
        """Displays workflow run in the IPython Notebook cell
        
        Parameters
        ----------
        run_id: integer, Workflow Run Id retrieved in WorkflowRun()
        """
        run_location = self.__url + '/runs/' + str(run_id) + '?embedded=true'
        iframe_code = '<iframe src="' + run_location + '" width=1200px height=900px></iframe>'
        h = HTML(iframe_code)
        display_html(h)

    def getResultsOfRun(self, run_id):
        """Waits for the workflow to finish running
        
        Parameters
        ----------
        run_id: integer, Workflow Run Id retrieved in WorkflowRun()
        
        Returns
        -------
        Dictionary with the run results
        
        Raises
        ------
        Exception('Error reading run information')
        Exception('Run was cancelled')
        """
        while True:
            latest_run_info = requests.get(self.__url + '/runs/' + str(run_id), headers=headers(), auth=self.__auth)
            if latest_run_info.status_code >= 400:
                raise Exception('Error reading run information')
            latest_run = latest_run_info.json()
            if latest_run['state'] == 'finished':
                break
            elif latest_run['state'] == 'cancelled':
                raise Exception('Run was cancelled')
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



