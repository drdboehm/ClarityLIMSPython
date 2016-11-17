import sys
import getopt
import re
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = True
api = None

ARTIFACTS = None
CACHE_IDS = []

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
			if nodes:
				naURI = nodes[0].getAttribute("next-step-uri")
				response = naURI

	return response

def routeAnalytes():

	# # Step 1: Get the XML relating to the actions resource for this step
	aURI = args[ "stepURI" ] + "/actions"
	aXML = api.getResourceByURI(aURI)
	aDOM = parseString(aXML)

	# # Step 2: Get the URI for the next-step, and select an action
	# # if we weren't given a -a flag, use the default next action for this step
	nsURI = ""
	if "action" in args.keys():
		action = args[ "action" ]
	else:
		nsURI = getNextActionURI(aXML)
		if DEBUG: print("URI for Next Action is:" + nsURI)
		if len(nsURI) == 0:
			action = "complete"
		else:
			action = "nextstep"

	# # Step 3: Hone in on the next-action nodes, as these will be the ones we update
	nodes = aDOM.getElementsByTagName("next-action")
	for node in nodes:
		# # ignore any nodes that already have an action attribute
		if not node.hasAttribute("action"):
			node.setAttribute("action", action)
			if len(nsURI) > 0:
				node.setAttribute("step-uri", nsURI)

	# # Step 4: update the LIMS
	rXML = api.updateObject(aDOM.toxml(), args[ "stepURI" ] + "/actions")
	try:
		rDOM = parseString(rXML)
		nodes = rDOM.getElementsByTagName("next-action")
		if len(nodes) > 1:
			# #api.reportScriptStatus( args[ "stepURI" ], "OK", "set Next Actions to default value" )
			pass
		else:
			api.reportScriptStatus(args[ "stepURI" ], "ERROR", "An error occured while trying to set Next Actions to default value:" + rXML)
	except:
		api.reportScriptStatus(args[ "stepURI" ], "ERROR", "An error occured while trying to set Next Actions to default value:" + rXML)

def main():

	global api
	global args

	args = {}

	# # opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:a:") 
	opts, extraparams = getopt.getopt(sys.argv[1:], "u:p:s:a:") 

	for o, p in opts:
		# # if o == '-l':
		# #	args[ "limsid" ] = p
		# # elif o == '-u':
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

	# # at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	# # so let's get this show on the road!

	routeAnalytes()

if __name__ == "__main__":
	main()
