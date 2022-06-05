import baseUIWindow
import maya.cmds as cmds
from maya import mel  
import maya.OpenMaya as om
import random

class vertexWeightUI(baseUIWindow.baseUI):

	def __init__(self):
		baseUIWindow.baseUI.__init__(self,'PlantVertexColorGenerator', 300, 250)

	def addUIElements(self):
		self.addList('BranchObjects')
		self.addText('')
		self.addTextField('TrunkObjects')
		self.addText('')
		self.addButton('Combine and Export', self.combineAndExportColor, 'combine and export the objects' )
		
	def combineAndExportColor(self, *args):
		branches = self.getListContents('BranchObjects')
		dupBranches = cmds.duplicate(branches)
		for dup in dupBranches:
			self.applyColor(dup);
		trunk = self.getTextField('TrunkObjects')
		dupTrunk = cmds.duplicate( trunk)
		self.applyColorTrunk(dupTrunk);
		
		cmds.polyUnite(dupBranches,dupTrunk)
		cmds.delete(ch = True)
		mel.eval("ExportSelection;")
		
	def applyColorTrunk(self, obj):
		
		objShape, objMFnMesh, vColors, vPositions, vIndices = self.getAPIHandles(obj)
		
		lenVertexList = vColors.length()
		
		for vert in range(lenVertexList):
			
			#apply the color
			cVal = om.MColor(0,0,0,1)			
			vColors.set(cVal,vert)
		objMFnMesh.setVertexColors(vColors,vIndices,None ) 
	
	def applyColor(self, obj):
		oRot = cmds.xform(obj, query = True, rotation =True)
		cmds.rotate( 0, 0, 0, obj)
		
		objShape, objMFnMesh, vColors, vPositions, vIndices = self.getAPIHandles(obj)
		originalColors = om.MColorArray()
		lenVertexList = vColors.length()
		
		gVal = random.uniform(0,1)
		furthestDistance = self.getBranchMaxDistance(vPositions, obj)
		for vert in range(lenVertexList):
			
			rVal = self.getEdgeStiffness(vPositions[vert], obj, objShape)
			
			xFormTrans = cmds.xform(obj, query = True, translation =True)
			toVertX = vPositions[vert].x - xFormTrans[0]
			if furthestDistance != 0:
				bVal = toVertX / furthestDistance
			else:
				bVal = 1
			
			#apply the color
			cVal = om.MColor(rVal,gVal,bVal,1)
			
			vColors.set(cVal,vert)
		objMFnMesh.setVertexColors(vColors,vIndices,None ) 
		
		cmds.rotate( oRot[0],oRot[1],oRot[2], obj)
	
	def getEdgeStiffness(self, vert, obj, objShape):
		forwardV = om.MVector(1,0,0)
		xFormTrans = cmds.xform(obj, query = True, translation =True)
		transV = om.MVector(xFormTrans[0], 0, xFormTrans[2])
		vertTransV = om.MVector(vert)
		vertTransV.y = 0
		toVertV = vertTransV - transV
		toVertV = toVertV.normal()
		forwardV = forwardV.normal()
		dot = abs(toVertV * forwardV)
		dot = abs(dot)
		rVal = 0
		if dot < 0.90:
			rVal = 1
		return rVal
		
		
	def getBranchMaxDistance(self, verts, obj):
		lenVertexList = verts.length()
		furthestDistance = 0
		for vert in range(lenVertexList):			
			
			xFormTrans = cmds.xform(obj, query = True, translation =True)
			toVertX = verts[vert].x - xFormTrans[0]
			if toVertX  > furthestDistance:
				furthestDistance = toVertX
		
		return furthestDistance	
	
	def get_DAG( self, node):
		dag = None
		if cmds.objExists(node ) == True:
			selectionList = om.MSelectionList()
			selectionList.add(node)
			dag = om.MDagPath()
			oNode = selectionList.getDagPath(0, dag)
		return dag
	
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
		
	def combineAndExport(self, *args):
		branches = self.getListContents('BranchObjects')
		trunk = self.getTextField('TrunkObjects')
		duplicates = cmds.duplicate( branches, trunk)
		cmds.polyUnite(duplicates)
		cmds.delete(ch = True)
		mel.eval("ExportSelection;")
		
vertexWeightUI()