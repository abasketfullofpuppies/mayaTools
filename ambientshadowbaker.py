import baseUIWindow
import maya.cmds as cmds
import maya.OpenMaya as om
from maya import mel  
import shutil

class geoSphereCreator:

	def geoSphere(self, divisions, radius):
		if divisions == 1:
			return cmds.polyPlatonicSolid(radius=radius,solidType=2,constructionHistory=False)  
		if divisions >= 2:
			geoSphereObj = cmds.polyPlatonicSolid(radius=radius,solidType=1,constructionHistory=False) 
			#rotate to match 1st division
			cmds.xform(geoSphereObj,rotation=[0,0,31.717])
			cmds.makeIdentity(geoSphereObj,apply=True) 		
			if divisions > 2:  
				#tesselate the object
				for i in range(2,divisions,1):  
					nf = cmds.polyEvaluate(geoSphereObj,face=True)  
					cmds.polySmooth(geoSphereObj, mth=0, dv=1, c=0, ch=False)  
					nvtx = cmds.polyEvaluate(geoSphereObj,vertex=True)  
					cmds.select('%s.vtx[%s:%s]'%(geoSphereObj[0], nvtx-nf, nvtx))  
					mel.eval('DeleteVertex;')  
					cmds.polyTriangulate(geoSphereObj) 
			#inflate the verts
			selected = om.MSelectionList()  
			om.MGlobal.getSelectionListByName(geoSphereObj[0], selected)  
			path = om.MDagPath()  
			selected.getDagPath(0, path)  
			iter = om.MItMeshVertex(path)  
			mesh = om.MFnMesh(path)  
			while not iter.isDone():              
				#defaults to object space  
				point = iter.position()  
				mesh.setPoint( iter.index(), om.MPoint( om.MVector(point).normal()*radius ) )  
				iter.next()  
		
			return geoSphereObj

class AmbientShadowBaker:	
	
	def __init__(self):
		self.lights = []
		self.geoSphereCreatorInst = geoSphereCreator()
		print 'AmbientShadowBaker initialized'
		
	def rebuildLightRig(self, detailLevels, lightType, minHeight, obj):
	
		temp = cmds.ls( sl=True )
		
		self.deleteLights()		
		self.lights = []
		self.lightType = lightType
		
		
		bBox = self.getBBox(obj)
		xBB = (bBox[0] + bBox[3])/ 2;
		yBB = (bBox[1] + bBox[4])/ 2;
		zBB = (bBox[2] + bBox[5])/ 2;		
		bbCenter = om.MVector(xBB,yBB,zBB)
		bbCorner = om.MVector(bBox[0],bBox[1],bBox[2])		
		bbRadius = (bbCorner - bbCenter).length() *1.5
		
		
		lightGeoSphere = self.geoSphereCreatorInst.geoSphere(detailLevels,bbRadius)	
		cmds.move( xBB,yBB,zBB , lightGeoSphere)
		sphereVerts =cmds.ls((lightGeoSphere[0]+'.vtx[*]'),flatten=True) 
		
		for vert in sphereVerts:
					
			vertPos = cmds.xform(vert, query = True, worldSpace = True, translation = True)
			minPos = bbCenter.y - bbRadius + (bbRadius*2*minHeight)
			minY = float('%.3f'%(minPos))
			vertPosY = float('%.3f'%(vertPos[1]))
			if vertPosY >= minY:
				self.lights.append(self.createLight(vertPos, 5))
							
		cmds.group(self.lights, name='lightRig')
		cmds.delete(lightGeoSphere)
		if len(temp) >0:
			cmds.select(temp)
	
	def createLight(self, pos, shadowRays ):
		light =  cmds.shadingNode(self.lightType ,asLight=True)
		cmds.setAttr( light+'.useRayTraceShadows', 1)
		cmds.setAttr( light+'.shadowRays', shadowRays)
		cmds.move( pos[0], pos[1], pos[2] , light)
		return light
		
	def deleteLights(self):
		for light in self.lights:
			if cmds.objExists(light):
				cmds.delete(light)
			
	def getBBox(self, obj):
		bBoxWS = cmds.xform( obj, query = True, worldSpace = True, boundingBox = True )
		return bBoxWS;
		
	def bakeAO(self, obj, uvChannel, filePath):	
		mrLoaded = cmds.pluginInfo( 'Mayatomr.mll',query = True, loaded = True)
		if mrLoaded == 0:
			cmds.loadPlugin('Mayatomr.mll')
		bakeSet = mel.eval('createBakeSet( "textureBakeSet1", "textureBakeSet" )' )
		mel.eval('assignBakeSet( "'+bakeSet+'", "'+ obj +'");')
		cmds.setAttr( bakeSet+".colorMode",  1)	
		cmds.setAttr( bakeSet+".xResolution",  512)
		cmds.setAttr( bakeSet+".yResolution",  512)
		cmds.setAttr( bakeSet+".samples",  2)
		cmds.setAttr( bakeSet+".backgroundColor",  1, 1, 1, type="double3")
		cmds.setAttr( bakeSet+".backgroundMode",  1)
		cmds.setAttr( bakeSet+".fillTextureSeams",  1)
		cmds.setAttr( bakeSet+".fileFormat",  1)
		cmds.setAttr( bakeSet+".overrideUvSet",  1)
		cmds.setAttr( bakeSet+".uvSetName", uvChannel,  type="string")
		
		
		objShape = cmds.listRelatives(obj,shapes=True, fullPath = True)[0]
		
		shadeGroup = cmds.listConnections(objShape, type = "shadingEngine" )
		
		 
		result = mel.eval("convertLightmap  -camera persp -sh -ulb " + shadeGroup[0] + " " +objShape+";" )
		
		
		currentProject = cmds.workspace( query = True,  rootDirectory = True)
		src = currentProject +'renderData/mentalray/lightMap/'+result[0]+'.tif'
		lastChar = filePath[len(filePath)-1]
		if lastChar != '/':
			if lastChar != '\\':
				filePath+='/'
		dst = filePath +result[0]+'.tif'
		if src != dst:
			shutil.move(src, dst)
		print 'Output File:' , dst
		
class AmbientShadowBakerUI(baseUIWindow.baseUI):	
	
	def __init__(self):
		self.AmbientShadowBakerInst = AmbientShadowBaker()
		baseUIWindow.baseUI.__init__(self,'AmbientShadowBaking', 300, 350)		
		print 'AO Baking UI initialized'
		
	def addUIElements(self):
		self.addTextField('target')
		self.addText('')
		self.addIntField('DetailLevels', default = 1, min = 1)
		self.addRadioButtons(['ambientLight','pointLight'])
		self.addFloatField('lightMinHeight', default = 0.0, min = 0.0, max = 1.0)
		self.addButton('RebuildLightRig', self.rebuildLightRigBase, 'Rebuild the light rig' , alignment = 'left')
		self.addText('')
		self.addTextField('UVchannel', addButtons = False, default = 'lightMapUVs')
		currentProject = cmds.workspace( query = True,  rootDirectory = True)
		defaultPath = currentProject +'renderData/mentalray/lightMap/'
		self.addTextField('FilePath', addButtons = False, default = defaultPath)
		self.addText('')
		self.addButton('Bake AO', self.bakeAOBase, 'Bake AO' )
		
	def rebuildLightRigBase(self, *args):
		print 'toBake'
		detailLevels = self.getIntField('DetailLevels')
		radioButtonSelected = self.getRadioButtonSelection(['ambientLight','pointLight'])
		minHeight = self.getFloatField('lightMinHeight')
		print 'toBake'
		toBake = self.getTextField('target')
		
		if cmds.objExists(toBake):
			self.AmbientShadowBakerInst.rebuildLightRig(detailLevels, radioButtonSelected, minHeight, toBake)
			
	def bakeAOBase(self,*args):
		toBake = self.getTextField('target')		
		uvChannel = self.getTextField('UVchannel')
		filePath = self.getTextField('FilePath')
		if cmds.objExists(toBake):
			print 'baking', toBake
			self.AmbientShadowBakerInst.bakeAO(toBake, uvChannel, filePath)
			#print 'baking', toBake
		
		
	
		
AmbientShadowBakerUI()