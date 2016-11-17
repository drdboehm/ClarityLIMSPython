import sys
import getopt
import glsapiutil
import xml.dom.minidom
from xml.dom.minidom import parseString

HOSTNAME = 'http://192.168.8.10:8080'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

DEBUG = False
api = None
args = None

def checkFields():

	# # get the process XMl and turn it into a DOM
	pURI = BASE_URI + "processes/" + args[ "limsid" ]
	pXML = api.getResourceByURI(pURI)
	pDOM = parseString(pXML)

	# # process each field passed to the script in the -f parameter
	failedFields = []
	for field in args[ "fields" ].split(","):
		field = field.strip()

		# # check the value of this field
		value = api.getUDF(pDOM, field)
		if len(value) == 0:
			failedFields.append(field)

	# # report back to user:
	if len(failedFields) > 0:
		msg = "The following fields have been marked as mandatory, and must be populated: " + ",".join(failedFields)
		print msg
		api.reportScriptStatus(BASE_URI + "steps/" + args[ "limsid" ], "ERROR", msg)

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:f:")

	for o, p in opts:
		if o == '-l':
			args[ "limsid" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-f':
			args[ "fields" ] = p

	api = glsapiutil.glsapiutil()
	api.setHostname(HOSTNAME)
	api.setVersion(VERSION)
	api.setup(args[ "username" ], args[ "password" ])

	# # at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	# # so let's get this show on the road!
	checkFields()

if __name__ == "__main__":
	main()
