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
import os
import cStringIO

#----------------------------------------------------------------------
# TOKEN TYPE
#----------------------------------------------------------------------
CTOKEN_ENDL = 0
CTOKEN_ENDF = 1
CTOKEN_IDENT = 2
CTOKEN_KEYWORD = 3
CTOKEN_STR = 4
CTOKEN_OPERATOR = 5
CTOKEN_INT = 6
CTOKEN_FLOAT = 7
CTOKEN_ERROR = 8

CTOKEN_NAME = { 0:'endl', 1:'endf', 2:'ident', 3:'keyword', 4:'str',
	5:'op', 6:'int', 7:'float', 8:'error' }

#----------------------------------------------------------------------
# CTOKEN Declare
#----------------------------------------------------------------------
class ctoken (object):
	def __init__ (self, mode = 0, value = 0, text = '', row = -1, col = -1):
		self.mode = mode
		self.value = value
		self.text = text
		self.row = row
		self.col = col
		self.fd = ''
		self.source = ''
	def copy (self):
		token = ctoken(self.mode, self.value, self.text, self.line, self.fd)
		token.source = self.source
		return token
	def is_endl (self):
		return self.mode == CTOKEN_ENDL
	def is_endf (self):
		return self.mode == CTOKEN_ENDF
	def is_ident (self):
		return self.mode == CTOKEN_IDENT
	def is_keyword (self):
		return self.mode == CTOKEN_KEYWORD
	def is_str (self):
		return self.mode == CTOKEN_STR
	def is_operator (self):
		return self.mode == CTOKEN_OPERATOR
	def is_int (self):
		return self.mode == CTOKEN_INT
	def is_float (self):
		return self.mode == CTOKEN_FLOAT
	def is_error (self):
		return self.mode == CTOKEN_ERROR
	def __repr__ (self):
		x = '(%s, %s)'%(CTOKEN_NAME[self.mode], repr(self.value))
		return x



#----------------------------------------------------------------------
# CTOKENIZE Declare
#----------------------------------------------------------------------
class ctokenize (object):
	def __init__ (self, fp = ''):
		if type(fp) == type(''):
			fp = cStringIO.StringIO(fp)
		self.fp = fp
		self.reset()
	def reset (self):
		self.ch = ''
		self.un = ''
		self.col = 0
		self.row = 1
		self.eof = 0
		self.state = 0
		self.text = ''
		self.init = 0
		self.error = ''
		self.code = 0
		self.tokens = []
	def getch (self):
		if self.un != '':
			self.ch = self.un
			self.un = ''
			return self.ch
		try: ch = self.fp.read(1)
		except: ch = ''
		self.ch = ch
		if ch == '\n':
			self.col = 1
			self.row += 1
		else:
			self.col += 1
		return self.ch
	def ungetch (self, ch):
		self.un = ch
	def isspace (self, ch):
		return ch in (' ', '\r', '\n', '\t')
	def isalpha (self, ch):
		return ch.isalpha()
	def isalnum (self, ch):
		return ch.isalnum()
	def skipspace (self):
		skip = 0
		while 1:
			if self.ch == '':
				return -1
			if not self.ch in (' ', '\r', '\n', '\t'):
				break
			if self.ch == '\n':
				break
			self.getch()
			skip += 1
		return skip
	def read (self):
		return None
	def next (self):
		if not self.init:
			self.init = 1
			self.getch()
		token = self.read()
		if token != None:
			self.tokens.append(token)
		return token
	def gettokens (self):
		result = []
		while 1:
			token = self.next()
			if token == None:
				if self.code:
					text = '%d: %s'%(self.row, self.error)
					raise SyntaxError(text)
				break
			result.append(token)
			if token.mode == CTOKEN_ENDF:
				break
		return result
	def __iter__ (self):
		return self.gettokens().__iter__()


#----------------------------------------------------------------------
# C/ASM Style Tokenizer
#----------------------------------------------------------------------
class cscanner (ctokenize):

	def __init__ (self, fp = '', keywords = [], casesensitive = False):
		super(cscanner, self).__init__ (fp)
		self.keywords = keywords
		self.casesensitive = casesensitive
		self.ch = ' '
		self.memo = {}
	
	def skipmemo (self):
		memo = ''
		while 1:
			skip = 0
			self.skipspace()
			if self.ch == '':
				break
			if self.ch in (';', '#'):
				skip += 1
				while (self.ch != '\n') and (self.ch != ''):
					memo += self.ch
					self.getch()
					skip += 1
			elif self.ch == '/':
				self.getch()
				if self.ch == '/':
					memo += self.ch
					skip += 1
					while (self.ch != '\n') and (self.ch != ''):
						memo += self.ch
						self.getch()
						skip += 1
				else:
					self.ungetch(self.ch)
					self.ch = '/'
			if skip == 0:
				break
		return memo
	
	def read_string (self):
		token = None
		self.error = ''
		if not self.ch in ('\'', '\"'):
			return None
		mode = (self.ch == '\'') and 1 or 0
		text = ''
		done = -1
		while 1:
			ch = self.getch()
			if ch == '\\':
				self.getch()
				text += '\\' + self.ch
			elif (mode == 0) and (ch == '\''):
				text += '\''
			elif (mode == 1) and (ch == '\"'):
				text == '\"'
			elif (mode == 0) and (ch == '\"'):
				ch = self.getch()
				if ch == '\"':
					text += '\"\"'
				else:
					done = 1
					token = ctoken(CTOKEN_STR, text, text)
					self.text = text
					break
			elif (mode == 1) and (ch == '\''):
				ch = self.getch()
				if ch == '\'':
					text += '\'\''
				else:
					done = 1
					token = ctoken(CTOKEN_STR, text, text)
					self.text = text
					break
			elif ch == '\n':
				self.error = 'EOL while scanning string literal'
				self.code = 1
				break
			elif ch != '':
				text += ch
			else:
				self.error = 'EOF while scanning string literal'
				self.code = 2
				break
		if not token:
			return None
		token.row = self.row
		token.col = self.col
		return token
	
	def read_number (self):
		token = None
		done = -1
		if ((self.ch < '0') or (self.ch > '9')):
			return None
		text = ''
		while self.ch.isalnum() or self.ch == '.':
			text += self.ch
			self.getch()

		pos = len(text)
		while pos > 0:
			ch = text[pos - 1]
			if ch.isdigit() or ch == '.':
				break
			if ch >= 'A' and ch <= 'F':
				break
			if ch >= 'a' and ch <= 'f':
				break
			pos -= 1
		if len(text) - pos > 2:
			self.error = 'number format error'
			self.code = 1
			return None

		if len(text) - pos == 2: ec1, ec2 = text[pos - 2], text[pos - 1]
		elif len(text) - pos == 1: ec1, ec2 = text[pos - 1], 0
		else: ec1, ec2 = 0, 0
		text = text[:pos]

		if text[:2] in ('0x', '0X'):
			try: value = long(text, 16)
			except: 
				self.error = 'bad hex number ' + text
				self.code = 2
				return None
			if value >= -0x80000000L and value <= 0x7fffffffL:
				value = int(value)
			token = ctoken(CTOKEN_INT, value, text)
		elif ec1 == 'h' and ec2 == 0:
			try: value = long(text, 16)
			except:
				self.error = 'bad hex number ' + text
				self.code = 3
				return None
			if value >= -0x80000000L and value <= 0x7fffffffL:
				value = int(value)
			token = ctoken(CTOKEN_INT, value, text)
		elif ec1 == 'b' and ec2 == 0:
			try: value = long(text, 2)
			except:
				self.error = 'bad binary number ' + text
				self.code = 4
				return None
			if value >= -0x80000000L and value <= 0x7fffffffL:
				value = int(value)
			token = ctoken(CTOKEN_INT, value, text)
		elif ec1 == 'q' and ec2 == 0:
			try: value = long(text, 8)
			except:
				self.error = 'bad octal number ' + text
				self.code = 5
				return None
			if value >= -0x80000000L and value <= 0x7fffffffL:
				value = int(value)
			token = ctoken(CTOKEN_INT, value, text)
		else:
			decimal = (not '.' in text) and 1 or 0
			if decimal:
				try: value = long(text, 10)
				except:
					self.error = 'bad decimal number ' + text
					self.code = 6
					return None
				if value >= -0x80000000L and value <= 0x7fffffffL:
					value = int(value)
				token = ctoken(CTOKEN_INT, value, text)
			else:
				try: value = float(text)
				except:
					self.error = 'bad float number ' + text
					self.code = 7
					return None
				token = ctoken(CTOKEN_FLOAT, value, text)
	
		token.row = self.row
		token.col = self.col
		return token

	def read (self):

		memo = self.skipmemo()

		if self.ch == '\n':
			lineno = self.row - 1
			token = ctoken(CTOKEN_ENDL)
			token.row = lineno
			self.memo[lineno] = memo
			memo = ''
			self.getch()
			return token

		if self.ch == '':
			self.eof += 1
			if self.eof > 1:
				return None
			token = ctoken(CTOKEN_ENDF, 0)
			token.row = self.row
			if memo:
				self.memo[self.row] = memo
			return token
		
		# this is a string
		if self.ch in ('\"', '\''):
			row, col = self.row, self.col
			self.code = 0
			self.error = ''
			token = self.read_string()
			if self.code:
				return None
			token.row, token.col = row, col
			return token
		
		issym2f = lambda x: x.isalpha() or (x in ('_', '$', '@'))
		issym2x = lambda x: x.isalnum() or (x in ('_', '$', '@'))

		# identity or keyword
		if issym2f(self.ch):
			row, col = self.row, self.col
			text = ''
			while issym2x(self.ch):
				text += self.ch
				self.getch()
			if self.keywords:
				for i in xrange(len(self.keywords)):
					same = 0
					if self.casesensitive:
						same = (text == self.keywords[i])
					else:
						same = (text.lower() == self.keywords[i].lower())
					if same:
						token = ctoken(CTOKEN_KEYWORD, i, text)
						token.row, token.col = row, col
						return token
			token = ctoken(CTOKEN_IDENT, text, text)
			token.row, token.col = row, col
			return token
		
		# this is a number
		if self.ch >= '0' and self.ch <= '9':
			row, col = self.row, self.col
			self.code = 0
			self.error = ''
			token = self.read_number()
			if self.code:
				return None
			token.row, token.col = row, col
			return token
		
		# this is an operator
		token = ctoken(CTOKEN_OPERATOR, self.ch, self.ch)
		token.row, token.col = self.row, self.col
		self.getch()

		return token



#----------------------------------------------------------------------
# tokenize in single function
#----------------------------------------------------------------------
def tokenize(script):
	scanner = cscanner(script)
	result = [ n for n in scanner ]
	scanner.reset()
	return result



#----------------------------------------------------------------------
# X86 - ASSEMBLY
#----------------------------------------------------------------------
REGNAME = [ 'AH', 'AL', 'BH', 'BL', 'CH', 'CL', 'DH', 'DL', 'AX', 
	'BX', 'CX', 'DX', 'EAX', 'EBX', 'ECX', 'EDX', 'RAX', 'RBX', 'RCX',    
	'RDX', 'CR0', 'CR1', 'CR2', 'CR3', 'DR0', 'DR1', 'DR2', 'DR3', 
	'DR4', 'DR5', 'DR6', 'DR7', 'SI', 'DI', 'SP', 'BP', 'ESI', 
	'EDI', 'ESP', 'EBP', 'RSI', 'RDI', 'RSP', 'RBP', 'TR6', 'TR7', 
	'ST0', 'ST1', 'ST2', 'ST3', 'ST4', 'ST5', 'ST6', 'ST7', 'MM0', 
	'MM1', 'MM2', 'MM3', 'MM4', 'MM5', 'MM6', 'MM7', 'MM8', 'MM9', 
	'MM10', 'MM11', 'MM12', 'MM13', 'MM14', 'MM15', 'XMM0', 'XMM1', 
	'XMM2', 'XMM3', 'XMM4', 'XMM5', 'XMM6', 'XMM7', 'XMM8', 'XMM9', 
	'XMM10', 'XMM11', 'XMM12', 'XMM13', 'XMM14', 'XMM15', 'R0', 'R1', 
	'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 
	'R12', 'R13', 'R14', 'R15' ]

def reginfo(name):
	name = name.lower()
	if name[:2] == 'mm':
		return 8
	if name[:3] == 'xmm':
		return 16
	if name[:1] == 'r' and name[1:].isdigit():
		return 8
	if name[:2] in ('cr', 'dr'):
		return 4
	if name[:2] in ('st', 'tr'):
		return 8
	if len(name) == 2:
		if name[0] == 'r':
			return 8
		if name[1] in ('h', 'l'):
			return 1
		if name[1] in ('x', 'i', 'p'):
			return 2
		raise SyntaxError('unknow register ' + name)
	if len(name) == 3:
		if name[2] in ('x', 'p', 'i'):
			if name[0] == 'e':
				return 4
			if name[0] == 'r':
				return 8
			raise SyntaxError('unknow register ' + name)
	return 0

REGSIZE = { }

for reg in REGNAME:
	REGSIZE[reg] = reginfo(reg)

regsize = lambda reg: REGSIZE[reg.upper()]
isreg = lambda reg: (reg.upper() in REGSIZE)


instreplace = {
	"cbw":"cbtw",
	"cdq":"cltd",
	"cmpsd":"cmpsl",
	"codeseg":".text",
	"cwd":"cwtd",
	"cwde":"cwtl",
	"dataseg":".data",
	"db":".byte",
	"dd":".int",
	"dw":".short",
	"emit":".byte",
	"_emit":".byte",
	"insd":"insl",
	"lodsd":"lodsl",
	"movsd":"movsl",
	"movsx":"movs",
	"movzx":"movz",
	"outsd":"outsl",
	"public":".globl",
	"scasd":"scasl",
	"stosd":"stosl",
	}

prefix = [ 'lock', 'rep', 'repne', 'repnz', 'repe', 'repz' ]


#----------------------------------------------------------------------
# coperand
#----------------------------------------------------------------------
O_REG	= 0			# 寄存器
O_IMM	= 1			# 立即数字
O_MEM	= 2			# 内存
O_LABEL	= 3			# 标识，可能是变量也可能是跳转地址

class coperand (object):
	def __init__ (self, tokens = None):
		self.mode = -1
		self.reg = ''						# 默认寄存器
		self.base = ''						# 寻址：基址寄存器
		self.index = ''						# 寻址：索引寄存器
		self.scale = 0						# 寻址：放大倍数
		self.offset = 0						# 寻址：偏移量
		self.segment = ''					# 段地址
		self.immediate = 0					# 立即数字
		self.label = ''						# 变量或者跳转地址
		self.size = 0						# 数据大小
		if tokens != None: 
			self.parse(tokens)
		self.name = 'operand'
	def reset (self):
		self.reg = ''
		self.base = ''
		self.index = ''
		self.scale = 0
		self.offset = 0
		self.immediate = 0
		self.segment = ''
		self.label = ''
		self.size = 0
	def parse (self, tokens):
		if type(tokens) == type(''):
			tokens = tokenize(tokens)
		tokens = [ n for n in tokens ]
		while len(tokens) > 0:
			if not tokens[-1].mode in (CTOKEN_ENDF, CTOKEN_ENDL):
				break
			tokens.pop()
		self.reset()
		if len(tokens) >= 2:
			t1 = tokens[0]
			t2 = tokens[1]
			if t2.mode == CTOKEN_IDENT and t2.value.lower() == 'ptr':
				if t1.mode == CTOKEN_IDENT:
					size = t1.value.lower()
					if size == 'byte': self.size = 1
					elif size == 'word': self.size = 2
					elif size == 'dword': self.size = 4
					elif size == 'qword': self.size = 8
					if self.size != 0:
						tokens = tokens[2:]
		if len(tokens) == 0:
			raise SyntaxError('expected operand token')
		head = tokens[0]
		tail = tokens[-1]
		if head.mode == CTOKEN_INT:			# 如果是立即数
			self.mode = O_IMM
			self.immediate = head.value
		elif head.mode == CTOKEN_IDENT:		# 寄存器或标识
			if isreg(head.value):			# 如果是寄存器
				self.mode = O_REG
				self.reg = head.value
				self.size = regsize(self.reg)
			else:
				self.mode = O_LABEL			# 如果是标识
				self.label = head.value
		elif head.mode == CTOKEN_OPERATOR:	# 如果是符号
			if head.value == '[':			# 如果是内存
				self.mode = O_MEM
				if tail.mode != CTOKEN_OPERATOR or tail.value != ']':
					raise SyntaxError('bad memory operand')
				self.__parse_memory(tokens)
			else:
				raise SyntaxError('bad operand descript ' + repr(head.value))
		else:
			raise SyntaxError('bad operand desc')
		return 0
	def __parse_memory (self, tokens):
		tokens = tokens[1:-1]
		if len(tokens) == 0:
			raise SyntaxError('memory operand error')
		self.scale = 1
		self.index = ''
		self.offset = 0
		self.base = ''
		segments = [ 'cs', 'ss', 'ds', 'es', 'fs', 'gs' ]
		pos = -1
		for i in xrange(len(tokens)):
			token = tokens[i]
			if token.mode == CTOKEN_OPERATOR and token.value == ':':
				pos = i
				break
		if pos >= 0 and pos < len(tokens):		# 如果覆盖段地址
			if pos == 0 or pos == len(tokens) - 1:
				raise SyntaxError('memory operand segment error')
			t1 = tokens[pos - 1]
			tokens = tokens[:pos - 1] + tokens[pos + 1:]
			if t1.mode != CTOKEN_IDENT:
				raise SyntaxError('memory operand segment bad')
			seg = t1.value.lower()
			if not seg in segments:
				raise SyntaxError('memory operand segment unknow')
			self.segment = seg
		pos = -1
		for i in xrange(len(tokens)):
			token = tokens[i]
			if token.mode == CTOKEN_OPERATOR and token.value == '*':
				pos = i
				break
		if pos >= 0 and pos < len(tokens):		# 如果有乘号
			if pos == 0 or pos == len(tokens) - 1:
				raise SyntaxError('memory operand error (bad scale)')
			t1 = tokens[pos - 1]
			t2 = tokens[pos + 1]
			tokens = tokens[:pos - 1] + tokens[pos + 2:]
			if t1.mode == CTOKEN_IDENT and t2.mode == CTOKEN_INT:
				pass
			elif t1.mode == CTOKEN_INT and t2.mode == CTOKEN_IDENT:
				t1, t2 = t2, t1
			else:
				raise SyntaxError('memory operand error (scale error)')
			if not isreg(t1.value):
				raise SyntaxError('memory operand error (no index register)')
			self.index = t1.value
			self.scale = (t2.value)
			if not self.scale in (1, 2, 4, 8):
				raise SyntaxError('memory operand error (bad scale number)')
		#for token in tokens: print token,
		#print ''
		for token in tokens:
			if token.mode == CTOKEN_IDENT and isreg(token.value):
				if self.base == '':
					self.base = token.value
				elif self.index == '':
					self.index = token.value
				else:
					print token
					raise SyntaxError('memory operand error (too many regs)')
			elif token.mode == CTOKEN_INT:
				if self.offset == 0:
					self.offset = token.value
				else:
					raise SyntaxError('memory operand error (too many offs)')
			elif token.mode == CTOKEN_OPERATOR and token.value == '+':
				pass
			else:
				raise SyntaxError('operand token error ' + repr(token))
		return 0
	def info (self):
		if self.mode == O_REG:
			return 'reg:%s'%self.reg
		elif self.mode == O_IMM:
			return 'imm:%d'%self.immediate
		elif self.mode == O_LABEL:
			return 'label:%s'%self.label
		data = []
		if self.base:
			data.append(self.base)
		if self.index:
			if self.scale == 1:
				data.append('%s'%self.index)
			else:
				data.append('%s * %d'%(self.index, self.scale))
		if self.offset != 0:
			data.append('0x%x'%(self.offset))
		size = ''
		if self.size == 1: size = '8'
		elif self.size == 2: size = '16'
		elif self.size == 4: size = '32'
		elif self.size == 8: size = '64'
		return 'mem%s:[%s]'%(size, ' + '.join(data))
	def translate (self, inline = 0):
		prefix = r'%'
		if inline: prefix = r'%%'
		if self.mode == O_REG:
			return prefix + self.reg
		if self.mode == O_IMM:
			return '$' + hex(self.immediate)
		if self.mode == O_LABEL:
			return self.label
		text = ''
		base = self.base and (prefix + self.base) or ''
		index = self.index and (prefix + self.index) or ''
		if not self.index:
			text = '(%s)'%base
		else:
			text = '(%s,%s,%d)'%(base, index, self.scale)
		if self.offset:
			text = '0x%x%s'%(self.offset, text)
		if self.segment:
			text = '%s:%s'%(self.segment, text)
		return text
	def __repr__ (self):
		return self.info() + ' -> ' + self.translate()



#----------------------------------------------------------------------
# cencoding
#----------------------------------------------------------------------
class cencoding (object):

	def __init__ (self, tokens = None):
		self.reset()
		if tokens != None:
			self.parse(tokens)
		self.name = 'cencoding'
	
	def reset (self):
		self.label = ''
		self.prefix = ''
		self.instruction = ''
		self.operands = []
		self.tokens = None
		self.empty = False
		return 0

	def parse (self, tokens = None):
		if type(tokens) == type(''):
			tokens = tokenize(tokens)
		tokens = [ n for n in tokens ]
		while len(tokens) > 0:
			if not tokens[-1].mode in (CTOKEN_ENDF, CTOKEN_ENDL):
				break
			tokens.pop()
		if len(tokens) == 0:
			self.empty = True
			return 0
		self.reset()
		self.tokens = tokens
		self.__parse_label()
		self.__parse_prefix()
		self.__parse_instruction()
		self.__parse_operands()
		self.__update()
		self.tokens = None
		return 0

	def __parse_label (self):
		if len(self.tokens) < 2:
			return 0
		t1, t2 = self.tokens[:2]
		if t2.mode == CTOKEN_OPERATOR and t2.value == ':':
			if t1.mode != CTOKEN_IDENT:
				raise SyntaxError('error label type')
			self.label = t1.value
			self.tokens = self.tokens[2:]
		return 0
	
	def __parse_prefix (self):
		prefix = [ 'lock', 'rep', 'repne', 'repnz', 'repe', 'repz' ]
		segments = [ 'cs', 'ss', 'ds', 'es', 'fs', 'gs' ]
		while len(self.tokens) >= 1:
			t1 = self.tokens[0]
			if t1.mode != CTOKEN_IDENT:
				break
			text = t1.value.lower()
			if (not text in prefix) and (not text in segments):
				break
			self.prefix += ' ' + text
			self.prefix = self.prefix.strip(' ')
			self.tokens = self.tokens[1:]
		return 0
	
	def __parse_instruction (self):
		if len(self.tokens) < 1:
			return 0
		t1 = self.tokens[0]
		self.tokens = self.tokens[1:]
		if t1.mode != CTOKEN_IDENT:
			raise SyntaxError('instruction type error')
		self.instruction = t1.value
		return 0
	
	def __parse_operands (self):
		operands = []
		while len(self.tokens) > 0:
			size = len(self.tokens)
			pos = size
			for i in xrange(size):
				if self.tokens[i].mode == CTOKEN_OPERATOR:
					if self.tokens[i].value == ',':
						pos = i
						break
			operands.append(self.tokens[:pos])
			self.tokens = self.tokens[pos + 1:]
		for tokens in operands:
			n = coperand(tokens)
			self.operands.append(n)
		operands = None
		return 0
	
	def __update (self):
		self.size = 0
		for operand in self.operands:
			if operand.size > self.size:		
				self.size = operand.size
		if self.prefix == '' and self.instruction == '':
			if len(self.operands) == 0:
				self.empty = True
		return 0

	def translate_instruction (self):
		lower = self.instruction.islower()
		instruction = self.instruction.lower()
		if instruction == 'align':
			return '.align'
		if instruction in instreplace:
			instruction = instreplace[instruction]
		postfix = False
		if len(self.operands) == 1:
			o = self.operands[0]
			if o.mode == O_MEM:
				postfix = True
			elif o.mode == O_LABEL:
				postfix = True
		elif len(self.operands) == 2:
			o1, o2 = self.operands[:2]
			if o1.mode == O_IMM and o2.mode == O_MEM:
				postfix = True
			if o1.mode == O_MEM and o2.mode == O_IMM:
				postfix = True
			if o1.mode == O_IMM and o2.mode == O_LABEL:
				postfix = True
			if o1.mode == O_LABEL and o2.mode == O_IMM:
				postfix = True
		if postfix:
			if self.size == 1:
				instruction += 'b'
			elif self.size == 2:
				instruction += 'w'
			elif self.size == 4:
				instruction += 'l'
			elif self.size == 8:
				instruction += 'q'
		if not lower:
			instruction = instruction.upper()
		return instruction

	def translate_operand (self, id, inline = 0):
		desc = []
		if self.instruction.lower() == 'align':
			size = 4
			if len(self.operands) > 0:
				op = self.operands[0]
				if op.mode == O_IMM:
					size = op.immediate
			if id == 0:
				return '%d, 0x90'%size
			return ''
		if id < 0 or id >= len(self.operands):
			raise KeyError('operand id out of range')
		text = self.operands[id].translate(inline)
		return text

	def __repr__ (self):
		text = ''
		if self.label:
			text += '%s: '%self.label
		if self.prefix:
			text += '%s '%self.prefix
		text += self.translate_instruction()
		text += ' '
		text += self.translate_operands()
		return text


#----------------------------------------------------------------------
# csynth
#----------------------------------------------------------------------
class csynthesis (object):
	
	def __init__ (self, source = None):
		self.reset()
		if source != None:
			self.parse(source)
		self.name = 'csynthesis'
	
	def reset (self):
		self.source = ''
		self.tokens = []
		self.encoding = []
		self.labels = {}
		self.references = {}
		self.lines = []
		self.memos = {}
		self.table = []
		self.vars = {}
		self.maps = {}
		self.variables = []
		self.registers = {}
		self.amd64 = False
		self.size = 0
		self.error = ''
	
	def parse (self, source = None):
		self.reset()
		if self.__tokenizer(source) != 0:
			return -1
		if self.__encoding() != 0:
			return -2
		if self.__analyse() != 0:
			return -3
		return 0
	
	def __tokenizer (self, source = None):
		scanner = cscanner(source)
		tokens = []
		while 1:
			token = scanner.next()
			if token == None:
				text = '%d: %s'%(scanner.row, scanner.error)
				self.error = text
				return -1
			tokens.append(token)
			if token.mode == CTOKEN_ENDF:
				break
		self.tokens = [ n for n in tokens ]
		while len(tokens) > 0:
			size = len(tokens)
			pos = size - 1
			for i in xrange(size):
				if tokens[i].mode == CTOKEN_ENDL:
					pos = i
					break
			self.lines.append(tokens[:pos + 1])
			tokens = tokens[pos + 1:]
		for i in xrange(len(self.lines)):
			lineno = i + 1
			if lineno in scanner.memo:
				self.memos[i] = scanner.memo[lineno].strip('\r\n\t ')
			else:
				self.memos[i] = ''
		scanner = None
		return 0

	def __encoding (self):
		lineno = 1
		for tokens in self.lines:
			try: 
				encoding = cencoding(tokens)
			except SyntaxError, e:
				text = '%d: %s'%(lineno, e)
				self.error = text
				return -1
			self.encoding.append(encoding)
			lineno += 1
		if len(self.lines) != len(self.encoding):
			raise Exception('core fault')
		return 0
	
	def __analyse (self):
		self.size = len(self.lines)
		index = 0
		amd64 = ('rax', 'rbx', 'rcx', 'rdx', 'rdi', 'rsi', 'rbp', 'rsp')
		for i in xrange(self.size):
			encoding = self.encoding[i]
			if encoding.label:
				index += 1
				self.labels[encoding.label] = (i, index)
		varlist = []
		for i in xrange(self.size):
			encoding = self.encoding[i]
			for j in xrange(len(encoding.operands)):
				operand = encoding.operands[j]
				if operand.mode == O_LABEL:
					if not operand.label in self.labels:
						varlist.append((operand.label, i, j))
					else:
						desc = self.references.get(operand.label, [])
						desc.append((i, j))
						self.references[operand.label] = desc
				elif operand.mode == O_REG:
					reg = operand.reg.lower()
					self.registers[reg] = 1
					if reg in amd64:
						self.amd64 = True
		vartable = []
		for var, line, pos in varlist:
			if pos == 0: vartable.append((var, line, pos))
		for var, line, pos in varlist:
			if pos != 0: vartable.append((var, line, pos))
		names = {}
		for i in xrange(len(vartable)):
			var, line, pos = vartable[i]
			desc = self.vars.get(var, [])
			if len(desc) == 0:
				index = len(names)
				names[var] = index
				self.table.append((var, line, pos, index))
				writable = pos == 0 and 1 or 0
				self.maps[var] = (index, writable)
				self.variables.append((index, var, writable))
			else:
				index = names[var]
			desc.append((var, line, pos, index))
			self.vars[var] = desc
		indent1 = 0
		indent2 = 0
		for i in xrange(self.size):
			encoding = self.encoding[i]
			encoding.inst = encoding.translate_instruction()
			if encoding.label and (not encoding.empty):
				if len(encoding.label) > indent1:
					indent1 = len(encoding.label)
			if len(encoding.inst) > indent2:
				indent2 = len(encoding.inst)
		self.indent1 = indent1 + 2
		self.indent2 = indent2
		if self.indent1 < 4: self.indent1 = 4
		if self.indent2 < 4: self.indent2 = 4
		return 0
	
	def get_label (self, lineno, clabel = 0):
		if lineno < 0 or lineno >= self.size:
			raise KeyError('line number out of range')
		encoding = self.encoding[lineno]
		if encoding.label == '':
			return ''
		if clabel == 0:
			return encoding.label + ':'
		line, index = self.labels[encoding.label]
		return '%d:'%index
	
	def get_instruction (self, lineno):
		if lineno < 0 or lineno >= self.size:
			raise KeyError('line number out of range')
		encoding = self.encoding[lineno]
		if encoding.empty:
			return ''
		source = encoding.prefix + ' ' + encoding.inst
		source = source.strip(' ')
		return source
	
	def get_operand (self, lineno, id, clabel = 0, inline = 0):
		if lineno < 0 or lineno >= self.size:
			raise KeyError('line number out of range')
		encoding = self.encoding[lineno]
		if id < 0 or id >= len(encoding.operands):
			raise KeyError('operand id out of range')
		operand = encoding.operands[id]
		if operand.mode in (O_IMM, O_REG, O_MEM):
			return operand.translate(inline)
		label = operand.label
		if label in self.labels:	# this is a jmp label
			if not clabel:
				return label
			line, index = self.labels[label]
			if line <= lineno:
				return '%db'%index
			return '%df'%index
		if label in self.vars:		# this is a variable
			id, writable = self.maps[label]
			return '%%%d'%id
		return '$' + label

	def synthesis (self, lineno, clabel = 0, inline = 0, align = 0):
		if lineno < 0 or lineno >= self.size:
			raise KeyError('line number out of range')
		encoding = self.encoding[lineno]
		source = self.get_label(lineno, clabel)
		# 内容缩进
		indent = self.indent1
		if clabel: 
			indent = len(self.labels) + 2
		indent = ((indent + 1) / 2) * 2
		source = source.ljust(indent)
		# 没有指令
		if encoding.empty:
			return source
		instruction = self.get_instruction(lineno)
		if align:
			indent = ((self.indent2 + 3) / 4 ) * 4
			instruction = instruction.ljust(indent)
		source += instruction + ' '
		if encoding.instruction.lower() == 'align':
			size = 4
			if len(encoding.operands) > 0:
				operand = encoding.operands[0]
				if operand.mode == O_IMM:
					size = operand.immediate
			source += '%d, 0x90'%size
		elif encoding.inst.lower() in ('.byte', '.int', '.short'):
			operands = []
			for i in xrange(len(encoding.operands)):
				op = encoding.operands[i]
				text = hex(op.immediate)
				operands.append(text)
			source += ', '.join(operands)
		else:
			operands = []
			for i in xrange(len(encoding.operands)):
				op = self.get_operand(lineno, i, clabel, inline)
				operands.append(op)
			operands.reverse()
			source += ', '.join(operands)
		source = source.rstrip(' ')
		return source
	
	def getvars (self, mode = 0):
		vars = []
		for id, name, writable  in self.variables:
			if mode == 0 and writable != 0:
				vars.append('"=m"(%s)'%name)
			elif mode == 1 and writable == 0:
				vars.append('"m"(%s)'%name)
		text = ', '.join(vars)
		return text

	def getregs (self):
		if self.amd64:
			return '"rsi", "rdi", "rax", "rbx", "rcx", "rdx"'
		return '"esi", "edi", "eax", "ebx", "ecx", "edx"'


#----------------------------------------------------------------------
# intel2gas
#----------------------------------------------------------------------
class CIntel2GAS (object):
	
	def __init__ (self):
		self.synthesis = csynthesis()
		self.config = {}
		self.config['align'] = 0
		self.config['inline'] = 0
		self.config['clabel'] = 0
		self.config['memo'] = 0
		self.error = ''
		self.lines = []
		self.output = []
		self.option()
	
	def option (self, align = 1, inline = 1, clabel = 1, memo = 1):
		self.config['align'] = align
		self.config['clabel'] = clabel
		self.config['inline'] = inline
		self.config['memo'] = memo
		return 0

	def __parse (self, source, clabel, inline, align):
		self.lines = []
		self.output = []
		self.memos = {}
		retval = self.synthesis.parse(source)
		self.error = self.synthesis.error
		if retval != 0:
			return retval
		for i in xrange(self.synthesis.size):
			text = self.synthesis.synthesis(i, clabel, inline, align)
			self.lines.append(text)
			memo = self.synthesis.memos[i].strip('\r\n\t ')
			if memo[:1] == ';': memo = memo[1:]
			memo = memo.strip('\r\n\t ')
			if memo[:2] != '//' and memo != '': memo = '//' + memo
			self.memos[i] = memo
		self.maxsize = 0
		for text in self.lines:
			if len(text) > self.maxsize:
				self.maxsize = len(text)
		self.maxsize = ((self.maxsize + 6) / 2) * 2
		return 0

	def intel2gas (self, source):
		self.lines = []
		self.output = []
		clabel = self.config['clabel']
		inline = self.config['inline']
		align = self.config['align']
		memo = self.config['memo']
		retval = self.__parse(source, clabel, inline, align)
		prefix = ''
		if retval != 0:
			return retval
		if inline:
			self.output.append('__asm__ __volatile__ (')
			prefix = '  '
		for i in xrange(self.synthesis.size):
			line = self.lines[i]
			if line.strip('\r\n\t ') == '':
				if self.memos[i] == '' or memo == 0:
					if inline:
						self.output.append(prefix + '')
					else:
						self.output.append('')
				else:
					self.output.append(prefix + self.memos[i])
			else:
				if inline:
					line = '"' + line + '\\n"'
				if self.memos[i] and memo:
					line = line.ljust(self.maxsize) + self.memos[i]
				self.output.append(prefix + line)
		if inline:
			self.output.append('  :' + self.synthesis.getvars(0))
			self.output.append('  :' + self.synthesis.getvars(1))
			self.output.append('  :"memory", ' + self.synthesis.getregs())
			self.output.append(');')
		return 0


#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------
def main ():
	align = 0
	memo = 0
	clabel = 0
	inline = 0
	for argv in sys.argv[1:]:
		argv = argv.lower()
		if argv == '-i': inline = 1
		if argv == '-a': align = 1
		if argv == '-l': clabel = 1
		if argv == '-m': memo = 1
	source = sys.stdin.read()
	intel2gas = CIntel2GAS()
	intel2gas.option(align, inline, clabel, memo)
	if intel2gas.intel2gas(source) != 0:
		sys.stderr.write('error: ' + intel2gas.error + '\n')
		return -1
	for line in intel2gas.output:
		print line
	return 0


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
	def test1():
		scanner = cscanner(open('intel2gas.asm'))
		for token in scanner:
			print token
		print REGSIZE
	def test2():
		print coperand('12')
		print coperand('loop_pixel')
		print coperand('eax')
		print coperand('ebx')
		print coperand('ax')
		print coperand('al')
		print coperand('[eax]')
		print coperand('[eax + ebx]')
		print coperand('[eax + 2*ebx]')
		print coperand('[eax + 2*ebx + 1]')
		print coperand('[eax + ebx + 3]')
		print coperand('[eax + 1]')
		print coperand('[eax*2]')
		print coperand('[eax*2 + 1]')
		print coperand('dword ptr [eax]')
		print coperand('word ptr [eax+ebx+3]')
		print coperand('byte ptr [es:eax+ebx*4+3]')
		print coperand('byte ptr abc')
		return 0
	def test3():
		synth = csynth(open('intel2gas.asm'))
		for i in xrange(len(synth.encoding)):
			print '%d: '%(i + 1), synth.encoding[i]
		print synth.labels
		print synth.references
		print synth.vars
		print synth.variables
		return 0
	def test4():
		synth = csynthesis()
		if synth.parse(open('intel2gas.asm')) != 0:
			print 'error', synth.error
			return 0
		for i in xrange(len(synth.encoding)):
			print '%3d: '%(i + 1), synth.synthesis(i, 1, 1, 1)
		print synth.getvars(0)
		print synth.getvars(1)
		print synth.indent1, synth.indent2
	def test5():
		intel2gas = CIntel2GAS()
		if intel2gas.intel2gas(open('intel2gas.asm')):
			return -1
		for line in intel2gas.output:
			print line
		return 0
	#test5()
	main()


