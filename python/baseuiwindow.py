import maya.cmds as cmds
 from functools import partial

class baseUI(object):

	def __init__(self, windowName , windowX, windowY ):
		self.windowName = windowName
		self.windowNameSafe = self.convertSpaces(windowName)
		self.windowX = windowX
		self.windowY = windowY
		self.lists = {}
		self.textFields = {}
		self.intFields = {}
		self.intSliders = {}
		self.floatFields = {}
		self.floatSliders = {}
		self.radioButtons = {}
		self.checkBoxes = {}
		self.openUIWindow()
		print self.windowName,'initialized'
		
	def closeUIWindow(self,*args):				
		if (cmds.window( self.windowNameSafe, exists = True)):
				cmds.deleteUI( self.windowNameSafe )
		
	def addRootLayout(self):
		return cmds.columnLayout(width = self.windowX, height = self.windowY)
	
	def openUIWindow(self):
		#Check if window is up. If so - kill it.
		self.closeUIWindow()
				
		self.window = cmds.window(self.windowNameSafe, sizeable= True, menuBar = False, width = self.windowX, height = self.windowY , title = self.windowName)
		
		self.windowLayout = self.addRootLayout()
		cmds.setParent(self.window)
		
		self.addUIElements()
			
		cmds.showWindow(self.window)
	
	#override this function to add UI elements 	
	def addUIElements(self):
		
		#to demonstrate how this works I add the currently supported UI elements
		self.addList('Objects')
		self.addText('')
		self.addTextField('Object')
		self.addText('')
		self.addIntField('Int', default = 1, max = 10)
		self.addText('')
		self.addFloatField('Float', default = 0.5, max = 5)
		self.addText('')
		self.addRadioButtons(['button 1','button 2','button 3'])
		self.addText('')
		self.addButton('Button', self.demoButton, 'click to list the objects' )
	
	def demoButton(self, *args):
		list = self.getListContents('Objects')
		print 'list', list
		field = self.getTextField('Object')
		print 'text field', field		
		intField = self.getIntField('Int')
		print 'int field', intField	
		floatField = self.getFloatField('Float')
		print 'float field', floatField	
		radioButtonSelected = self.getRadioButtonSelection(['button 1','button 2','button 3'])
		print 'Selected Radio Button', radioButtonSelected	
		
		print 'button clicked'
		
		
	def convertSpaces(self, toConvert):
		converted = toConvert.replace (" ", "_")
		return converted
		
	def convertUnderscore(self, toConvert):
		converted = toConvert.replace ("_", " ")
		return converted
		
	#---lists	
	def addList(self, listName):
		
		self.addText( listName+':')
		#list
		cmds.paneLayout(configuration = 'single', width =300)
		validName = self.convertSpaces(listName)
		newList = cmds.textScrollList( validName, numberOfRows=5, allowMultiSelection=True)
		self.lists[listName] = newList
		cmds.setParent( self.windowLayout )
		#buttons
		cmds.rowColumnLayout( listName+'Buttons', numberOfColumns = 3 , width = 300, columnSpacing = [(1,20),(2,20),(3,20)],columnWidth = [(1,70),(2,80),(3,70)])
		
		cmds.button(label = 'Add Object', width = 40, command  = partial(self.addToList,newList), annotation = 'Add the selected meshes to the list' )
		cmds.button(label = 'Remove Object', width = 40, command  = partial(self.removeFromList,newList), annotation = 'Remove the selected meshes from the list' )
		cmds.button(label = 'Clear', width = 40, command  = partial(self.clearList,newList), annotation = 'Clear the List' )
		cmds.setParent( self.windowLayout )
	
	def addToList(self,list,*args):
		if (cmds.textScrollList( list, exists = True)):
			temp = cmds.ls( sl=True )
			if len(temp) > 0:
				currentContents = self.getListContents( list )
				for obj in temp:
					doAppend = True
					if currentContents != None:
						for curobj in currentContents:
							if curobj == obj:
								doAppend = False
								break
					
					if doAppend:
						textToAppend = obj
						if textToAppend[0] == '|':
							textToAppend =  textToAppend.replace("|", "")
						cmds.textScrollList(list, edit=True, append = textToAppend )
			else:
				cmds.error( "Select objects to remove from list" )	
	
	def removeFromList(self,list,*args):
		if (cmds.textScrollList( list, exists = True)):
			temp = cmds.ls( sl=True )
			if len(temp) > 0:
				currentContents = self.getListContents(list)
				for obj in temp:
					doRemove = False
					if currentContents != None:
						for curobj in currentContents:
							if curobj == obj:
								doRemove = True
								break
					
					if doRemove:
						cmds.textScrollList(list, edit=True, removeItem = obj )
			else:
				cmds.error( "Select objects to remove from list" )
		
	def clearList(self,list,*args):
		if (cmds.textScrollList( list, exists = True)):
			cmds.textScrollList(list, edit=True, removeAll = True )
		
	def getListContents(self,listName):	
		print listName
		listPath = listName.split('|')
		listName = listPath[len(listPath)-1]
		listName = self.convertUnderscore(listName)
		list = self.lists[listName]
		
		if (cmds.textScrollList( list, exists = True)):
			print 'found'
			currentContents = cmds.textScrollList(list, query = True, allItems = True )
			return currentContents
	
	#radio buttons
	def addRadioButtons(self, buttons, default = 0):
		cmds.columnLayout()	
		cmds.radioCollection()
		spot = 0
		for button in buttons:
			validName =  self.convertSpaces(button)
			newButton =  cmds.radioButton( validName,label=button)
			self.radioButtons[button] = newButton
			if spot == default:
				cmds.radioButton( newButton, edit = True, select = True)
			spot += 1
		cmds.setParent( self.windowLayout )
		
	def getRadioButtonSelection(self, buttons):
		selectedButton = None
		for button in buttons:
			radioButton = self.radioButtons[button]
			exists = cmds.radioButton(radioButton, query = True, exists = True)
			if exists:
				selected = cmds.radioButton(radioButton, query = True, select = True)
				if selected == True:
					selectedButton = button
					break
		return selectedButton

	def addCheckbox(self, button, default, note = "", changeCmnd = "", parent = 'windowLayout'):
		validName =  self.convertSpaces(button)
		newButton = cmds.checkBox(validName, label= button, value = default, annotation = note )
		if changeCmnd != "":
			cmds.checkBox(newButton, changeCommand = changeCmnd, edit = True )
		self.checkBoxes[button] = newButton
		if parent == 'windowLayout': parent = self.windowLayout        
		cmds.setParent(parent)
				
	def getCheckbox(self, button):
		checkbox = self.checkBoxes[button]
		exists = cmds.checkBox(checkbox, query = True, exists = True)
		if exists:
			return cmds.checkBox(checkbox, query = True, value = True)			
	




	
	#text label	
	def addText(self, textLabel, parent = 'windowLayout'):
		self.textLayout = cmds.columnLayout()
		cmds.text( label= textLabel, align='center' )
		if parent == 'windowLayout':
			cmds.setParent( self.windowLayout )
		
	def addIntSlider(self, fieldName, dragC, changeC, default = 0, min = None, max = None, parent =  'windowLayout'):
		validName =  self.convertSpaces(fieldName)
		newField = cmds.intSliderGrp(label = validName, value = default, dragCommand =  dragC, changeCommand = changeC,  columnWidth = [1, 50], columnWidth2 =[2,40] , field = True )
		if min != None:
			cmds.intSliderGrp(newField, edit = True, minValue = min)
			cmds.intSliderGrp(newField, edit = True, fieldMinValue = min)
		if max != None:
			cmds.intSliderGrp(newField, edit = True, maxValue = max)
			cmds.intSliderGrp(newField, edit = True, fieldMaxValue = max)

		self.intSliders[fieldName] = newField
		if parent == 'windowLayout': parent = self.windowLayout
		cmds.setParent(parent)

	def getIntSlider(self,fieldName, *args):
		try:
			intFieldObj = self.intSliders[fieldName]
		except:
			return 0
		value = cmds.intSliderGrp( intFieldObj, query = True, value = True)
		return value    

	def addIntField(self, fieldName, default = 0, min = None, max = None ):
		#label
		self.addText( fieldName+':')
		#field
		cmds.columnLayout()	
		validName =  self.convertSpaces(fieldName)
		newField = cmds.intField(validName, value = default, width = 50)
		if min != None:
			cmds.intField(newField, edit = True, minValue = min)
		if max != None:
			cmds.intField(newField, edit = True, maxValue = max)
		self.intFields[fieldName] = newField
		cmds.setParent( self.windowLayout )
		
	def getIntField(self,field, *args):
		intFieldObj = self.intFields[field]
		value = cmds.intField( intFieldObj, query = True, value = True)
		return value
		
	
	def addFloatSlider(self, fieldName, dragC, changeC, default = 0, min = None, max = None , parent =  'windowLayout' , columnWidth = 50 ):
		validName =  self.convertSpaces(fieldName)
		newField = cmds.floatSliderGrp(label = validName, value = default, dragCommand =  dragC, changeCommand = changeC,  columnWidth = [1, columnWidth], columnWidth2 =[2, columnWidth] , field = True )
		if min != None:
			cmds.floatSliderGrp(newField, edit = True, minValue = min)
			cmds.floatSliderGrp(newField, edit = True, fieldMinValue = min)
		if max != None:
			cmds.floatSliderGrp(newField, edit = True, maxValue = max)
			cmds.floatSliderGrp(newField, edit = True, fieldMaxValue = max)

		self.floatSliders[fieldName] = newField
		if parent == 'windowLayout': parent = self.windowLayout
		cmds.setParent(parent)

	def getFloatSlider(self,fieldName, *args):
		try:
			floatFieldObj = self.floatSliders[fieldName]
		except:
			return 0
		value = cmds.floatSliderGrp( floatFieldObj, query = True, value = True)
		return value    

	def addFloatField(self, fieldName, default = 0, min = None, max = None, parent = 'windowLayout' ):
		#label
		self.addText( fieldName+':', parent = parent)
		#field
		cmds.columnLayout()	
		validName =  self.convertSpaces(fieldName)
		newField = cmds.floatField(validName, value = default, width = 50)
		if min != None:
			cmds.floatField(validName, edit = True, minValue = min)
		if max != None:
			cmds.floatField(validName, edit = True, maxValue = max)
		self.floatFields[fieldName] = newField
		if parent == 'windowLayout':
			cmds.setParent( self.windowLayout )
		
	def getFloatField(self,field, *args):
		floatFieldObj = self.floatFields[field]
		value = cmds.floatField( floatFieldObj, query = True, value = True)
		return value
	
	#text field	
	def addTextField(self, fieldName, addButtons = True, default = ''):
		#label
		self.addText( fieldName+':')
		#field
		cmds.columnLayout()	
		validName =  self.convertSpaces(fieldName)
		newField = cmds.textField(validName, width = self.windowX, text = default)
		self.textFields[fieldName] = newField
		cmds.setParent( self.windowLayout )
		#buttons
		if addButtons:
		#cmds.columnLayout()
			cmds.rowColumnLayout( fieldName+'buttons', numberOfColumns = 2 , width = 300, columnSpacing = [(1,50),(2,50)],columnWidth = [(1,70),(2,70)])
			cmds.button(label = 'Add Object', width = 40, command  = partial(self.addSelectedToField, newField), annotation = 'Add the selected object to the field' )
			cmds.button(label = 'Clear Object', width = 40, command  =  partial(self.clearField, newField), annotation = 'Clear the field' )
			cmds.setParent( self.windowLayout )

	def addSelectedToField(self, field, *args):
		temp = cmds.ls( sl=True )
		if len(temp) == 1:
			cmds.textField(field, edit = True, text = temp[0])
		else:
			cmds.error( "Select a single object" )
			
	def clearField(self,field, *args):
		cmds.textField(field, edit = True, text = '')
		
	def getTextField(self,field, *args):
		textField = self.textFields[field]
		value = cmds.textField( textField, query = True, text = True)
		return value
		
	#button
	def addButton(self, buttonLabel, buttonCommand, annotation = '', alignment = 'center'):
		buttonWidth = len(buttonLabel)*10
		buttonLayout = cmds.columnLayout(width = self.windowX )	
		cmds.button(label = buttonLabel, width = buttonWidth, command  = buttonCommand, annotation = annotation )
		if alignment == 'center':
			cmds.columnLayout(buttonLayout , edit = True, columnAttach = ('both', (self.windowX - buttonWidth) /2))
		elif alignment == 'left':
			cmds.columnLayout(buttonLayout , edit = True, columnAttach = ('left', 0))
		elif alignment == 'right':
			cmds.columnLayout(buttonLayout , edit = True, columnAttach = ('left', (self.windowX -buttonWidth) ))
		cmds.setParent( self.windowLayout )

class demoUIExtention(baseUI):

	def __init__(self):
		baseUI.__init__(self,'demoUIExtention', 300, 450)

	def addUIElements(self):
		self.addList('Objects 1')
		self.addText('')
		self.addList('Objects 2')
		self.addText('')
		self.addTextField('Object 1')
		self.addText('')
		self.addTextField('Object 2')
		self.addText('')
		self.addButton('CLICK THIS TO LIST THINGS', self.demo2, 'click to list the objects' )
	
	def demo2(self, *args):
		list1 = self.getListContents('Objects 1')
		print 'list1', list1
		list2 = self.getListContents('Objects 2')
		print 'list2', list2
		field1 = self.getTextField('Object 1')
		print 'field1', field1	
		field2 = self.getTextField('Object 2')
		print 'field2', field2	
		print 'button clicked'

