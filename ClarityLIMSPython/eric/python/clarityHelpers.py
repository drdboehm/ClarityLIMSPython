__author__ = 'mark'

from xml.dom.minidom import parseString

class stepOutput:

	def __init__(self):
		self.__inputLUID = ""
		self.__LUID = ""
		self.__type = ""
		self.__isShared = False
		self.__props = {}
		pass

	def setInputLUID(self, value): self.__inputLUID = value
	def getInputLUID(self): return self.__inputLUID

	def setOutputLUID(self, value): self.__LUID = value
	def getOutputLUID(self): return self.__LUID

	def setOutputType(self, value): self.__type = value
	def getOutputType(self): return self.__type

	def setIsShared(self, value): self.__isShared = value
	def getIsShared(self): return self.__isShared

	def setProperty(self, propName, propValue): self.__props[ propName ] = propValue
	def getProperty(self, propName):
		if propName in self.__props.keys():
			return self.__props[ propName ]
		else:
			return ""

	def toString(self):
		txt = "Input:" + self.__inputLUID
		txt += " Output:" + self.__LUID
		txt += " Type:" + self.__type
		txt += " Shared:" + str(self.__isShared)

		for k in self.__props.keys():
			txt += " " + k + ":" + str(self.__props[ k ])

		return txt

class IOMapper:

	def __init__( self ):
		self.__stepURI = ""
		self.__IOMaps = []
		self.__detailsDOM = None
		self.__APIHandler = None

	def setStepURI( self, value ): self.__stepURI = value
	def setAPIHandler(self, object ): self.__APIHandler = object

	def getIOMaps( self, outputType="", shared=False ):
		if len(self.__stepURI) > 0:
			## do we already have a populated DOM? If not, fetch the XML we require
			if self.__detailsDOM is None:
				detailsURI = self.__stepURI + "/details"
				detailsXML = self.__APIHandler.getResourceByURI( detailsURI )
				self.__detailsDOM = parseString( detailsXML )

				IOMaps = self.__detailsDOM.getElementsByTagName( "input-output-map" )
				for IOMap in IOMaps:
					tmp = stepOutput()
					nodes = IOMap.getElementsByTagName( "input" )
					iLUID = nodes[0].getAttribute( "limsid" )
					tmp.setInputLUID( iLUID )
					nodes = IOMap.getElementsByTagName( "output" )
					## does the step even produce outputs? Maybe not
					if len(nodes) > 0:
						tmp.setOutputLUID( nodes[0].getAttribute( "limsid" ) )
						tmp.setOutputType( nodes[0].getAttribute( "type" ) )
						## set the output-generation-type
						ogType = nodes[0].getAttribute( "output-generation-type" )
						if ogType == "PerInput":
							tmp.setIsShared( False )
						else:
							tmp.setIsShared( True )

					## do we want this as part of our collection?
					if shared is True:
						if len(outputType) == 0:
							self.__IOMaps.append( tmp )
						elif outputType == tmp.getOutputType():
							self.__IOMaps.append( tmp )
					elif shared is False and tmp.getIsShared() is False:
						if len(outputType) == 0:
							self.__IOMaps.append( tmp )
						elif outputType == tmp.getOutputType():
							self.__IOMaps.append( tmp )

		return self.__IOMaps

class stepHelper:

	def __init__( self ):
		self.__stepURI = ""
		self.IOMaps = None
		self.__APIHandler = None
		self.__placementsDOM = None
		self.__processDOM = None
		self.__poolingDOM = None
		pass

	def setStepURI( self, value ): self.__stepURI = value
	def setAPIHandler(self, object ): self.__APIHandler = object

	def getIOMaps( self, outputType="", shared=False ):
		if self.IOMaps is None:
			self.IOMaps = IOMapper()
			self.IOMaps.setStepURI( self.__stepURI )
			self.IOMaps.setAPIHandler( self.__APIHandler )
		IOMaps = self.IOMaps.getIOMaps( outputType, shared )

		return IOMaps

	def getSelectedContainers( self ):

		scLUIDs = []

		if len(self.__stepURI) > 0 and self.__placementsDOM is None:
			placementsURI = self.__stepURI + "/placements"
			placementsXML = self.__APIHandler.getResourceByURI( placementsURI )
			self.__placementsDOM = parseString( placementsXML )

		nodes = self.__placementsDOM.getElementsByTagName( "selected-containers" )
		scNodes = nodes[0].getElementsByTagName( "container")
		for sc in scNodes:
			scURI = sc.getAttribute( "uri")
			scLUID = scURI.split( "/" )[-1:]

			scLUIDs.append( scLUID )

		return scLUIDs

	def getProcessDOM(self):

		if self.__processDOM is None:
			pURI = self.__stepURI.replace( "steps", "processes" )
			detailsXML = self.__APIHandler.getResourceByURI( pURI )
			self.__processDOM = parseString( detailsXML )

		return self.__processDOM

	def getPoolingDOM(self):

		if self.__poolingDOM is None:
			pURI = self.__stepURI + "/pools"
			pXML = self.__APIHandler.getResourceByURI( pURI )
			self.__poolingDOM = parseString( pXML )

		return self.__poolingDOM

	def getPlacementsDOM(self):

		if len(self.__stepURI) > 0 and self.__placementsDOM is None:
			placementsURI = self.__stepURI + "/placements"
			placementsXML = self.__APIHandler.getResourceByURI( placementsURI )
			self.__placementsDOM = parseString( placementsXML )

		return self.__placementsDOM