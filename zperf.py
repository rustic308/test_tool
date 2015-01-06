from fabric.api import *
from envconfig import *

from zfs import *
from protocol import *
from fiojob import *


class zperf(object):
	def __init__(self):
		self._config={}
		self._dbconf = dbconf().load("db.conf")
		self._envnum = 0
		self._fionum= 0
		self._diskmap = {}
		self._envconfig = {}
		self._fioconfig = {}
		
	def env_prepare(self):
		
		print 'set up server network adapter:'
		with settings(
			hide('stdout'),
			host_string=self._dbconf['server_host'],password=self._dbconf['server_password'],
			warn_only=True
		):
			run('ifconfig %s 192.168.10.1 netmask 255.255.255.0'%self._dbconf['server_adapter'])
		
		print 'set up client network adapter:'
		with settings(
			hide('stdout'),
			host_string=self._dbconf['client_host'],password=self._dbconf['client_password'],
			warn_only=True
		):
			run('ifconfig %s 192.168.10.2 netmask 255.255.255.0'%self._dbconf['client_adapter'])

		print 'test network between client and server'	
		with settings(
			hide('stdout'),
			host_string=self._dbconf['client_host'],password=self._dbconf['client_password'],
			warn_only=True,
		):
			run('ping 192.168.10.1 -c 1')

		self.srv_getver()	

		self.srv_check_jbod_multipath()
		
	def srv_check_jbod_multipath(self):
		print 'check jobod disk multipath'
		es_disklist={}
		with settings(
			hide('stdout'),
			host_string=self._dbconf['server_host'],password=self._dbconf['server_password'],
			warn_only=True
		):
	
			run('/nas/util/diskscan.py add jbod')
			output = run('disk -d status',quiet=True)
			for line in output.splitlines():
				tmp = line.split()
				# jobd disk start with s-528,we need to translate it to h.x format
				if tmp[0].startswith('s-528.'):
					str = tmp[0].rsplit('.')
					tmp[0] ='h.%d'%(int(str[1])+16)
				es_disklist[tmp[0]] = tmp[10]

			self._diskmap = es_disklist
			#print self._diskmap	
		
	def srv_getver(self):
		with settings(
			hide('stdout'),
			host_string=self._dbconf['server_host'],password=self._dbconf['server_password'],
			warn_only=True
		):
			zfs_ver = 0
			fw_ver = 0
			output = run('ver -v');
			result = output.splitlines()[0].split()[0]	
			idx = result.rindex('-')
			#get ES firmware version
			fw_ver = result[idx+1:]
			#get zfs-stable version
			for item in output.splitlines():
				for splice in item.split():
					if splice.startswith('zfs-stable'):
						result = splice.split()[0]
						idx = result.rindex('-')
						zfs_ver = int(result[idx+1:])

			self._config['zfs_ver'] = zfs_ver
			self._config['fw_ver'] = fw_ver
				
	def get_setting_num(self):
		env_num = 0
		fio_num = 0
		for root,dir,files in os.walk("./config"):
			for file in files:
				if file.startswith('env_config'):
					env_num = env_num + 1
				elif file.startswith('fio_config'):
					fio_num = fio_num + 1
		
		self._envnum = env_num
		self._fionum = fio_num

	def clt_connect(self,prot_type):
		with settings(
			hide('stdout'),
			host_string=self._dbconf['client_host'],password=self._dbconf['client_password'],
			warn_only=True,
		):				
			if prot_type == 'iscsi':
				run('iscsiadm -m discovery -t sendtargets -p 192.168.10.1:3260')
				run('iscsiadm -m node -l -T iqn.zperftarget -p 192.168.10.1:3260')

			elif prot_type == 'nfs':
				run('mkdir /mnt/stripe_pool2')
				run('chmod 777 /mnt/stripe_pool2')
				run('mount -t nfs 192.168.10.1:/mnt/stripe_pool2 /mnt/stripe_pool2')
							
			else:
				print 'not yet implement'
	

	def full_exec(self,prot_type):
		#self.get_setting_num()
		self._envnum = 1
		self._fionum = 1
		for i in xrange(1, self._envnum + 1):	
			for j in xrange(1, self._fionum + 1):
				fs = zfs(self._dbconf)
				ptl = protocol(self._dbconf)

				fs.createzpool(i, prot_type)
				ptl.service_start(prot_type)
				self.clt_connect(prot_type)
				self.clt_fio(j, prot_type, False)

	def clt_fio(self,fio_num, prot_type,record_db):
		host = ''
		pw = ''
		if prot_type == 'local':
			host = self._dbconf['server_host']
			pw = self._dbconf['server_password']
		else:
			host = self._dbconf['client_host']
			pw = self._dbconf['client_password']

		
		with settings(
			host_string=host,password=pw,
			warn_only=True,
		):
			print env.host_string
			#record_db = record.savetodb()
			rw,fioconfig = fioconf().load("config/fio_config%d"%fio_num)
			fioJob = FioJob()
			#record = fiorecord()
	
			fioJob.addKVArg('name',"fiojob")
			if (record_db==True):
				fioJob.addSglArg('minimal')
			fioJob.addSglArg('thread')

			for key,val in fioconfig.iteritems():
				if val == None:
					fioJob.addSglArg(key)
				else:
					fioJob.addKVArg(key,val)

			if prot_type=='iscsi':
				#iscsi do io to zvol instead of zfs,disable directory mountpoint
				fioJob.delKVArg('directory')
				#do io to raw disk,fetch partition table last item
				output = run('cat /proc/partitions',quiet=True)
				for line in output.splitlines():
					tmp = line.split()
				fioJob.addKVArg('filename','/dev/%s'%''.join(tmp[-1:]))	
		
		#with settings(host_string=localhost):
        	#	record.set_configdata(env_num, fio_num)	


			result = fioJob.start()

		'''
		if (record_db):
			tpread = fioJob.getTPRead(result)/1024#convert to MB/s
        		tpwrite = fioJob.getTPWrite(result)/1024#convert to MB/s
        		iopsread = fioJob.getIOPSRead(result)
        		iopswrite = fioJob.getIOPSWrite(result)
        		record.set_fiodata(tpread,tpwrite,iopsread,iopswrite,prot_type)
        		record.get_alldata()
        		with settings(host_string=localhost):
				record.record_update()
		'''
def main():
	mode = raw_input('''Please select Zperf operate mode:
    1. Official release mode(EUT)--Test data will automatically store in regular table
    2. Quit''')
    
	mode = int(mode)

	if mode == 1:
	#release mode
		option = raw_input('''Option:
	1. Full Setting execution
	2. Quit
	''')

		option = int(option)
		if option == 1:
			save_result = True
			save = raw_input("store result in database?(y/n):(default:y)")
			if save!='y':
				save_result = False
			
			task = zperf()
			task.env_prepare()
			task.full_exec('local')
			
		else:
			print "Leave Zperf!"
			return 0

	
	else	:
		print "Leave Zperf!"
		return 0
								
if __name__ == '__main__':
	main()	

