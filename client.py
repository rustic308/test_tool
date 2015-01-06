from fabric.api import *
from zfs import *
from envconfig import *
from protocol import *
from fiojob import *
from fiorecord import *


localhost='127.0.0.1'

def clt_connect(prot_type):
	#run('ifconfig enp6s0f0 192.168.10.2 netmask 255.255.255.0')
	
	if prot_type == 'iscsi':
		run('iscsiadm -m discovery -t sendtargets -p 192.168.10.1:3260')
		run('iscsiadm -m node -l -T iqn.zperftarget -p 192.168.10.1:3260')
	elif prot_type == 'nfs':
		run('mkdir /mnt/stripe_pool2')
		run('chmod 777 /mnt/stripe_pool2')
		run('mount -t nfs 192.168.10.1:/mnt/stripe_pool2 /mnt/stripe_pool2')
		
	else:
		print 'not yet implement'

def clt_close(prot_type):
	if prot_type == 'iscsi':
		run('iscsiadm -m node -u -T iqn.zperftarget -p 192.168.10.1:3260')
	elif prot_type == 'nfs':
		run('umount /mnt/stripe_pool2')
		run('rmdir /mnt/stripe_pool2')
		
def clt_fio(env_num, fio_num, prot_type, record):
	record_db = record.savetodb()
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

	with settings(host_string=localhost):
        	record.set_configdata(env_num, fio_num)	


	result = fioJob.start()

	
	if (record_db):
		tpread = fioJob.getTPRead(result)/1024#convert to MB/s
        	tpwrite = fioJob.getTPWrite(result)/1024#convert to MB/s
        	iopsread = fioJob.getIOPSRead(result)
        	iopswrite = fioJob.getIOPSWrite(result)
        	record.set_fiodata(tpread,tpwrite,iopsread,iopswrite,prot_type)
        	record.get_alldata()
	
