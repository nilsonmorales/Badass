"""Grab the tips from Options.xml
$Id: extopts.py,v 1.1 2007/01/14 14:07:31 stephen Exp $
Originally ROX-Filer/src/po/tips.py by Thomas Leonard.
"""

from xml.sax import *
from xml.sax.handler import ContentHandler
import os, sys

class Handler(ContentHandler):
	data = ""

	def startElement(self, tag, attrs):
		for x in ['title', 'label', 'end', 'unit']:
			if attrs.has_key(x):
				self.trans(attrs[x])
		self.data = ""
	
	def characters(self, data):
		self.data = self.data + data
	
	def endElement(self, tag):
		data = self.data.strip()
		if data:
			self.trans(data)
		self.data = ""
	
	def trans(self, data):
		data = '\\n'.join(data.split('\n'))
		if data:
			out.write('_("%s")\n' % data.replace('"', '\\"'))

ifname='Options.xml'
ofname='Options_strings'

if len(sys.argv)>2:
	ifname=sys.argv[1]
	ofname=sys.argv[2]
elif len(sys.argv)==2:
	ifname=sys.argv[1]
	
print "Extracting translatable bits from %s..." % os.path.basename(ifname)

out = open(ofname, 'wb')
parse(ifname, Handler())
out.close()
