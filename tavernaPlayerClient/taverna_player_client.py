 # tavernaplayerclient.py
 #  Taverna Player Client for running Taverna Workflows from IPython Notebook.
 #-----------------------------------------------------------------------------
 #  Copyright (c) 2014, Alan R. Wiliams myGrid Team, <support@mygrid.org.uk>

import requests
import json
import time
import sys
import urllib2

from IPython.display import HTML, display_html
from copy import deepcopy
from zipfile import ZipFile
import StringIO

__all__ = ['Client', 'Workflow', 'Run', 'RunTemplate']

class Client(object):
    """
    Main class for the Taverna Player Client 
    """
    
    WORKFLOWS_LOCATION = '%s/workflows'
    RUN_TEMPLATE_LOCATION = '%s/runs/new?workflow_id=%d'
    RUNS_LOCATION = '%s/runs'
    RUN_LOCATION = '%s/runs/%d'
    
    JSON_MIME = 'application/json'
    HEADERS = {'content-type':JSON_MIME, 'accept':JSON_MIME}

    
    def __init__(self, url, username, password) :
        """
        Parameters
        ----------
        url : URL, Taverna Player Portal URL
        username: string, username for the Taverna Player portal
        password: string, password for the Taverna Player portal  
    
        Returns
        -------
        Client object
        
        Raises
        ------
        Exception('url, username and password must be specified')
        Exception('username must be a string')
        Exception('password must be a string')
        """
        
        if None in [url, username, password]:
            raise Exception('url, username and password must be specified')
        
        check_url(url)
        self.__url = url

        if not isinstance(username, basestring):
            raise Exception('username must be a string')
        
        if not isinstance(password, basestring):
            raise Exception('password must be a string')
        
        self.__auth = (username, password)
        self.__workflows_cache = None
        self.__run_template_cache = {}
    
    def get_workflows(self):
        """Returns a list of workflows available on Taverna Player sorted by their identifier 
        
        Raises
        ------   
        Exception('Unable to retrieve workflow descriptions')
        """
        
        if self.__workflows_cache is None:
            current_keys = []
            self.__workflows_cache = {}
        else:
            current_keys = list(self.__workflows_cache.keys())
        
        location = Client.WORKFLOWS_LOCATION % self.__url
        workflow_descriptions_response = requests.get(location, headers=Client.HEADERS, auth=self.__auth)
        if workflow_descriptions_response.status_code >= 400:
            raise Exception('Unable to retrieve workflow descriptions')
        workflow_descriptions = workflow_descriptions_response.json()
        result = []
        for wd in workflow_descriptions:
            if wd['id'] in current_keys:
                current_keys.remove(wd['id'])
            else:
                new_workflow = Workflow(self, wd['id'], wd['category'], wd['description'], wd['title'])
                self.__workflows_cache[wd['id']] = new_workflow
        
        # current_keys will now contain keys that have been removed from the player
        for k in current_keys:
            del self.__workflows_cache[k]
        
        
        return sorted(self.__workflows_cache.values(), key=lambda k: k.identifier)
    
    workflows = property(get_workflows)
        
    def get_run_template(self, workflowId):
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
        Exception('Unable to extract information from workflow description')
        """   
        if workflowId is None:
            raise Exception('workflowId must be specified')
        
        if not isinstance(workflowId, int):
            raise Exception('workflowId must be an integer')
        
        if workflowId not in self.__run_template_cache:
        
            location = Client.RUN_TEMPLATE_LOCATION % (self.__url, workflowId)
            workflow_description_response = requests.get(location, headers=Client.HEADERS, auth=self.__auth)
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
            
            result = RunTemplate(run)
            self.__run_template_cache[workflowId] = result
        
        return self.__run_template_cache[workflowId]
    
    def get_workflow(self, workflowId):
        """Return the Workflow with the specified identifier
        
        Parameters
        ----------
        workflowId: integer, Workflow ID of the workflows available on the Taverna Player Portal
        
        Returns
        -------
        Returns the matching Workflow object
        
        """
        self.get_workflows()
        return self.__workflows_cache[workflowId]
    
    
    def run_workflow(self, workflowId, runName, inputDict):
        """Runs the specified workflow
        Parameters
        ----------
        workflowId: integer, Workflow ID of the workflows available on the Taverna Player Portal
        runName: string, name of the new run
        inputDict: dictionary object, input values provided by the user
        
        Returns
        -------
        The run
        
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
        new_run = self.start_workflow_run(workflowId, runName, inputDict)
        self.show_workflow_run(new_run)
        new_run.get_outputs()
        return new_run
    
    def start_workflow_run(self, workflowId, runName, inputDict):
        """Starts a new instance of a Workflow Run 
        
        Parameters
        ----------
        workflowId: integer, Workflow ID of the workflows available on the Taverna Player Portal
        runName: string, name of the new run
        inputDict: dictionary object, input values provided by the user
        
        Returns
        -------
        The started Run
        
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
            
        workflow_description = deepcopy(self.get_run_template(workflowId))
        expectedInputs = workflow_description.inputs
        input_list = []
        for inputName in expectedInputs:
            value = expectedInputs[inputName]
            if inputName in inputDict:
                value = inputDict[inputName]
            else:
                if value is not None:
                    inputDict[inputName] = value
            if value is None:
                raise Exception('No value specified for ' + inputName)
            input_list.append({'name':inputName, 'value': value})
                
        contents = {}
        contents['workflow_id'] = workflowId
        contents['name'] = runName
        contents['embedded'] = 'true'
        if input_list:
            contents['inputs_attributes'] = input_list
        # All values should now be filled in
        new_run_request_data = json.dumps({'run' : contents})
        location = Client.RUNS_LOCATION % self.__url
        new_run_result = requests.post(location, headers=Client.HEADERS, auth=self.__auth, data=new_run_request_data)
        if new_run_result.status_code >= 400:
            print new_run_request_data
            raise Exception('Unable to create run ' + str(new_run_result.status_code))
        if new_run_result.headers is None:
            print new_run_request_data
            raise Exception('Unable to locate new run')
        try:
            run_info = new_run_result.json()
            new_run = Run(self, run_info['id'], inputDict)
            return new_run
            
        except KeyError:
            raise Exception('Unable to local new run')
        
    def show_workflow_run(self, run):
        """Displays workflow run in the IPython Notebook cell
        
        Parameters
        ----------
        run: Run, Run object to be shown
        """
        run_location = Client.RUN_LOCATION % (self.__url, run.identifier) + '?embedded=true'
        iframe_code = '<iframe src="' + run_location + '" width=1200px height=900px></iframe>'
        h = HTML(iframe_code)
        display_html(h)

    def get_results_of_run(self, run):
        """Waits for the workflow to finish running and retrieves the results
        
        Parameters
        ----------
        run: Run, Run of which to retrieve the results
        
        Returns
        -------
        The Run with outputs etc. determined
        
        Raises
        ------
        Exception('Error reading run information')
        Exception('Run was cancelled')
        Exception('Error reading outputs')
        Exception('Error reading log')
        """
        run_id = run.identifier
        while True:
            latest_run_info = requests.get(Client.RUN_LOCATION % (self.__url, run.identifier), headers=Client.HEADERS, auth=self.__auth)
            if latest_run_info.status_code >= 400:
                raise Exception('Error reading run information')
            latest_run = latest_run_info.json()
            if latest_run['state'] == 'finished':
                break
            elif latest_run['state'] == 'cancelled':
                raise Exception('run was cancelled')
            time.sleep(5)

        finished_info = latest_run_info.json()
        if finished_info['state'] == 'finished':
            run.start_time = finished_info['start_time']
            run.finish_time = finished_info['finish_time']
            
            outputzip_location = finished_info['outputs_zip']
            zip_location = self.__url + outputzip_location
            zip_response = requests.get(zip_location, headers = {'accept':'application/octet-stream'}, auth=self.__auth)
            if zip_response.status_code >= 400:
                raise Exception('Error reading outputs')
            output_dict = convert_zip(zip_response.content)
            run._set_outputs(output_dict)
            log_location = self.__url + finished_info['log']
            log_response = requests.get(log_location, headers = {'accept':'application/octet-stream'}, auth=self.__auth)
            if log_response.status_code >= 400:
                raise Exception('Error reading log')
            run.log = log_response.text
        else:
            run.outputs = None

class Workflow(object):
    """
    A representation of a Taverna 2 workflow known to the Taverna Player
    """
    
    def __init__(self, client, identifier, category, description, title):
        """
        Parameters
        ----------
        client : The Client that knows the Workflow
        identifier: identifier of the Workflow for the Client
        category: category of the Workflow according to the Taverna Player
        description: description of the Workflow
        title: title of the Workflow
        
        Raises
        ------
        Exception('identifier and category must be specified')
 
        Return
        ------
        The Workflow object
        
        """
        
        if None in [identifier, category]:
            raise Exception('identifier and category must be specified')
        self.__run_template = None
        self.__client = client
        self.identifier = identifier
        self.category = category
        self.description = description
        self.title = title
        
    def get_run_template(self):
        """
        
        Return
        ------
        The RunTemplate for the Workflow
        """
        if self.__run_template is None:
            self.__run_template = self.__client.get_run_template(self.identifier)
        return self.__run_template
    
    run_template = property(get_run_template)

    def run(self, runName, inputDict):
        """Runs the Workflow
        Parameters
        ----------
        runName: string, name of the new run
        inputDict: dictionary object, input values provided by the user
        
        Returns
        -------
        The run
        """
        return self.__client.run_workflow(self.identifier, runName, inputDict)

class RunTemplate(object):
    """
    The information required to run a Workflow
    
    """
    
    def __init__(self, d):
        """
        Parameters
        ----------
        d : dictionary object, input ports that must be specified, possibly along with default value
        
        Return
        ------
        The RunTemplate object
        """
        self.inputs = {}
        try:
            inputs_attributes = d['inputs_attributes']
            for a in inputs_attributes:
                name = a['name']
                if 'value' in a:
                    value = a['value']
                else:
                    value = None
                self.inputs[name] = value
        except KeyError:
            pass

class Run(object):
    """
    The information required to run a Workflow
    
    """    
    def __init__(self, client, id, inputs):
        """
        Parameters
        ----------
        id : string, the identifier of the Run
        inputs: dictionary object mapping port names to input values
        
        Return
        ------
        The RunTemplate object
        """
        self.identifier = id
        self.inputs = inputs
        self.__outputs = None
        self.__client = client
    
    def get_outputs(self):
        if self.__outputs is None:
            self.__client.get_results_of_run(self)
        return self.__outputs
    
    def _set_outputs(self, results):
        self.__outputs = results
    
    
    outputs = property(get_outputs)

def check_url(url):
    """
    Attempt to contact the specified URL
    
    Parameters
    ----------
    url: string, the URL to contact
    
    Raises
    ------
    Exception('Unable to contact ' + url')
    """
    try:
       f = urllib2.urlopen(urllib2.Request(url))
       deadLinkFound = False
    except:
        raise Exception('Unable to contact ' + url)

def convert_zip(stringZip):
    """Convert a string representation of a zip file to a dictionary
    
    Parameters
    ----------
    stringZip: string, the string representation of a zip file
    
    Return
    ------
    The dictionary of top-level names to singletons or n-depth lists
    """
    
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
            result[portName] = convert_dict_to_list(value)
    return result

def convert_dict_to_list(d):
    """Convert a multi-level dictionary to a dictionary of names to singletons or n-level lists
    
    Parameters
    ----------
    d: dictionary object, the multi-level dictionary to convert
    
    Return
    ------
    The dictionary of names to singletons or n-level lists
    """
    
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
                result[int_i] = convert_dict_to_list(v)
            else:
                result[int_i] = v
        except:
            pass
    return result

