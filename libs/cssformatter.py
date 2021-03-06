#!/usr/bin/python
# encoding: utf-8
#
# Convert CSS/SASS/SCSS/LESS code to Expanded, Compact or Compressed format.
#
# Usage: 
#     formatter = CssFormater()
#     formatter.run(code, action)
#
# Author: Mutian Wang <mutian@me.com>
#

import re


class CssFormater():

	def __init__(self, indentation='\t', expand_block_break='\n\n'):
		self.indentation = indentation
		self.expand_block_break = expand_block_break


	def run(self, code, action='compact'):
		actFuns = {
			'expand'		: self.expand_rules,
			'expand-bs'		: self.expand_rules,		# expand (break selectors)
			'compact'		: self.compact_rules,
			'compact-bs'	: self.compact_rules,		# compact (break selectors)
			'compact-ns'	: self.compact_ns_rules,	# compact (no spaces)
			'compact-bs-ns'	: self.compact_ns_rules,	# compact (break selectors, no spaces)
			'compress'		: self.compress_rules
		}

		if action not in actFuns:
			return code

		# Comments
		if action == 'compress':
			# Remove comments
			code = re.sub(r'\s*\/\*[\s\S]*?\*\/\s*', '', code)
			
			# Remove comments //
			code = re.sub(r'\/\/.*\n', '', code)
		else:
			# Protect comments
			commentReg = r'[ \t]*\/\*[\s\S]*?\*\/'
			comments = re.findall(commentReg, code)
			code = re.sub(commentReg, '!comment!', code)
			
			# Protect comments //
			comment2Reg = r'\/\/.*\n'
			comments2 = re.findall(comment2Reg, code)
			code = re.sub(comment2Reg, '!comment2!\n', code)


		# Protect strings
		stringReg = r'(content\s*:|[\w-]+\s*=)\s*(([\'\"]).*?\3)\s*'
		strings = re.findall(stringReg, code)
		code = re.sub(stringReg, r'\1!string!', code)
		
		#Protect SASS variables
		sassvarsReg = r'\#\{[^}]*\}'
		sassvars = re.findall(sassvarsReg, code)
		print(sassvars)
		code = re.sub(sassvarsReg, '!sass!', code)

		# Protect urls
		urlReg = r'((?:url|url-prefix|regexp)\([^\)]+\))'
		urls = re.findall(urlReg, code)
		print(urls)
		code = re.sub(urlReg, '!url!', code)
		
		# Protect brackets
		bracketsReg = r'\[[^(\])]*\"[^(")]*\"\]'
		brackets = re.findall(bracketsReg, code)
		code = re.sub(bracketsReg, r'!brackets!', code)

		# Pre process
		code = re.sub(r'\s*([\{\}:;,])\s*', r'\1', code)	# remove \s before and after characters {}:;,
		code = re.sub(r'([\[\(])\s*', r'\1', code)			# remove space inner [ or (
		code = re.sub(r'\s*([\)\]])', r'\1', code)			# remove space inner ) or ]
		# code = re.sub(r'(\S+)\s*([\+>~])\s*(\S+)', r'\1\2\3', code)	# remove \s before and after relationship selectors
		code = re.sub(r',[\d\s\.\#\+>~:]*\{', '{', code)	# remove invalid selectors without \w
		code = re.sub(r'([;,])\1+', r'\1', code)			# remove repeated ;,

		if action != 'compress':
			# Group selector
			if re.search('-bs', action):
				code = self.break_selectors(code)				# break after selectors' ,
			else:
				code = re.sub(r',\s*', ', ', code)			# add space after ,

			# Add space
			if re.search('-ns', action):
				code = re.sub(r', +', ',', code)								# remove space after ,
				code = re.sub(r'\s+!important', '!important', code)				# remove space before !important
			else:
				code = re.sub(r'([A-Za-z-](?:\+_?)?):([^;\{]+[;\}])', r'\1: \2', code)	# add space after properties' :
				code = re.sub(r'\s*!important', ' !important', code)			# add space before !important

		# Process action rules
		code = actFuns[action](code)


		if action == 'compress':
			# Remove last semicolon
			code = code.replace(';}', '}')
			
		else:
			# Add blank line between each block in `expand-bs` mode
			if action == 'expand-bs':
				code = re.sub(r'\}\s*', '}\n\n', code)		# double \n after }

			# Fix comments
			code = re.sub(r'\s*!comment!\s*@', '\n\n!comment!\n@', code)
			code = re.sub(r'\s*!comment!\s*([^\/\{\};]+?)\{', r'\n\n!comment!\n\1{', code)
			code = re.sub(r'\s*\n!comment!', '\n\n!comment!', code)

			# Backfill comments
			for i in comments:
				code = re.sub(r'[ \t]*!comment!', i, code, 1)
			
			# Indent
			code = self.indent_code(code)
			
			# Backfill comments //
			for i in comments2:
				code = re.sub(r'!comment2!', i.strip(), code, 1)
			
		
		
		# Backfill brackets
		for i in brackets:
			code = code.replace('!brackets!', i, 1)
				
		# Backfill urls
		for i in urls:
			code = code.replace('!url!', i, 1)
		
		# Backfill sass
		for i in sassvars:
			code = code.replace('!sass!', i, 1)
			
		# Backfill strings
		for i in range(len(strings)):
			code = code.replace('!string!', strings[i][1], 1)	
		
		# Trim
		code = re.sub(r'^\s*(\S+(\s+\S+)*)\s*$', r'\1', code)

		return code


	# Expand Rules
	def expand_rules(self, code):
		code = re.sub('{', ' {\n', code)									# add space before { and add \n after {

		code = re.sub(';', ';\n', code)										# add \n after ;
		code = re.sub(r';\s*([^\{\};]+?)\{', r';\n\n\1{', code)				# double \n between ; and include selector

		code = re.sub(r'\s*(!comment!)\s*;\s*', r' \1 ;\n', code)			# fix comment before ;
		code = re.sub(r'(:[^:;]+;)\s*(!comment!)\s*', r'\1 \2\n', code)		# fix comment after ;

		code = re.sub(r'\s*\}', '\n}', code)								# add \n before }
		code = re.sub(r'\}\s*', '}' + self.expand_block_break, code)		# add block break after }

		return code


	# Compact Rules
	def compact_rules(self, code):
		code = re.sub('{', ' { ', code)											# add space before and after {
		code = re.sub(r'(@[\w-]*(document|font-feature-values|keyframes|media|supports)[^;]*?\{)\s*', r'\1\n', code)
																				# add \n after @xxx {

		code = re.sub(';', '; ', code)											# add space after ;
		code = re.sub(r'(@(charset|import|namespace).+?;)\s*', r'\1\n', code)	# add \n after @charset & @import
		code = re.sub(r';\s*([^\};]+?\{)', r';\n\1', code)						# add \n before included selector

		code = re.sub(r'\s*(!comment!)\s*;', r' \1 ;', code)					# fix comment before ;
		code = re.sub(r'(:[^:;]+;)\s*(!comment!)\s*', r'\1 \2 ', code)			# fix comment after ;

		code = re.sub(r'\s*\}', ' }', code)										# add space before }
		code = re.sub(r'\}\s*', '}\n', code)									# add \n after }

		return code


	# Compact Rules (no space)
	def compact_ns_rules(self, code):
		code = re.sub(r'(@[\w-]*(document|font-feature-values|keyframes|media|supports)[^;]*?\{)\s*', r'\1\n', code)
																				# add \n after @xxx {

		code = re.sub(r'(@(charset|import|namespace).+?;)\s*', r'\1\n', code)	# add \n after @charset & @import
		code = re.sub(r';\s*([^\};]+?\{)', r';\n\1', code)						# add \n before included selector

		code = re.sub(r'\s*(!comment!)\s*;', r'\1;', code)						# fix comment before ;
		code = re.sub(r'(:[^:;]+;)\s*(!comment!)\s*', r'\1\2', code)			# fix comment after ;

		code = re.sub(r'\}\s*', '}\n', code)									# add \n after }

		return code


	# Compress Rules
	def compress_rules(self, code):
		code = re.sub(r'\s*([\{\}:;,])\s*', r'\1', code)					# remove \s before and after characters {}:;, again
		code = re.sub(r'\s+!important', '!important', code)					# remove space before !important
		code = re.sub(r'((?:@charset|@import)[^;]+;)\s*', r'\1\n', code)	# add \n after @charset & @import

		return code


	# Break after Selector
	def break_selectors(self, code):
		block = code.split('}')
		for i in range(len(block)):

			b = block[i].split('{')
			bLen = len(b)
			for j in range(bLen):

				if j == bLen - 1:
					b[j] = re.sub(r',\s*', ', ', b[j])			# add space after properties' ,
				else:
					s = b[j].split(';')
					sLen = len(s)
					sLast = s[sLen - 1]

					for k in range(sLen - 1):
						s[k] = re.sub(r',\s*', ', ', s[k])		# add space after properties' ,

					# For @document, @media
					if re.search(r'\s*@(document|media)', sLast):
						s[sLen - 1] = re.sub(r',\s*', ', ', sLast)		# add space after @media's ,

					# For mixins
					elif re.search(r'(\(|\))', sLast):
						u = sLast.split(')')
						for m in range(len(u)):
							v = u[m].split('(')
							vLen = len(v)
							if vLen < 2:
								continue
							v[0] = re.sub(r',\s*', ',\n', v[0])
							v[1] = re.sub(r',\s*', ', ', v[1])			# do not break arguments
							u[m] = '('.join(v)
						s[sLen - 1] = ')'.join(u)

					# For selectors
					else:
						s[sLen - 1] = re.sub(r',\s*', ',\n', sLast)		# add \n after selectors' ,

					b[j] = ';'.join(s)

			block[i] = '{'.join(b)

		code = '}'.join(block)

		return code


	# Code Indent
	def indent_code(self, code):
		lines = code.split('\n')
		level = 0
		inComment = False
		outPrefix = ''

		for i in range(len(lines)):
			if not inComment:
				# Quote level adjustment
				validCode = re.sub(r'\/\*[\s\S]*?\*\/', '', lines[i])
				validCode = re.sub(r'\/\*[\s\S]*', '', validCode)
				adjustment = validCode.count('{') - validCode.count('}')

				# Trim
				m = re.match(r'^(\s+)\/\*.*', lines[i])
				if m is not None:
					outPrefix = m.group(1)
					lines[i] = re.sub(r'^' + outPrefix + '(.*)\s*$', r'\1', lines[i])
				else:
					lines[i] = re.sub(r'^\s*(.*)\s*$', r'\1', lines[i])
			else:
				# Quote level adjustment
				adjustment = 0

				# Trim
				lines[i] = re.sub(r'^' + outPrefix + '(.*)\s*$', r'\1', lines[i])
			
			# Is next line in comment?
			commentQuotes = re.findall(r'\/\*|\*\/', lines[i])
			for quote in commentQuotes:
				if inComment and quote == '*/':
					inComment = False
				elif quote == '/*':
					inComment = True

			# Quote level adjustment
			nextLevel = level + adjustment
			thisLevel = level if adjustment > 0 else nextLevel
			level = nextLevel
			
			# Add indentation
			lines[i] = self.indentation * thisLevel + lines[i]
			
			
			#Test for SASS new lines
			if i > 1:
				if lines[i - 1].strip() == "":
					if lines[i].strip() == "}":
						lines[i-1] = "!stopnewline!";		 

		lines	=	list(filter(lambda a: a != "!stopnewline!", lines))
		code = '\n'.join(lines)

		return code
