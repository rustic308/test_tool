from fabric.api import *
from server import *
from client import *

#for test
from fiorecord import *

client='root@10.77.1.103:22'
client_pw='Qnap@1234'
server='root@10.77.2.186:22'
server_pw='qq'
env.hosts = [client,server]

env.passwords = {server: server_pw, client: client_pw}
#env.hosts = [server]
#env.passwords = {server:server_pw}


@hosts(server)
def testcmd():
	run("echo '/mnt/stripe_pool2  -network 192.168.10.0/24' > /etc/exports")
	
@hosts(server)
def zfs_create(env_num,prot_type):
	with settings(host_string=server):
		srv_create_zpool(prot_type,env_num)

@hosts(server)
def zfs_destroy():
	with settings(host_string=server):
		srv_destroy_zpool()

@hosts(server)
def service_start(prot_type):
	with settings(host_string=server):
		srv_enable_service(prot_type)

@hosts(server)
def service_stop(prot_type):
	with settings(host_string=server):
		srv_disable_service(prot_type)

@hosts(client)
def client_connect(prot_type):
	with settings(host_string=client):
		clt_connect(prot_type)

@hosts(client)
def client_close(prot_type):
	with settings(host_string=client):
		clt_close(prot_type)

@hosts(client)	
def client_fio(env_num, fio_num, prot_type, record):
	if prot_type == 'local':
		with settings(host_string=server):
			clt_fio(env_num, fio_num, prot_type, record)
	else:	
		with settings(host_string=client):
			clt_fio(env_num, fio_num, prot_type, record)
			
		
@hosts(server)
def iscsi_fulltest():
	debug_enable = False
	save_enable = True
	prot_type='iscsi'
	env_num = 2
	fio_num = 2
	record = fiorecord(debug_enable,save_enable)
	for i in xrange(1,env_num+1):
		for j in xrange(1,fio_num+1):
			print "iscsi test : env_num=%d fio_num=%d"%(i,j)
			srv_getver(record)
			zfs_create(i,prot_type)
			service_start(prot_type)
			client_connect(prot_type)
			client_fio(i, j, prot_type,record)
			client_close(prot_type)
			service_stop(prot_type)
			zfs_destroy()

@hosts(server)
def nfs_fulltest():
	debug_enable = False
	save_enable = False
	prot_type='nfs'
	env_num = 1
	fio_num = 1
	record = fiorecord(debug_enable,save_enable)
	for i in xrange(1,env_num+1):
		for j in xrange(1,fio_num+1):
			print "nfs test : env_num=%d fio_num=%d"%(i,j)
			srv_getver(record)
			zfs_create(i,prot_type)
			service_start(prot_type)
			client_connect(prot_type)
			client_fio(i, j, prot_type,record)
			client_close(prot_type)
			service_stop(prot_type)
			zfs_destroy()			
	
@hosts(server)
def local_fulltest():
	debug_enable = False
	save_enable = True
	prot_type = 'local'
	env_num = 1
	fio_num = 1
	record = fiorecord(debug_enable,save_enable)
	for i in xrange(1,env_num+1):
		for j in xrange(1,fio_num+1):
			print "local test : env_num=%d fio_num=%d"%(i,j)
			srv_getver(record)
			zfs_create(i,prot_type)
			client_fio(i, j, prot_type,record)
			zfs_destroy()
