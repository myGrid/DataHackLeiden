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
from copy import deepcopy
from zipfile import ZipFile
import StringIO

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
            print str(workflowId)
            print str(workflow_description_response.status_code)
            raise Exception('Unable to read json of workflow description')
        
        try:
            run = workflow_description['run']
        except KeyError:
            raise Exception('Unable to extract information from workflow description')
        
        return RunTemplate(run)
    
    

    
        

    def runWorkflow(self, workflowId, runName, inputDict):
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
        new_run = self.startWorkflowRun(workflowId, runName, inputDict)
        self.showWorkflowRun(new_run)
        results = self.getResultsOfRun(new_run)
        return results
    

      

    def startWorkflowRun(self, workflowId, runName, inputDict):
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
            

        workflow_description = deepcopy(self.getRunTemplate(workflowId))
        expectedInputs = workflow_description.inputs
        input_list = []
        for inputName in expectedInputs:
            value = expectedInputs[inputName]
            if inputName in inputDict:
                value = inputDict[inputName]
            if value is None:
                raise Exception('No value specified for ' + inputName)
            input_list.append({'name':inputName, 'value': value})
                
        contents = {}
        contents['workflow_id'] = workflowId
        contents['name'] = runName
        if input_list:
            contents['inputs_attributes'] = input_list
        # All values should now be filled in
        new_run_request_data = json.dumps({'run' : contents})

        location = self.__url + '/runs'
        new_run_result = requests.post(location, headers=headers(), auth=self.__auth, data=new_run_request_data)
        if new_run_result.status_code >= 400:
            print new_run_request_data
            raise Exception('Unable to create run ' + str(new_run_result.status_code))
        if new_run_result.headers is None:
            print new_run_request_data
            raise Exception('Unable to locate new run')
        try:
            run_info = new_run_result.json()
            new_run = Run(run_info)
            return new_run
            
        except KeyError:
            raise Exception('Unable to locate new run')
        

        

    def showWorkflowRun(self, run):
        """Displays workflow run in the IPython Notebook cell
        
        Parameters
        ----------
        run_id: integer, Workflow Run Id retrieved in WorkflowRun()
        """
        run_location = self.__url + '/runs/' + str(run.identifier) + '?embedded=true'
        iframe_code = '<iframe src="' + run_location + '" width=1200px height=900px></iframe>'
        h = HTML(iframe_code)
        display_html(h)


        

    def getResultsOfRun(self, run):
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
        run_id = run.identifier
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

        finished_info = latest_run_info.json()
        outputzip_location = finished_info['outputs_zip']
        zip_location = self.__url + outputzip_location
        zip_response = requests.get(zip_location, headers = {'accept':'application/octet-stream'}, auth=self.__auth)
        output_dict = convertZip(zip_response.content)

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

def convertZip(stringZip):
    result = {}
    zipFile = ZipFile(StringIO.StringIO(stringZip))
    zipFileContentsList = zipFile.infolist()
    for member in zipFileContentsList:
        parts = member.filename.split('/')
        currentDict = result
        for p in parts:
            nameParts = p.split('.')
            prefix = nameParts[0]
            if prefix in currentDict:
                currentDict = currentDict[prefix]
            else:
                if len(nameParts) > 1:
                    ## There is a suffix and so it a leaf
                    currentDict[prefix] = zipFile.read(member)
                else:
                    currentDict[prefix] = {}
                    currentDict = currentDict[prefix]
    
    for portName in result:
        value = result[portName]
        if isinstance(value, dict):
            result[portName] = convertDictToList(value)
    return result

def convertDictToList(d):
    size = 0
    for i in d:
        try:
            int_i = int(i)
            size = max(size, int_i)
        except:
            pass
    result = [None] * size
    
    for i in d:
        try:
            int_i = int(i) - 1
            v = d[i]
            if isinstance(v, dict):
                result[int_i] = convertDictToList(v)
            else:
                result[int_i] = v
        except:
            pass
    return result

    
