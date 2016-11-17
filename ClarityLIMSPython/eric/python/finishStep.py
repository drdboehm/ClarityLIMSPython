import sys
import getopt
import glsapiutil
import xml.dom.minidom
import time
import clarityHelpers
import logging
import logging.handlers

from xml.dom.minidom import parseString

LOG_FILENAME = "/tmp/finishStep.log"
HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None
args = None
LOG = None
nextStepURI = ""
SH = None

def setupGlobalsFromURI(uri):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split("/")
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"

	if DEBUG is True:
		print HOSTNAME
		print BASE_URI

def getNextActionURI(cfXML):

	response = ""

	if len(cfXML) > 0:
		DOM = parseString(cfXML)
		nodes = DOM.getElementsByTagName("configuration")
		if len(nodes) > 0:
			cfURI = nodes[0].getAttribute("uri")
			stXML = api.getResourceByURI(cfURI)
			stDOM = parseString(stXML)
			nodes = stDOM.getElementsByTagName("transition")
			if len(nodes) == 1:
				naURI = nodes[0].getAttribute("next-step-uri")
				response = naURI
			if len(nodes) > 1:
				# # there is probably a safer way to do this, but it seems that if we get two possible
				# # transitions, we want the second one
				naURI = nodes[1].getAttribute("next-step-uri")
				response = naURI

	return response

def getNextStepURI(wfURI, thisStageURI):

	nextStageURI = ""

	try:
		wfXML = api.getResourceByURI(wfURI)
		wfDOM = parseString(wfXML)
		stages = wfDOM.getElementsByTagName("stage")
		for i in range(0, len(stages)):
			stageURI = stages[ i ].getAttribute("uri")
			if stageURI == thisStageURI:
				nextStageURI = stages[ i + 1 ].getAttribute("uri")
				break

		if len(nextStageURI) > 0:
			nextStageXML = api.getResourceByURI(nextStageURI)
			nextStageDOM = parseString(nextStageXML)
			nodes = nextStageDOM.getElementsByTagName("step")
			response = nodes[0].getAttribute("uri")
	except:
		response = ""

	return response

def findNextStage(artifactDOM):

	global nextStepURI

	stageURI = ""
	# # get the name of the current step being finished
	pDOM = SH.getProcessDOM()
	nodes = pDOM.getElementsByTagName("type")
	thisProcessName = nodes[0].firstChild.data

	try:

		# # does this artifact have a stage in progress?
		stages = artifactDOM.getElementsByTagName("workflow-stage")
		for s in stages:
			status = s.getAttribute("status")
			if status == "IN_PROGRESS":
				stageURI = s.getAttribute("uri")
				break

		if len(stageURI) > 0:
			stageXML = api.getResourceByURI(stageURI)
			stageDOM = parseString(stageXML)
			nodes = stageDOM.getElementsByTagName("stg:stage")
			stageName = nodes[0].getAttribute("name")
			if stageName == thisProcessName:
				stageURI = nodes[0].getAttribute("uri")
				nodes = stageDOM.getElementsByTagName("workflow")
				wfURI = nodes[0].getAttribute("uri")
				response = getNextStepURI(wfURI, stageURI)

	except:
		response = ""

	return response

def routeAnalytes():

	global nextStepURI

	# # Step 1: Get the XML relating to the actions resource for this step
	aURI = args[ "stepURI" ] + "/actions"
	aXML = api.getResourceByURI(aURI)
	aDOM = parseString(aXML)

	# # Step 2: Get the URI for the next-step, and select an action
	# # if we weren't given a -a flag, use the default next action for this step
	nsURI = ""

	nsURI = getNextActionURI(aXML)
	if DEBUG: print("URI for Next Action is:" + nsURI)
	if len(nsURI) == 0:
		action = "complete"
	else:
		action = "nextstep"
		nextStepURI = nsURI

	if len(nsURI) == 0:
		LOG.info("Checking to see if this step is termination of a protocol ...")
		# # get the first artifact from the /actions resource
		nodes = aDOM.getElementsByTagName("next-action")
		oURI = nodes[0].getAttribute("artifact-uri")
		oXML = api.getResourceByURI(oURI)
		oDOM = parseString(oXML)
		nsURI = findNextStage(oDOM)

	if len(nsURI) > 0:
		LOG.info("Found the next step URI:" + nsURI)
		nextStepURI = nsURI
	else:
		LOG.info("unable to find the next step URI")

	# # Step 3: Hone in on the next-action nodes, as these will be the ones we update
	nodes = aDOM.getElementsByTagName("next-action")
	for node in nodes:
		# # ignore any nodes that already have an action attribute
		if not node.hasAttribute("action"):
			node.setAttribute("action", action)
			if action == "nextstep":
				node.setAttribute("step-uri", nsURI)

	# # Step 4: update the LIMS
	rXML = api.updateObject(aDOM.toxml(), args[ "stepURI" ] + "/actions")
	try:
		rDOM = parseString(rXML)
		nodes = rDOM.getElementsByTagName("next-action")
		if len(nodes) > 0:
			LOG.info("Sample will be routed to " + nsURI)
			return True
		else:
			LOG.info("An error occurred while trying to set Next Actions to default value:" + rXML)
			return False
	except:
		LOG.info("An error occurred while trying to set Next Actions to default value:" + rXML)
		return False

def advanceStep():

	sURI = args[ "stepURI" ]
	sXML = api.getResourceByURI(sURI)
	sDOM = parseString(sXML)
	nodes = sDOM.getElementsByTagName("stp:step")
	oldState = nodes[0].getAttribute("current-state")

	LOG.info("Trying to advance step ...")
	aURI = sURI + "/advance"
	rXML = api.createObject(sXML, aURI)

	try:
		rDOM = parseString(rXML)
		LOG.debug("response was:")
		LOG.debug(rXML)
		nodes = rDOM.getElementsByTagName("message")
		if len(nodes) > 0:
			if nodes[0].firstChild.data.find("external program queued") > -1:
				# # if we reach here, there is an external program running, and we need to let it finish
				programComplete = False
				count = 0
				while programComplete is False:
					time.sleep(5)
					LOG.info("Waiting for automation script to complete")
					count += 1
					# # check the progress state again now
					rXML = api.getResourceByURI(sURI)
					rDOM = parseString(rXML)
					nodes = rDOM.getElementsByTagName("stp:step")
					currentState = nodes[0].getAttribute("current-state")
					if not currentState == oldState:
						programComplete = True
					# # let's not be stuck here forever
					if count > 20: 
						programComplete = True
	except:
		LOG.info("Unable to parse rXML! - Is it valid XML:")
		LOG.info(rXML)
		return False

	nodes = rDOM.getElementsByTagName("stp:step")
	state = nodes[0].getAttribute("current-state")
	if state == oldState:
		LOG.debug("oldstate == current state")
		return False
	else:
		LOG.info("Step was advanced")
		return True

def getPlacedArtifacts():

	plURI = args[ "stepURI" ] + "/placements"
	plXML = api.getResourceByURI(plURI)
	plDOM = parseString(plXML)
	nodes = plDOM.getElementsByTagName("output-placement")
	aURIs = []
	for node in nodes:
		aURI = node.getAttribute("uri")
		if aURI not in aURIs:
			aURIs.append(aURI)

	return aURIs

def getProcessOutputs():

	sURI = args[ "stepURI" ] + "/details"
	sXML = api.getResourceByURI(sURI)
	sDOM = parseString(sXML)

	nodes = sDOM.getElementsByTagName("output")
	aURIs = []
	for node in nodes:
		if node.getAttribute("type") == "Analyte":
			aURI = node.getAttribute("uri")
			if aURI not in aURIs:
				aURIs.append(aURI)

	return aURIs

def getCurrentUser():

	try:
		thisURI = args[ "stepURI" ].replace("steps", "processes")
		thisXML = api.getResourceByURI(thisURI)
		thisDOM = parseString(thisXML)

		nodes = thisDOM.getElementsByTagName("technician")
		rURI = nodes[0].getAttribute("uri")
		response = rURI
	except:
		response = ""

	return response

def startNextStep(artifactURIs, rURI):

	LINES = []

	# # determine the allowed container type for the next process
	stepXML = api.getResourceByURI(nextStepURI)
	stepDOM = parseString(stepXML)
	try:
		nodes = stepDOM.getElementsByTagName("permitted-containers")
		cnodes = nodes[0].getElementsByTagName("container-type")
		cType = cnodes[0].firstChild.data
	except:
		cType = ""

	LINES.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
	LINES.append('<stp:step-creation xmlns:stp="http://genologics.com/ri/step">')
	LINES.append('<configuration uri="' + nextStepURI + '"/>')
	if len(cType) > 0:
		LINES.append('<container-type>' + cType + '</container-type>')
	LINES.append('<inputs>')
	for uri in artifactURIs:
		LINES.append('<input uri="' + uri + '" replicates="1"/>')
	LINES.append('</inputs></stp:step-creation>')

	scXML = "".join(LINES)
	LOG.debug("Step Creation XML:")
	LOG.debug(scXML)
	rXML = api.createObject(scXML, BASE_URI + "steps")
	try:
		rDOM = parseString(rXML)
	except:
		LOG.info("Error Creating Step, Invalid XML was returned:")
		LOG.info(rXML)
		return

	# # did we get an exception
	nodes = rDOM.getElementsByTagName("exc:exception")
	if len(nodes) > 0:
		LOG.info("Step was not created")
		LOG.info(rDOM.toxml())
		return

	# # try to dig out the LUID from the newly created step
	try:
		nodes = rDOM.getElementsByTagName("stp:step")
		npLUID = nodes[0].getAttribute("limsid")
		LOG.info("Step was created, with LUID: " + npLUID)
	except:
		LOG.info("Step was created, but could not find its id")
		LOG.info(rXML)
		return

	# # now we need to switch the user
	npURI = BASE_URI + "processes/" + npLUID
	npXML = api.getResourceByURI(npURI)
	npDOM = parseString(npXML)

	nodes = npDOM.getElementsByTagName("technician")
	nodes[0].setAttribute("uri", rURI)

	# # update the process:
	LOG.info("Updating the process with: " + rURI)
	rXML = api.updateObject(npDOM.toxml(), npURI)
	LOG.info(rXML)

def finishStep():

	if args[ "action" ] == "START":
		# # get the current user, as we'll need this when we start the next step
		rURI = getCurrentUser()
		LOG.debug("Current user is: " + rURI)

		# # get the placed outputs from this process, as we'll need them to start the next process in the sequence
		artifactURIs = getProcessOutputs()

	status = advanceStep()
	if status is False:
		# #try again
		status = advanceStep()

	if status is False:
		LOG.info("Unable to advance step")
		return

	# # step is now on next steps screen
	if routeAnalytes() is True:
			# # advance the step to completion
			status = advanceStep()
			if status is False:
				# #try again
				status = advanceStep()

	if status is False:
		LOG.info("Unable to advance step")
		return

	if args[ "action" ] == "START":
		# # now start the next step
		startNextStep(artifactURIs, rURI)

def main():

	global api
	global args
	global SH
	global LOG

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "u:p:s:a:")

	for o, p in opts:
		if o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-s':
			args[ "stepURI" ] = p
		elif o == '-a':
			args[ "action" ] = p

	setupGlobalsFromURI(args[ "stepURI" ])
	api = glsapiutil.glsapiutil()
	api.setHostname(HOSTNAME)
	api.setVersion(VERSION)
	api.setup(args[ "username" ], args[ "password" ])
	# # set up a step handler
	SH = clarityHelpers.stepHelper()
	SH.setStepURI(args[ "stepURI" ])
	SH.setAPIHandler(api)

	# # at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	# # so let's get this show on the road!

	# # set up the logging components
	# Set up a specific logger with our desired output level
	LOG = logging.getLogger("finishStep")
	LOG.setLevel(logging.DEBUG)

	# Add the LOG message handler to the logger
	handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5000000, backupCount=5)
	# create formatter
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	# add formatter to handler
	handler.setFormatter(formatter)

	LOG.addHandler(handler)
	LOG.info("+++++++++++++++++++++++++")
	LOG.debug(BASE_URI)

	finishStep()

if __name__ == "__main__":
	time.sleep(5)
	main()
