#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
# 
# intel2gas.py - intel assembly to at&t format
#
# NOTE:
# for more information, please see the readme file
#
#======================================================================
import sys, time
import intel2gas

from Tkinter import *


class Intel2GUI (Frame):
	
	def __init__ (self, parent=None, text='Intel2GAS', file=None):
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)                 # make me expandable
		self.makewidgets()
		self.intel2gas = intel2gas.CIntel2GAS()
	
	def settext (self, widget, text):
		widget.delete('1.0', END)
		widget.insert('1.0', text)
		widget.mark_set(INSERT, '1.0')
	
	def gettext(self, widget): 
		return widget.get('1.0', END+'-1c') 

	def makewidgets (self):
		form = Frame(self, width=800, height=600)
		botm = Frame(self)
		left = Frame(form)
		rite = Frame(form)
		botm.pack(side=BOTTOM, expand=YES, fill=X)
		form.pack(side=TOP, expand=YES, fill=BOTH)
		left.pack(side=LEFT, expand=YES, fill=BOTH, padx=2, pady=2)
		rite.pack(side=RIGHT, expand=YES, fill=BOTH, padx=2, pady=2)
		text1 = Text(left, relief=SUNKEN, width=40, height=25, wrap='none')
		text2 = Text(rite, relief=SUNKEN, width=40, height=25, wrap='none')
		sbar1 = Scrollbar(left)
		sbar2 = Scrollbar(rite)
		sbar3 = Scrollbar(left, orient='horizontal')
		sbar4 = Scrollbar(rite, orient='horizontal')
		text1.config(yscrollcommand=sbar1.set)  
		text2.config(yscrollcommand=sbar2.set)
		text1.config(xscrollcommand=sbar3.set)
		text2.config(xscrollcommand=sbar4.set)
		sbar1.config(command=text1.yview) 
		sbar2.config(command=text2.yview) 
		sbar3.config(command=text1.xview)
		sbar4.config(command=text2.xview)
		sbar1.pack(side=RIGHT, fill=Y)
		sbar2.pack(side=RIGHT, fill=Y)
		sbar3.pack(side=BOTTOM, fill=X)
		sbar4.pack(side=BOTTOM, fill=X)
		text1.pack(side=LEFT, expand=YES, fill=BOTH)
		text2.pack(side=LEFT, expand=YES, fill=BOTH)
		self.text1 = text1
		self.text2 = text2
		text3 = Text(botm, width=40, height=4)
		text3.pack(side=TOP, expand=YES, fill=X, padx=2, pady=2)
		self.text3 = text3
		self.int1 = IntVar()
		self.int2 = IntVar()
		self.int3 = IntVar()
		self.int4 = IntVar()
		cb1 = Checkbutton(botm, text = 'inline mode', variable=self.int1)
		cb2 = Checkbutton(botm, text = 'operands align', variable=self.int2)
		cb3 = Checkbutton(botm, text = 'convert label', variable=self.int3)
		cb4 = Checkbutton(botm, text = 'including memo', variable=self.int4)
		cb1.pack(side=LEFT, padx=2, pady=2)
		cb2.pack(side=LEFT, padx=2, pady=2)
		cb3.pack(side=LEFT, padx=2, pady=2)
		cb4.pack(side=LEFT, padx=2, pady=2)
		self.int1.set(1)
		self.int2.set(1)
		self.int3.set(1)
		self.int4.set(0)
		font1 = ('Courier New', 10, 'bold')
		font2 = ('Courier New', 10, '')
		btn = Button(botm, text='Intel2GAS', command=self.convert, padx=2, pady=2)
		btn.pack(side=RIGHT, padx=2, pady=2)
		btn.config(font=font1)
		text = 'HELP: type intel format assembly in the left edit box'
		self.settext(self.text3, text)
		btn = Button(botm, text='Clear Code', command=self.clear, padx=2, pady=2)
		btn.pack(side=RIGHT, padx=2, pady=2)
		btn.config(font=font1)
		self.text1.focus()

	def convert (self):
		self.settext(self.text2, '')
		self.settext(self.text3, '')
		inline = self.int1.get()
		align = self.int2.get()
		clabel = self.int3.get()
		memo = self.int4.get()
		self.intel2gas.option(align, inline, clabel, memo)
		source = self.gettext(self.text1)
		if type(source) == type(u''):
			source = source.encode('gbk')
		import cStringIO
		sio = cStringIO.StringIO(source)
		if self.intel2gas.intel2gas(sio) != 0:
			self.settext(self.text3, 'error: ' + self.intel2gas.error)
			lineno = int(self.intel2gas.error.split(':')[0])
			self.text1.tag_add(SEL, '%d.0'%lineno, '%d.0'%(lineno + 1))
			self.text1.mark_set(INSERT, '%d.0'%lineno) 
			return -1
		text = '\r\n'.join(self.intel2gas.output)
		self.settext(self.text2, text)
		return 0
	
	def clear (self):
		self.settext(self.text1, '')
		self.settext(self.text2, '')
		self.settext(self.text3, '')
		self.text1.focus()


def demo4():
	fields = 'Name', 'Job', 'Pay'

	def fetch(variables):
		for variable in variables:
			print 'Input => "%s"' % variable.get()      # get from var

	def makeform(root, fields):
		form = Frame(root)                              # make outer frame
		left = Frame(form)                              # make two columns
		rite = Frame(form)
		form.pack(fill=X) 
		left.pack(side=LEFT)
		rite.pack(side=RIGHT, expand=YES, fill=X)       # grow horizontal

		variables = []
		for field in fields:
			lab = Label(left, width=5, text=field)      # add to columns
			ent = Entry(rite)
			lab.pack(side=TOP)
			ent.pack(side=TOP, fill=X)                  # grow horizontal
			var = StringVar()
			ent.config(textvariable=var)                # link field to var
			var.set('enter here')
			variables.append(var)
		return variables

	root = Tk()
	vars = makeform(root, fields)
	Button(root, text='Fetch', 
				 command=(lambda v=vars: fetch(v))).pack(side=LEFT)
	#Quitter(root).pack(side=RIGHT)
	root.bind('<Return>', (lambda event, v=vars: fetch(v)))   
	root.mainloop()
	return 0

if __name__ == '__main__':
	def demo1():
		root = Tk()
		root.title('LINWEI')
		labelfont = ('times', 20, 'bold')
		widget = Label(root, text = 'Hello config world')
		widget.config(bg='black', fg='yellow')
		widget.config(font = labelfont)
		widget.config(height = 3, width = 20)
		widget.pack(expand = YES, fill = BOTH)
		root.mainloop()
	def demo2():
		widget = Button(text='Spam', padx=10, pady=10)
		widget.pack(padx=20, pady=20)
		widget.config(cursor='gumby')
		widget.config(bd=8, relief=RAISED)
		widget.config(bg='dark green', fg='white')
		widget.config(font=('helvetica', 20, 'underline italic'))
		mainloop()
	def demo3():
		def fetch():
			print 'Input => "%s"' % ent.get()              # get text
		root = Tk()
		ent = Entry(root)
		ent.insert(0, 'Type words here')                   # set text
		ent.pack(side=TOP, fill=X)                         # grow horiz
		ent.focus()                                        # save a click
		ent.bind('<Return>', (lambda event: fetch()))      # on enter key
		btn = Button(root, text='Fetch', command=fetch)    # and on button 
		btn.pack(side=LEFT)
		#Quitter(root).pack(side=RIGHT)
		root.mainloop()
	def demo5():
		root = Tk()
		root.title('Intel2GAS (Assembly format convertion from Intel to GNU AS)')
		Intel2GUI(root)
		root.mainloop()
	demo5()


