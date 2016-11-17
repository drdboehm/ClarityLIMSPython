import sys
import getopt
import os

def log(msg):

	f = open("/tmp/runLater.log", "w")
	f.write(msg + "\n")
	f.close()

def main():

	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "c:")

	for o, p in opts:
		if o == '-c':
			args[ "command" ] = p

	if len(args[ "command" ]) > 0:

		fName = "/opt/gls/clarity/customextensions/job.tmp"

		f = open(fName, "w")
		f.write('bash -l -c "' + args[ "command" ] + '"')
		f.close()

		cmd = "cd /tmp && /usr/bin/at -f " + fName + " now"
		log(cmd)
		os.system(cmd)
		print("This step will be finished for you. Press the 'Lab View' button on the main Clarity Tool Bar")

if __name__ == "__main__":
	main()
