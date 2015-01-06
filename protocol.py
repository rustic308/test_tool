from fabric.api import *


class protocol(object):
	def __init__(self,dbconf):
		self._type = ''
		self._iscsitgt = 'iqn.zperftarget'
		self._iscsiportal = '192.168.10.1'
		self._iscsiacl = '192.168.10.0/24'
		self._dbconf =dbconf
	def service_start(self,prot_type):
		with settings(
			hide('stdout'),
			host_string=self._dbconf['server_host'],password=self._dbconf['server_password'],
			warn_only=True
		):
			self._type = prot_type
			if self._type=='iscsi':
				self.iscsi_load()
			
				run('/nas/util/scst/iscsiadm add_target %s'%self._iscsitgt)
				run('/nas/util/scst/scsidevadm add_device -n lun1 -h vdisk_blockio -f /dev/zvol/testpool/lun1')
				run('/nas/util/scst/iscsiadm add_allow_portal %s %s'%(self._iscsitgt,self._iscsiportal))
				run('/nas/util/scst/iscsiadm add_acl_network %s %s'%(self._iscsitgt,self._iscsiacl))
				run('/nas/util/scst/scstadm add_lun -d iscsi -t %s -l 1 -D lun1 -e 0'%self._iscsitgt)
			
			elif self._type == 'local':
				print "local,no operation"
			elif self._type == 'nfs':
				run("echo '/mnt/stripe_pool2  -network 192.168.10.0/24' > /etc/exports")
				run('service nfsd onestart')
			
			elif self._type == 'samba':	
				print ' samba not yet implement'
			else:
				print 'why are you here?'
			
	def service_enable(self,prot_type):
		self._type = prot_type

		self.mod_load(self._type)
		
		if self._type=='iscsi':
			run('/nas/util/scst/iscsiadm add_target %s'%self._iscsitgt)
			run('/nas/util/scst/scsidevadm add_device -n lun1 -h vdisk_blockio -f /dev/zvol/testpool/lun1')
			run('/nas/util/scst/iscsiadm add_allow_portal %s %s'%(self._iscsitgt,self._iscsiportal))
			run('/nas/util/scst/iscsiadm add_acl_network %s %s'%(self._iscsitgt,self._iscsiacl))
			run('/nas/util/scst/scstadm add_lun -d iscsi -t %s -l 1 -D lun1 -e 0'%self._iscsitgt)
			
		elif self._type == 'local':
			print "local,no operation"
		elif self._type == 'nfs':
			run("echo '/mnt/stripe_pool2  -network 192.168.10.0/24' > /etc/exports")
			run('service nfsd onestart')
			
		elif self._type == 'samba':	
			print ' samba not yet implement'
		else:
			print 'why are you here?'

	def mod_load(self,prot_type):
		if prot_type == 'iscsi':
			self.iscsi_load()
		elif prot_type == 'nfs':
			print 'nfs:do nothing'	
		else :
			print 'local operation:do nothing'	

	def service_stop(self,prot_type):
		self._type = prot_type
		if self._type == 'iscsi':
			run('/nas/util/scst/scstadm del_lun -d iscsi -t %s -l 1'%self._iscsitgt)
			run('/nas/util/scst/iscsiadm del_acl_network %s %s'%(self._iscsitgt,self._iscsiacl))
			run('/nas/util/scst/iscsiadm del_allow_portal %s %s'%(self._iscsitgt,self._iscsiportal))
			run('/nas/util/scst/scsidevadm del_device -n lun1 -h vdisk_blockio')
			run('/nas/util/scst/iscsiadm del_target %s'%self._iscsitgt)
			
		elif self._type == 'nfs':
			run('service nfsd onestop')
			run('service mountd stop')
			
	def iscsi_modcheck(self):
		output = run('kldstat | grep scst',warn_only=True)
		print "output= %s"%output
		if not output:
			return False
		for item in output.splitlines():
			for splice in item.split():
				if splice.find('scst'):
					return True

	def iscsi_load(self):
		mod_loaded = self.iscsi_modcheck()
		print "mod loaded= %s "%mod_loaded
		
		if mod_loaded == False:
			run('/etc/rc.d/q-scstd start')
		else:
			run('/etc/rc.d/q-scstd restart')

		#tricky to enable daemon 
		run(' nohup /nas/util/scst/iscsi-scstd >& /dev/null < /dev/null &',pty=False)

	def iscsi_unload(self):
		run('kldunload iscsi_scst.ko')
		run('kldunload scst_vdisk.ko')
		run('kldunload scst.ko')
		run('pkill iscsi-scstd')
		
def main():
	pass
		
if __name__ == '__main__':
	main()		

