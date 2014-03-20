
from nose.tools import *
from TavernaPlayerClient import TavernaPlayerClient
from TavernaPlayerClient import json_mime
from TavernaPlayerClient import headers

url = 'https://dev.at.biovel.eu/'
#url = 'http://cspool00.cs.man.ac.uk:3003'
username = 'player'
password = 'player'

@raises(Exception)
def test_init_constructor():
	# test if an error is raised when no url, username or password is provided
	TavernaPlayerClient(None,None,None)

@raises(Exception)
def test_no_string_user():
	# test if an error is raised when the usernames is not a string
	TavernaPlayerClient('test',1,'test')

@raises(Exception)
def test_no_string_pass():
	# test if an error is raised when the password is not a string
	TavernaPlayerClient('test','test',1)

@raises(Exception)
def test_invalid_url():
	# test if an error is raised when the url is invalid
	TavernaPlayerClient.check_url('aaaaaaaaaaaaaaaaa')

def test_valid_url():
	# test if no error is raised when a valid url is entered
	TavernaPlayerClient.check_url(url)

def test_valid_input():
	# test if all input (url, username and password) is valid
	TavernaPlayerClient(url,username,password)

def test_json_mime():
	# test if the json_mime function returns the correct output
	assert json_mime() == 'application/json'

def test_headers():
	# test if the headers function return the correct output
	assert headers() == {'content-type':'application/json', 'accept':'application/json'}

TPC = TavernaPlayerClient(url,username,password)
Timeout = TavernaPlayerClient(url+'abcdef',username,password)

@raises(Exception)
def test_getWorkflow_timeout():
	# test if a timeout occcurs when there no valid user / pass is provided
	Timeout.getWorkflows()

def test_getWorkflow_list_output():
	# test if the getWorkflow function returns a list
	assert type(TPC.getWorkflows()) is list

@raises(Exception)
def test_runWorkflow_without_workflowID():
	# test if an execution is raised when no id is provided
	TPC.runWorkflow(None,None)

@raises(Exception)
def test_runWorkflow_with_invalid_ID_type():
	# test if an error is raised when no valid id is provided
	TPC.runWorkflow('1',None)

@raises(Exception)
def test_startWorkflowRun_without_workflowid():
	# test if an exception is raised when no workflow id is provided
	TPC.startWorkflowRun(None,None)

@raises(Exception)
def test_startWorkflowRun_with_invalid_id_type():
	# test if an error is raised if the workflow id is not an int
	TPC.startWorkflowRun('1',None)

@raises(Exception)
def test_WorkflowDescription_without_workflowID():
	# test if an error is raised when the workflowID is None
	TPC.getRunTemplate(None)

@raises(Exception)
def test_WorkflowDescription_with_invalid_workflowID_type():
	# test if invalid input type returns an error
	TPC.getRunTemplate('test')

@raises(Exception)
def test_WorkflowDescription_timeout():
	# test if an error is raised when the request timesout
	Timeout.getRunTemplate(99999999)

@raises(Exception)
def test_WorkflowDescription_with_invalid_user_info():
	# test if the server request correctly times out
	TPC.getRunTemplate(1234)

@raises(Exception)
def test_getResultsOfRun_with_invalid_runid():
	# test if an exception is raised when no results can be obtained
	TPC.getResultsOfRun('10')
