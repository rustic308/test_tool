import shelve
#import subprocess
from fabric.api import *
from envconfig import *

class zfs(object):
	def __init__(self,dbconf):
		self._config = 'testconfig'
		self.__poolArgs = {}
		self.__volArgs = {}
		self.__volCreateArgs = {}
		self._zfsparam={}
		self._disk={}
		self._poolname = 'testpool'
		self._zfsname=self._poolname+"/z1"
		self._zvolname=self._poolname+"/lun1"
		self._dbconf = dbconf

	def createzpool(self,env_num,prot_type):
		with settings(
			hide('stdout'),
			host_string=self._dbconf['server_host'],password=self._dbconf['server_password'],
			warn_only=True
		):
			zpool_config = envconf().load('config/env_config%d'%env_num)
			poolname = self._poolname
			param = dict(zpool_config)
			self._zfsparam = dict(zpool_config)
			#print self._zfsparam
			disklist=[]
			self._disk = self.transformslotname()
			for slot in param['disk'].split():
				disklist.append(self._disk[slot])

			# generate zpool create command
			cmd = self.createcmd(param['pooltype'],param['poolprop'],poolname,disklist)
			run(cmd)
			# add qlog 
			run('zpool add %s qlog ramdisk0'%self._poolname)
			if param['globalcache']:
				for cache in param['globalcache'].split():
					print cache
					if cache.startswith('h.'):
						geom_cache = self._disk[cache]
					else:
						geom_cache = cache
					#add globalcache if exists	
					run("zpool add %s cache %s"%(self._poolname,geom_cache))	

			self.createzvol(param,prot_type)			
		
	def createcmd(self,pooltype,poolproperty,poolname,disklist):
		#create 1+0
		result=[]
		#print "pool type= %s"%pooltype

		cmd="zpool create -f"

		if poolproperty:
			for prop in poolproperty.split():
				cmd += " -o %s=on"%prop
				

		cmd += " %s"%poolname
		
		if pooltype == "mirror":
			result = self.div_list(disklist,2)#each mirror use 2 disk
			
		elif pooltype == "raidz":
			result = self.div_list(disklist,9)#each raidz use 8+1 disk

		elif pooltype == "raidz2":
			result = self.div_list(disklist,10)#each raidz use 8+2 disk

		elif pooltype == "raidz3":
			result = self.div_list(disklist,11)#each raidz use 8+3 disk	

		if pooltype == "stripe" or pooltype=="":
			cmd +=" "+ ' '.join(disklist)
		else:	
			#print result
			for val in result:
				cmd+= " %s %s"%(pooltype,' '.join(val))	
				
		#print "cmd=%s"%cmd		
		return cmd
		
	def div_list(self,disklist,gp_size):			
		size = len(disklist)
		return [disklist[i:i+gp_size] for i in range(0,size,gp_size)]
		
	def destroyzpool(self):
		run('zpool destroy %s' % self._poolname)
		
	def createzvol(self,param,prot_type):
		cmd="zfs create "
		
		if param['zvolprop']:
			for prop in param['zvolprop'].split():
				cmd += "-o %s=on "%prop
				if prop == "encryption":
					cmd += " -o keysource=/etc/passwd "
		# iscsi create zvol
		if prot_type=='iscsi':
			cmd += "-b 128k -V 100g "
			cmd += self._zvolname
		else:
		#else create zfs
			if param['mountpoint']:
				cmd +="-o mountpoint=%s "%param['mountpoint']
			cmd += self._zfsname
	
		run(cmd)
		run('chmod 777 %s'%param['mountpoint'])
	
	def transformslotname(self):
		es_disklist={}
	
		#run('/nas/util/diskscan.py add jbod',quiet=True)
		output = run('disk -d status')
		for line in output.splitlines():
			tmp = line.split()
			# jobd disk start with s-528,we need to translate it to h.x format
			if tmp[0].startswith('s-528.'):
				str = tmp[0].rsplit('.')
				tmp[0] ='h.%d'%(int(str[1])+16)
			es_disklist[tmp[0]] = tmp[10]
		
		#print es_disklist
		return es_disklist		
			
def main():
	pass
		
if __name__ == '__main__':
	main()		

