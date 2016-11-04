'''
Created on 28.10.2016

@author: boehm
'''

import platform
import glsapiutil

HOSTNAME = platform.node()
VERSION = 'v2'
BASE_URI = HOSTNAME + '/api/' + VERSION + '/'
USERNAME = 'username'
PASSWORD ='password'
api = None

def main():
    global api 
    api = glsapiutil
    api.setHostname(HOSTNAME)
    api.setVersion(VERSION)
    api.setup(USERNAME,PASSWORD)
    
    api = glsapiutil.glsapiutil2() ## initialise the API object, using version 2 of 
    setupGlobalsFromURI( args.stepURI ) #assuming the step URI was passed by the EPP trigger

    api.setHostname( HOSTNAME ) # set the hostname, currently taken from the system
    api.setVersion( VERSION ) # the version, currently set to 'v2'
    api.setup( USERNAME, PASSWORD ) # authenticate with the Clarity API user credentials
    


def setupGlobalsFromURI( uri ):
    global HOSTNAME
    global VERSION
    global BASE_URI
    tokens = uri.split( '/' )
    HOSTNAME = '/'.join( tokens[0:3] )
    VERSION = tokens[4]
    BASE_URI = '/'.join( tokens[0:5] ) + '/'