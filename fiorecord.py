from pg8000 import DBAPI
from envconfig import *
import datetime

class fiorecord(object):
	def __init__(self,debug_flag,savedb_flag):
		self._db = dbconf().load("db.conf")
		self._totalconfig = {}
		self._reqopt = ['pooltype','poolprop','zvolprop','rw','ioengine','sync','bs','fw_ver','zfs_ver','debug_id']
		self._zvolprop_list = ['dedup','compression','encryption']
		self._zpoolprop_list = ['globalcache']
		#self._debug_id = 0
		self._debug_enable = debug_flag
		self.get_debug_id()
		self._save2db = savedb_flag
		

	def __del__(self):
		print "object destroy!!!!!!!!!!"

	def savetodb(self):
		return self._save2db


	def get_debug_id(self):
		if self._debug_enable:
			db = self._db
			conn = DBAPI.connect(host="%s"%db['host'],database="%s"%db['database'],user="%s"%db['user'],password="%s"%db['password'])
			cursor = conn.cursor()
			cursor.execute("lock table global_var in access exclusive mode")
			cursor.execute("select debug_id from global_var")
		
			#self._debug_id = int(cursor.fetchone()[0])
			self._totalconfig['debug_id'] = int(cursor.fetchone()[0])
			print "DEBUG MODE:get debug id %d"%self._totalconfig['debug_id'] 
			cursor.execute("update global_var set debug_id=debug_id+1")
			conn.commit()
			conn.close()
		
	def get_alldata(self):
		print self._totalconfig	

	def set_srvinfo(self,fw_ver,zfs_ver):
		self._totalconfig['fw_ver'] = fw_ver
		self._totalconfig['zfs_ver'] = zfs_ver
		
	def set_configdata(self,env_num,fio_num):
		envconfig = envconf().load("config/env_config%d"%env_num)
		rw,fioconfig = fioconf().load("config/fio_config%d"%fio_num)
		self._totalconfig.update(dict(envconfig,**fioconfig))
		self.trimconfig()

		self._totalconfig['env_num'] = env_num
		self._totalconfig['fio_num'] = fio_num
		self._totalconfig['datetime'] = datetime.datetime.now().strftime("%y-%m-%d %H:%M")
		
	def trimconfig(self):
		''' @there are some options we don't want to store in database,
		      trimconfig try to get rid of them '''
		unneeded =[]
		for key,val in self._totalconfig.iteritems():
			if key not in self._reqopt:
				unneeded.append(key)
				
		for key in unneeded:
			del self._totalconfig[key]
			
		#add one line to set zpool type empty as stripe
		if self._totalconfig['pooltype'] =='':
				self._totalconfig['pooltype']='stripe'

		#translate poolprop and zvolprop to on/off
		zpoolprop = self._totalconfig['poolprop']
		if zpoolprop=='':
			for option in self._zpoolprop_list:
				self._totalconfig[option]='off'
		else:
			for option in self._zpoolprop_list:
				if option in zpoolprop.split():
					self._totalconfig[option]='on'
				else:
					self._totalconfig[option]='off'
		
		zvolprop = self._totalconfig['zvolprop']
		if zvolprop=='':
			for option in self._zvolprop_list:
				self._totalconfig[option]='off'
		else:
			for option in self._zvolprop_list:
				if option in zvolprop.split():
					self._totalconfig[option]='on'
				else:
					self._totalconfig[option]='off'

	def set_fiodata(self,tpread,tpwrite,iopsread,iopswrite,prot_type):
		self._totalconfig['tpread']=tpread
		self._totalconfig['tpwrite']=tpwrite
		self._totalconfig['iopsread']=iopsread
		self._totalconfig['iopswrite']=iopswrite
		self._totalconfig['prot_type']= prot_type
		print "in set fiodata config=%s"%self._totalconfig
		
	def record_update(self):
		db = dbconf().load("db.conf")
		conn = DBAPI.connect(host="%s"%db['host'],database="%s"%db['database'],user="%s"%db['user'],password="%s"%db['password'])
		conn.close()

	def test_sqlcmd(self):
		print 'call testsqlcommand'
		
