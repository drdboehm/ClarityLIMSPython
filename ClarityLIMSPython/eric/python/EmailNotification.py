import sys
import getopt
import glsapiutil
import smtplib

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None
SIMULATE = False

ARTIFACTS = None
CACHE_IDS = []

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"

	if DEBUG is True:
		print HOSTNAME
		print BASE_URI


def sendMail(body, to_address):

	# Import the email modules we'll need
	from email.mime.text import MIMEText

	# For this example, assume that
	# the message contains only ASCII characters.
	msg = MIMEText( body )

	# me == the sender's email address
	# you == the recipient's email address
	me = 'postmaster@genologics.com'
	if len(to_address) == 0:
		you = 'noreply@genologics.com'
	else:
		you = to_address

	msg['Subject'] = 'Test'
	msg['From'] = me
	msg['To'] = you

	# Send the message via our own SMTP server, but don't include the
	# envelope header.

	# replace "localhost" below with the IP address of the mail server
	s = smtplib.SMTP('localhost')
	s.sendmail(me, [you], msg.as_string())
	s.quit()

def createMail():

	## create message of the email
	msg = "test"
	if SIMULATE is True:
		print msg
	else:
		sendMail( msg, "" )

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:")

	for o,p in opts:
		if o == '-l':
			args[ "limsid" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-s':
			args[ "stepURI" ] = p

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	## so let's get this show on the road!
	createMail()

if __name__ == "__main__":
	main()

