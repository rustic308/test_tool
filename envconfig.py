import ConfigParser

class envconf(object):
	
	def __init__(self):
		self._zfs={}
		self._parser =ConfigParser.SafeConfigParser(allow_no_value=True)
		
	def load(self,file):
		self._parser.read(file)
		section = "Env"
		for name in self._parser.options(section):
			self._zfs[name] = self._parser.get(section,name)
		return self._zfs

class dbconf(object):
	def __init__(self):
		self._db={}
		self._parser =ConfigParser.SafeConfigParser(allow_no_value=True)
					
	def load(self,file):
		self._parser.read(file)
		section = "DB"
		for name in self._parser.options(section):
			self._db[name] = self._parser.get(section,name)
		return self._db

class fioconf(object):
	def __init__(self):
		#print "enter fioconfig init"
		self._fio={}
		self._parser =ConfigParser.SafeConfigParser(allow_no_value=True)
					
	def load(self,file):
		self._parser.read(file)
		section = "Fio"
		for name in self._parser.options(section):
			self._fio[name] = self._parser.get(section,name)
			if name=="rw":
				rw= self._fio[name]
		print self._fio		
		return rw,self._fio


		
		
def main():
	pass
		
if __name__ == '__main__':
	main()			
			
