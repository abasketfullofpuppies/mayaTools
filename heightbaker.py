import maya.cmds as cmds
import maya.OpenMaya as om
import math

class heightBaker:	
	
	def __init__(self):
		print 'heightBaker initialized'
		
	
		
	def bakeHeight(self, toBake, ignoreFloating, excludeMeshes, normalizedHeight, ceilHeight, mapScale, mapBias, heightRGBA, heightRGB, *args):
		
		print 'baking alpha'
		
		self.normalizedHeight = normalizedHeight
		self.ceilHeight = ceilHeight
		self.mapScale = mapScale 
		self.mapBias = mapBias 
		self.heightRGBA = heightRGBA
		self.heightRGB = heightRGB
		
		#some diagnostic info
		totalTimer = cmds.timerX()		
		vertsRayTested = 0
		rayTests = 0
		rayHitCount=0
		rayMissCount=0
		
		temp = cmds.ls( sl=True )
		
			
		#API Stuff - shape, MFnMesh, vert Color list, vert Position list, vert Index list
		objShape, objMFnMesh, vColors, vPositions, vIndices = self.getAPIHandles(toBake)
		lenVertexList = vColors.length()
		
		if excludeMeshes != None:
			print 'adding to list'
			excludeMeshes.append(objShape)
		else:
			excludeMeshes = [objShape]
			
		
		meshes,meshesBBMin,meshesBBMax = self.getAllMeshBounds(excludeMeshes)			
		lenMeshesList = len(meshes)
		
		bakeTimeTotal = 0	
		castDir = om.MFloatVector(0,1,0)	
		originalColors = om.MColorArray()
		
		for vert in range(lenVertexList):
			
			#clear the alpha
			cVal = om.MColor()
			cVal = vColors[vert]
			originalColors.append(om.MColor(cVal.r,cVal.g,cVal.b,cVal.a))
			cVal.a = 0
			
			#find meshes with a bounding box that emcompasses the vert
			vPos = vPositions[vert]
			meshIndex = 0
			meshesToRayTest = []			
			for mesh in range(lenMeshesList):
				if vPos.x > meshesBBMin[meshIndex].x  and vPos.x < meshesBBMax[meshIndex].x :
					if vPos.z > meshesBBMin[meshIndex].z and vPos.z < meshesBBMax[meshIndex].z :
						if ignoreFloating == False:
							meshesToRayTest.append(meshes[mesh])
						elif vPos.y > meshesBBMin[meshIndex].y and vPos.y < meshesBBMax[meshIndex].y :
								meshesToRayTest.append(meshes[mesh])
				meshIndex += 1
				
			bakeTimer = cmds.timerX()
			if len(meshesToRayTest)	> 0:
				vertsRayTested +=1
				
			#order the meshes to test via distance to vert from center of bounding box
			meshesToRayTest = self.orderViaDistanceToCenter(vPos, meshesToRayTest)
				
			#rayTest the meshes with a bounding box that emcompasses the vert
			for meshToTest in meshesToRayTest:
				rayHitsFace,rayHitsPoint = self.rayCastHit(meshToTest,vPos, castDir, 999999)
				lenRayHits = len(rayHitsFace)
				if lenRayHits > 0 :
					#find and use the highest point
					highestHitPoint = 0
					highestVal = 0
					for rayHit in range(lenRayHits):
						face = str(meshToTest)+'.f['+str(rayHitsFace[rayHit])+']'
						point = rayHitsPoint[rayHit]
						toHit = point - vPos
						distanceToFace = toHit.length()
						if rayHit == 0:							
							highestHitPoint = point
							highestVal = distanceToFace
						elif highestHitPoint.y <point.y:
							highestHitPoint = point
							highestVal = distanceToFace
							
					#store distance as alpha
					cVal.a = highestVal
					rayHitCount+=1
					rayTests +=1
					break
				else:
					rayMissCount+=1
					rayTests +=1
			bakeTimeTotal += cmds.timerX(startTime=bakeTimer)
			vColors.set(cVal,vert)
			
		#handle color settings
		self.setColors(originalColors, vColors, vIndices, objMFnMesh)
		
		if len(temp) >0:
			cmds.select(temp)
		totalTime = cmds.timerX(startTime=totalTimer)
		
		
		print "Total Bake Time :", totalTime, "seconds"
		print "Total verts :", lenVertexList
		print vertsRayTested,"verts ray tested in :", bakeTimeTotal, "seconds"
		if rayHitCount > 0 and rayTests > 0:
			print int((float(rayHitCount)/rayTests)*100),"% ray hits - ", rayHitCount, "ray hits", rayMissCount, "ray misses", rayTests, "total ray tests"

	def setColors(self, originalColors, vColors, vIndices, objMFnMesh):

		lenVertexList = vColors.length()
		
		#find largest for normalization
		furthestDist = 0
		if self.normalizedHeight:
			for vert in range(lenVertexList):
				cVal = om.MColor()
				cVal = vColors[vert]
				if cVal.a > furthestDist:
					furthestDist = cVal.a
						
		for vert in range(lenVertexList):
			
			cVal = om.MColor()
			cVal = vColors[vert]
			if self.normalizedHeight:
				if furthestDist != 0:
					cVal.a = cVal.a/furthestDist
			if self.ceilHeight:
				if cVal.a > 0:
					cVal.a = 1
				elif cVal.a < 0:
					cVal.a = -1
			
			
			cVal.a *= self.mapScale
			cVal.a += self.mapBias
			
			
			if self.heightRGBA == True or self.heightRGB == 1:
				cVal = om.MColor(cVal.a,cVal.a,cVal.a,cVal.a)
				if self.heightRGB:
					oVal = om.MColor()
					oVal = originalColors[vert]
					cVal.a = oVal.a
			
			vColors.set(cVal,vert)
		#set all the colors
		objMFnMesh.setVertexColors(vColors,vIndices,None ) 
			
	def getBBCenter(self, obj):
		bBoxWS = cmds.xform( obj, query = True, worldSpace = True, boundingBox = True )
		xBB = (bBoxWS[0] + bBoxWS[3])/ 2;
		yBB = (bBoxWS[1] + bBoxWS[4])/ 2;
		zBB = (bBoxWS[2] + bBoxWS[5])/ 2;
		bbCenter = om.MVector(xBB,yBB,zBB)
		return bbCenter;
		
	def rayCastHit( self, mesh, vertPosition, dir, maxDistance):
		
		#API wrangling
		om.MGlobal.clearSelectionList()	
		om.MGlobal.selectByName(mesh)
		sList = om.MSelectionList()
		#Assign current selection to the selection list object
		om.MGlobal.getActiveSelectionList(sList)	
		item = om.MDagPath()
		sList.getDagPath(0, item)
		item.extendToShape()	
		fnMesh = om.MFnMesh(item)
		
		#setup vars
		faceIds = None
		triIds = None
		idsSorted = False
		testBothDirections = False
		worldSpace = om.MSpace.kWorld
		accelParams = None
		sortHits = True
		hitPoints = om.MFloatPointArray()
		hitRayParams = om.MFloatArray()
		hitFaces = om.MIntArray()
		hitTris = None
		hitBarys1 = None
		hitBarys2 = None
		tolerance = 0.0001
		
		hit = fnMesh.allIntersections(vertPosition, dir, faceIds, triIds, idsSorted, worldSpace, maxDistance, testBothDirections, accelParams, sortHits, hitPoints, hitRayParams, hitFaces, hitTris, hitBarys1, hitBarys2, tolerance)
		om.MGlobal.clearSelectionList()
		return hitFaces,hitPoints
	
	def get_DAG( self, node):
		selectionList = om.MSelectionList()
		selectionList.add(node)
		dag = om.MDagPath()
		oNode = selectionList.getDagPath(0, dag)
		return dag

	def getAllMeshBounds( self, excludeMeshes = []):	
		meshes = cmds.ls(type="mesh", long=True)
		meshesBBMin = []
		meshesBBMax = []
		spot = 0
		for mesh in range(len(meshes)):
			shortName = cmds.ls(meshes[spot] , shortNames=True)
			exclude = False
			for excludeMesh in excludeMeshes:
				if cmds.objExists(excludeMesh) and excludeMesh != None:
					excludeM = cmds.listRelatives(excludeMesh,shapes=True)
					if excludeM != None:
						excludeM = excludeM[0]
					else:
						excludeM = excludeMesh
					if excludeM == shortName[0]:
						exclude = True
						print 'mesh ',shortName[0]
						print 'excludeMesh ',excludeM
			if exclude != True:
				transform = cmds.listRelatives( meshes[spot],parent=1,fullPath=1 )
				transform =  transform[0].split('|')[-1]
				bBoxWS = cmds.xform( transform, query = True, worldSpace = True, boundingBox = True )
				meshesBBMin.append( om.MVector(bBoxWS[0],bBoxWS[1],bBoxWS[2]) )
				meshesBBMax.append( om.MVector(bBoxWS[3],bBoxWS[4],bBoxWS[5]) )
				spot+=1
			else:
				meshes.remove(meshes[spot])
		return meshes,meshesBBMin,meshesBBMax

	def getAPIHandles(self, toBake):
		temp = cmds.ls( sl=True )

		# query the color set
		cmds.select(toBake)		
		colorSet = cmds.polyColorSet( query=True, currentColorSet=True )
		#assign temporary colors if needed
		if colorSet == None:		
			cmds.polyColorPerVertex (r=1,g=1,b=0,a=0, clamped = True)
				
		#get the shape
		objShape = cmds.listRelatives(toBake,shapes=True)[0] 
		#get the MFnMesh 
		api_Dag = self.get_DAG(objShape)
		api_MFnMesh = om.MFnMesh(api_Dag) 		
		#get the vertex colors
		vertexColorList = om.MColorArray()
		api_MFnMesh.getVertexColors(vertexColorList)
		# get the vertPositions
		vertexPositionList = om.MFloatPointArray()		
		api_MFnMesh.getPoints(vertexPositionList, om.MSpace.kWorld)		
		#get the vertex list
		lenVertexList = vertexColorList.length()
		fnComponent = om.MFnSingleIndexedComponent()
		fullComponent = fnComponent.create( om.MFn.kMeshVertComponent )
		fnComponent.setCompleteData( lenVertexList );
		vertexIndexList = om.MIntArray()
		fnComponent.getElements(vertexIndexList)
		
		if temp != []:
			cmds.select(temp)
		
		return objShape, api_MFnMesh, vertexColorList, vertexPositionList, vertexIndexList

	def orderViaDistanceToCenter(self, pos, objs):
		#order the meshes to test via distance to vert from center of bounding box
		objsOrdered = []
		objsDistance = []
		posV = om.MVector(pos)
		for obj in objs:
			transform = cmds.listRelatives( obj,parent=1,fullPath=1 )
			transform =  transform[0].split('|')[-1]
			centerPoint = self.getBBCenter(transform)
			toCenter = centerPoint - posV
			toCenter = toCenter.length()
			if len(objsDistance) < 1:
				objsOrdered.append(obj)
				objsDistance.append(toCenter)
			else:
				for distanceSpot in range(len(objsDistance)):
					if toCenter < objsDistance[distanceSpot]:
						objsOrdered.insert(distanceSpot, obj)
						objsDistance.insert(distanceSpot, toCenter)
						break
						
		return objsOrdered
		
class heightBakerUI:	
	
	def __init__(self):
		self.heightBakerInst = heightBaker()
		self.heightBakingTools()
		print 'heightBaker UI initialized'
		
		
	def deleteHeightWindow(self, *args):
		if (cmds.window('heightBaking', exists = True)):
			cmds.deleteUI( 'heightBaking' )

	def heightBakingTools(self):
		#Check if window is up. If so - kill it.
		
		self.deleteHeightWindow()
		
		
		cmds.window('heightBaking', sizeable= False, menuBar = False, width = 300, height = 400, title = 'Heightmap Baking')
		
		cmds.columnLayout(width = 300)
		browseFiles = cmds.textField('objPath', width = 300 )
		cmds.setParent( '..' )
		
		cmds.rowColumnLayout( 'buttons', numberOfColumns = 3 , width = 300, columnSpacing = [(1,20),(2,20),(3,20)],columnWidth = [(1,70),(2,70),(3,70)])
		
		cmds.button(label = 'Set Target', width = 40, command  = self.setObjPath, annotation = 'Set the mesh to bake height onto' )
		cmds.button(label = 'Bake Height', width = 40, command  = self.bakeHeight, annotation = 'Bake the height' )
		cmds.button(label = 'Cancel', width = 40, command  = self.deleteHeightWindow, annotation = 'Click to cancel' )
		cmds.setParent( '..' )
		
		cmds.text( label=' ', align='center' )
		cmds.text( label='Height Storage:', align='center' )
		cmds.rowColumnLayout(  numberOfColumns = 3 , width = 300, columnSpacing = [(1,20),(2,20),(3,20)],columnWidth = [(1,70),(2,70),(3,70)])
		cmds.radioCollection()
		cmds.radioButton( 'heightRGB',label='RGB',  select =True)
		cmds.radioButton( 'heightA',label='A', )		
		cmds.radioButton( 'heightRGBA',label='RGBA')	
		cmds.setParent( '..' )
		
		cmds.text( label=' ', align='center' )
		cmds.columnLayout( adjustableColumn=True )
		cmds.checkBox( 'ignoreFloating',label='Ignore Non-Intersecting Objects',  value =True)
		cmds.setParent( '..' )
		cmds.text( label=' ', align='center' )
		
		cmds.text( label='Explicitly Ignored Objects:', align='center' )
		cmds.paneLayout(configuration = 'single', width =300)
		cmds.textScrollList( 'ignoredObjectList', numberOfRows=5, allowMultiSelection=True)
		cmds.setParent( '..' )
		cmds.setParent( '..' )
		
		cmds.rowColumnLayout( 'ignoredListButtons', numberOfColumns = 3 , width = 300, columnSpacing = [(1,20),(2,20),(3,20)],columnWidth = [(1,70),(2,80),(3,70)])
		
		cmds.button(label = 'Add Object', width = 40, command  = self.addToIgnoredObjectsList, annotation = 'Add the selected meshes to the list' )
		cmds.button(label = 'Remove Object', width = 40, command  = self.removeFromIgnoredObjectsList, annotation = 'Remove the selected meshes from the list' )
		cmds.button(label = 'Clear', width = 40, command  = self.clearIgnoredObjectsList, annotation = 'Clear the List' )
		cmds.setParent( '..' )
		
		cmds.text( label=' ', align='center' )
		cmds.columnLayout( adjustableColumn=True )
		cmds.radioCollection()
		cmds.radioButton( 'ceilHeight',label='Ceil Height', select = True)
		cmds.radioButton( 'normalizedHeight',label='Normalized Height')	
		cmds.setParent( '..' )
		
		cmds.columnLayout( adjustableColumn=True )
		cmds.text( label='Scale', align='left' )
		cmds.floatField( 'mapScale', value = 1.0)
		cmds.setParent( '..' )
		
		cmds.columnLayout( adjustableColumn=True )
		cmds.text( label='Bias', align='left' )
		cmds.floatField( 'mapBias', value = 0.0)
		cmds.setParent( '..' )
		
		cmds.showWindow('heightBaking')

	def setObjPath(self, *args):
		temp = cmds.ls( sl=True )
		if len(temp) == 1:
			cmds.textField('objPath', edit = True, text = temp[0])
		else:
			cmds.error( "Select a single object to bake" )

	def getObjPath(self):
		path = cmds.textField('objPath', query = True, text = True)
		return path

	def getIgnoreFloating(self):
		ignoreFloating  = False
		exists = cmds.checkBox('ignoreFloating', query = True, exists = True)
		if exists:
			ignoreFloating = cmds.checkBox('ignoreFloating', query = True, value = True)
		return ignoreFloating
	
	
	def addToIgnoredObjectsList(self, *args):
		if (cmds.textScrollList( 'ignoredObjectList', exists = True)):
			temp = cmds.ls( sl=True )
			if len(temp) > 0:
				currentContents = self.getIgnoredObjectsList()
				for obj in temp:
					doAppend = True
					if currentContents != None:
						for curobj in currentContents:
							if curobj == obj:
								doAppend = False
								break
					
					if doAppend:
						cmds.textScrollList("ignoredObjectList", edit=True, append = obj )
			else:
				cmds.error( "Select objects to remove from list" )
	
	def removeFromIgnoredObjectsList(self, *args):
		if (cmds.textScrollList( 'ignoredObjectList', exists = True)):
			temp = cmds.ls( sl=True )
			if len(temp) > 0:
				currentContents = self.getIgnoredObjectsList()
				for obj in temp:
					doRemove = False
					if currentContents != None:
						for curobj in currentContents:
							if curobj == obj:
								doRemove = True
								break
					
					if doRemove:
						cmds.textScrollList("ignoredObjectList", edit=True, removeItem = obj )
			else:
				cmds.error( "Select objects to remove from list" )
			
	def clearIgnoredObjectsList(self, *args):
		if (cmds.textScrollList( 'ignoredObjectList', exists = True)):
			cmds.textScrollList("ignoredObjectList", edit=True, removeAll = True )

	def getHeightRGBA(self):
		heightRGBA  = False
		exists = cmds.radioButton('heightRGBA', query = True, exists = True)
		if exists:
			heightRGBA = cmds.radioButton('heightRGBA', query = True, select = True)
		return heightRGBA
		
	def getHeightRGB(self):
		heightRGB  = False
		exists = cmds.radioButton('heightRGB', query = True, exists = True)
		if exists:
			heightRGB = cmds.radioButton('heightRGB', query = True, select = True)
		return heightRGB
		
		
	def getNormalizedHeight(self):
		normalizedHeight  = False
		exists = cmds.radioButton('normalizedHeight', query = True, exists = True)
		if exists:
			normalizedHeight = cmds.radioButton('normalizedHeight', query = True, select = True)
		return normalizedHeight
		
	def getCeilHeight(self):
		ceilHeight  = False
		exists = cmds.radioButton('ceilHeight', query = True, exists = True)
		if exists:
			ceilHeight = cmds.radioButton('ceilHeight', query = True, select = True)
		return ceilHeight
		
	def getMapScale(self):
		mapScale  = 1.0
		exists = cmds.floatField('mapScale', query = True, exists = True)
		if exists:
			mapScale = cmds.floatField('mapScale', query = True, value = True)
			print 'mapScale', mapScale
		return mapScale
		
	def getMapBias(self):
		mapBias  = 0
		exists = cmds.floatField('mapBias', query = True, exists = True)
		if exists:
			mapBias = cmds.floatField('mapBias', query = True, value = True)
		return mapBias
		
			
	def getIgnoredObjectsList(self):
		if (cmds.textScrollList( 'ignoredObjectList', exists = True)):
			currentContents = cmds.textScrollList("ignoredObjectList", query = True, allItems = True )
			return currentContents

	def bakeHeight(self,*args):
		toBake = self.getObjPath()
		if cmds.objExists(toBake):
			#get some settings
			ignoreFloating = self.getIgnoreFloating()
			print 'ignoreFloating',ignoreFloating
			excludeMeshes = self.getIgnoredObjectsList()
			normalizedHeight = self.getNormalizedHeight()
			ceilHeight = self.getCeilHeight()
			mapScale = self.getMapScale()
			mapBias = self.getMapBias()			
			heightRGBA = self.getHeightRGBA()
			heightRGB = self.getHeightRGB()
			
			self.heightBakerInst.bakeHeight(toBake, ignoreFloating, excludeMeshes,normalizedHeight,ceilHeight,mapScale,mapBias,heightRGBA,heightRGB)
		
#heightBakingTools()
heightBakerUI()