from fabric.api import *
from zfs import *
from envconfig import *
from protocol import *
from fiorecord import *

def srv_getver(record):
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
	#print fw_ver,zfs_ver
	record.set_srvinfo(fw_ver,zfs_ver)

def srv_check_jbod_multipath():
	es_disklist={}
	
	run('/nas/util/diskscan.py add jbod')
	output = run('disk -d status',quiet=True)
	for line in output.splitlines():
		tmp = line.split()
		# jobd disk start with s-528,we need to translate it to h.x format
		if tmp[0].startswith('s-528.'):
			str = tmp[0].rsplit('.')
			tmp[0] ='h.%d'%(int(str[1])+16)
		es_disklist[tmp[0]] = tmp[10]
		
	print es_disklist

def srv_create_zpool(prot_type,env_num):
	envconfig = envconf().load('config/env_config%d'%env_num)
	#rw,fioconfig = fioconf().load('config/fio_config1')
	zfs().createzpool(envconfig,prot_type)
	
def srv_destroy_zpool():	
	zfs().destroyzpool()

def srv_enable_service(prot_type):
	#set up 10g adapter connection
	run('ifconfig ix0 192.168.10.1 netmask 255.255.255.0')
	protocol().service_start(prot_type)

def srv_disable_service(prot_type):
	protocol().service_stop(prot_type)


	