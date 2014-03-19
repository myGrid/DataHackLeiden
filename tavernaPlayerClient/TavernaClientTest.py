from nose.tools import *
from TavernaPlayerClient import TavernaPlayerClient
from TavernaPlayerClient import json_mime
from TavernaPlayerClient import headers

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
	TavernaPlayerClient.check_url('http://cspool00.cs.man.ac.uk:3003')

def test_valid_input():
	# test if all input (url, username and password) is valid
	TavernaPlayerClient('http://cspool00.cs.man.ac.uk:3003','test','test')

def test_WorkflowDescription_with_valid_workflowID():
	# test if valid input does not return an error
	TPC = TavernaPlayerClient('http://cspool00.cs.man.ac.uk:3003','test','test')
	TPC.getWorkflowDescription('test')

def test_json_mime():
	# test if the json_mime function returns the correct output
	assert json_mime() == 'application/json'

def test_headers():
	# test if the headers function return the correct output
	assert headers() == {'content-type':'application/json', 'accept':'application/json'}

@raises(Exception)
def test_getResultsOfRun_with_invalid_runid():
	# test if an exception is raised when no results can be obtained
        TPC = TavernaPlayerClient('http://cspool00.cs.man.ac.uk:3003','test','test')
	TPC.getResultsOfRun('10')
