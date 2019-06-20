from __future__ import print_function

import lxml.etree as ET
import subprocess,random,sys,libvirt,os,wget,configparser

def config_parser ():
    global  config
    config = configparser.ConfigParser ()
    config.read ('config.ini')

config_parser()

file_path = "xenial-server-cloudimg-amd64-disk1.img"
if os.path.exists(file_path) == True :
    pass
else:
    url = config [ 'PARAMETERS' ] [ 'VM_BASE_IMAGE' ]
    lsimage = wget.download (url)


mac = "52:54:00:%02x:%02x:%02x" % (
    random.randint (0, 255),
    random.randint (0, 255),
    random.randint (0, 255),)



def configvm1():
    with open ('/home/hvashchenko/.ssh/id_rsa.pub', 'r') as file:
        data = file.read ().replace ('\n', '')
    user_data_vm1="""#cloud-config
password: password
chpasswd: {expire}
ssh_pwauth: True
ssh_authorized_keys:
  - {data}
apt_update: true
package_update: true
packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - software-properties-common
runcmd:
  - echo 1 > /proc/sys/net/ipv4/ip_forward
  - echo "nameserver 8.8.8.8" > /etc/resolv.conf
  - iptables -t nat -A POSTROUTING -o {ext_if} -j MASQUERADE
  - ip link add name {vxlan_if} type vxlan id {vid} dev {int_if} remote {vm2_ip} local {int_ip} dstport 4789
  - ip address add {vx_nal_net}/{int_mask} dev {vxlan_if}
  - ip link set up {vxlan_if}
  - apt-get install apt-transport-https ca-certificates curl software-properties-common - y
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  - add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu  $(lsb_release -cs)  stable" 
  - apt-get update
  - apt-get install docker-ce -y
""".format(data=data, expire='{ expire: False }',int_ip=config['INTERNAL']['VM1_INTERNAL_IP'],int_mask=config['INTERNAL']['INTERNAL_NET_MASK'],vxlan_if=config['PARAMETERS']['VXLAN_IF'],vid=config['PARAMETERS']['VID'],vm2_ip=config["INTERNAL"]["VM2_INTERNAL_IP"],int_if=config['VM1']['VM1_INTERNAL_IF'],ext_if=config["VM1"]["VM1_EXTERNAL_IF"],vx_nal_net=config["PARAMETERS"]["VM1_VXLAN_IP"])

    meta_data_vm1 = """instance-id: bca73069-81e0-4419-acec-6beaa5ae74df
hostname: {vm1_name}
local-hostname: {vm1_name}
network-interfaces: |
  auto {vm1_external_if}
  iface {vm1_external_if} inet dhcp
  dns-nameservers {vm_dns}
  auto {vm1_internal_if}
  iface {vm1_internal_if} inet static
  address {vm1_internal_ip}
  netmask {internal_mask}
  auto {vm1_mgmt_if}
  iface {vm1_mgmt_if} inet static
  address {vm1_mgmt_ip}
  netmask {vm1_mgmt_mask}
""".format(vm1_name=config[ "VM1" ][ "VM1_NAME" ],
                                    vm1_external_if=config[ "VM1" ][ "VM1_EXTERNAL_IF" ],
                                    vm1_internal_if=config[ "VM1" ][ "VM1_INTERNAL_IF" ],
                                    vm1_internal_ip=config[ "INTERNAL" ][ "VM1_INTERNAL_IP" ],
                                    internal_mask=config[ "INTERNAL" ][ "INTERNAL_NET_MASK" ],
                                    vm_dns=config["PARAMETERS"]["VM_DNS"],
                                    vm1_mgmt_if=config["VM1"]["VM1_MANAGEMENT_IF"],
                                    vm1_mgmt_ip=config["MGMT"]["VM1_MANAGEMENT_IP"],
                                    vm1_mgmt_mask=config["MGMT"]["MANAGEMENT_NET_MASK"])

    with open ('config-drives/vm1-config/meta-data', 'w') as f:
        f.write (meta_data_vm1)


    with open ('config-drives/vm1-config/user-data', 'w') as f:
        f.write (user_data_vm1)

def configvm2():

    with open ('/home/hvashchenko/.ssh/id_rsa.pub', 'r') as file:
        data = file.read ().replace ('\n', '')

    user_data_vm2 = """#cloud-config
password: password
chpasswd: {expire}
ssh_pwauth: True
ssh_authorized_keys:
  - {data}
package_update: true
packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - software-properties-common
runcmd:
  - echo 1 > /proc/sys/net/ipv4/ip_forward
  - echo "nameserver 8.8.8.8" > /etc/resolv.conf
  - echo "127.0.0.1 localhost, vm2" > /etc/hosts
  - ip link add name {vxlan_if} type vxlan id {vid} dev {int_if} remote {vm1_ip} local {vm2_ip} dstport 4789
  - ip address add {vx_nal_net}/{int_mask} dev {vxlan_if}
  - ip link set up {vxlan_if}
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  - add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu  $(lsb_release -cs)  stable" 
  - apt-get update
  - apt-get install docker-ce -y
""".format (data=data, expire='{ expire: False }',vxlan_if=config['PARAMETERS']['VXLAN_IF'],vid=config['PARAMETERS']['VID'],int_mask=config['INTERNAL']['INTERNAL_NET_MASK'],vm1_ip=config["INTERNAL"]["VM1_INTERNAL_IP"],vm2_ip=config["INTERNAL"]["VM2_INTERNAL_IP"],int_if=config['VM2']['VM2_INTERNAL_IF'],vx_nal_net=config["PARAMETERS"]["VM2_VXLAN_IP"])

    meta_data_vm2 = """instance-id: bca73069-81e0-4419-acec-6beaa5ae742f
hostname: {vm2_name}
local-hostname: {vm2_name}
network-interfaces: |
  auto {vm2_internal_if}
  iface {vm2_internal_if} inet static
  address {vm2_internal_ip}
  netmask {internal_mask}
  gateway {gateway}
  dns-nameservers {external_host_ip} {vm_dns}
  auto {vm2_mgmt_if}
  iface {vm2_mgmt_if} inet static
  address {vm2_mgmt_ip}
  netmask {vm2_mgmt_mask}
""".format (vm2_name=config [ "VM2" ] [ "VM2_NAME" ],
            vm2_internal_if=config[ "VM2" ][ "VM2_INTERNAL_IF" ],
            vm2_internal_ip=config[ "INTERNAL" ][ "VM2_INTERNAL_IP" ],
            internal_mask=config[ "INTERNAL" ][ "INTERNAL_NET_MASK" ],
            vm_dns=config[ "PARAMETERS" ][ "VM_DNS" ],
            external_host_ip=config["EXTERNAL"]["EXTERNAL_NET_HOST_IP"],
            gateway=config["INTERNAL"]["VM1_INTERNAL_IP"],
            vm2_mgmt_if=config[ "VM2" ][ "VM2_MANAGEMENT_IF" ],
            vm2_mgmt_ip=config[ "MGMT" ][ "VM2_MANAGEMENT_IP" ],
            vm2_mgmt_mask=config[ "MGMT" ][ "MANAGEMENT_NET_MASK"]
            )

    with open ('config-drives/vm2-config/meta-data', 'w') as f:
        f.write (meta_data_vm2)

    with open ('config-drives/vm2-config/user-data', 'w') as f:
        f.write (user_data_vm2)


def config_iso():

    os.system('sudo mkisofs -o "/var/lib/libvirt/images/vm1/config-vm1.iso" -V cidata -r -J --quiet /home/hvashchenko/libpy/config-drives/vm1-config')
    subprocess.call(['sudo','cp','xenial-server-cloudimg-amd64-disk1.img','/var/lib/libvirt/images/vm1/vm1.qcow2'])
    os.system ('sudo mkisofs -o "/var/lib/libvirt/images/vm2/config-vm2.iso" -V cidata -r -J --quiet /home/hvashchenko/libpy/config-drives/vm2-config')
    subprocess.call ([ 'sudo', 'cp', 'xenial-server-cloudimg-amd64-disk1.img', '/var/lib/libvirt/images/vm2/vm2.qcow2' ])


def create_vms():
    vm1 = "virt-install --name {name} --ram 512 --vcpus=1 --os-variant=ubuntu16.04 --virt-type=kvm --hvm  --cdrom=/var/lib/libvirt/images/vm1/config-vm1.iso  --network network={ext},mac={mac} --network network={int} --network network={mgmt} --graphics vnc  --disk path=/var/lib/libvirt/images/vm1/vm1.qcow2,size=10,bus=virtio,format=qcow2 --noautoconsole".format(mac=mac,name=config['VM1']["VM1_NAME"],ext=config["EXTERNAL"]["EXTERNAL_NET_NAME"],int=config["INTERNAL"]["INTERNAL_NET_NAME"],mgmt=config["MGMT"]["MANAGEMENT_NET_NAME"])
    os.system(vm1)
    vm2 = "virt-install --name {name} --ram 512 --vcpus=1 --os-variant=ubuntu16.04 --virt-type=kvm --hvm  --cdrom=/var/lib/libvirt/images/vm2/config-vm2.iso  --network network={int} --network network={mgmt} --graphics vnc  --disk path=/var/lib/libvirt/images/vm2/vm2.qcow2,size=10,bus=virtio,format=qcow2 --noautoconsole".format(name=config['VM2']["VM2_NAME"],int=config["INTERNAL"]["INTERNAL_NET_NAME"],mgmt=config["MGMT"]["MANAGEMENT_NET_NAME"])
    os.system(vm2)
def cr_int_net():
    root = ET.Element("network")
    doc = ET.SubElement(root, "name")
    doc.text = 'internal'
    tree = ET.ElementTree(root)
    tree.write("networks/internal.xml")


def cr_mgmt_net():
    name = name=config ['MGMT']['MANAGEMENT_NET_NAME']
    ip = config[ 'MGMT' ][ 'MANAGEMENT_HOST_IP' ]
    mask = config[ 'MGMT' ][ 'MANAGEMENT_NET_MASK' ]
    root = ET.Element("network")
    doc = ET.SubElement(root, 'name')
    doc.text = name
    level2 = ET.SubElement(root, 'ip', address=ip, mask=mask)
    tree = ET.ElementTree(root)
    tree.write("networks/management.xml")



def cr_ext_net():
    ipaddr = config[ 'EXTERNAL' ][ 'EXTERNAL_NET_HOST_IP' ]
    name = config[ 'EXTERNAL' ][ 'EXTERNAL_NET_NAME' ]
    mask = config[ 'EXTERNAL' ][ 'EXTERNAL_NET_MASK' ]
    start = config[ 'EXTERNAL' ][ 'EXTERNAL_NET_DHCP_RANGE_START' ]
    end = config[ 'EXTERNAL' ][ 'EXTERNAL_NET_DHCP_RANGE_END' ]
    vm1_ip = config[ 'EXTERNAL' ][ 'VM1_EXTERNAL_IP' ]
    root = ET.Element("network")
    doc = ET.SubElement(root, "name")
    doc.text = name
    forward = ET.SubElement(root, "forward", mode=u"nat" )
    nat = ET.SubElement(forward, "nat")
    port = ET.SubElement(nat, "port", start="1024",end="65535")
    ip = ET.SubElement(root, "ip", address=ipaddr, mask=mask)
    dhcp = ET.SubElement(ip, "dhcp")
    range = ET.SubElement(dhcp, "range", start=start, end=end)
    host = ET.SubElement(dhcp, "host", mac="52:54:00:dc:29:7a", name="vm1", ip=vm1_ip)
    tree = ET.ElementTree(root)
    tree.write ("networks/external.xml")






def create_files():
    subprocess.call ([ "sudo", "rm", '-rf', '/var/lib/libvirt/images/vm1' ])
    subprocess.call ([ 'sudo', 'mkdir', '/var/lib/libvirt/images/vm1' ])
    subprocess.call ([ "sudo", "rm", '-rf', '/var/lib/libvirt/images/vm2' ])
    subprocess.call ([ 'sudo', 'mkdir', '/var/lib/libvirt/images/vm2' ])
    dirName = 'networks'
    try:
        os.mkdir(dirName)
        print("Directory ", dirName, " Created ")
    except FileExistsError:
        print("Directory ", dirName, " already exists")
    dirvms = 'config-drives'
    try:
        os.mkdir(dirvms)
        print("Directory", dirvms," Created")
    except FileExistsError:
        print("Directory", dirvms," alreade exists")

    file_path1="config-drives/vm1-config"
    try:
        os.mkdir(file_path1)
        print("Directory created")
    except FileExistsError:
        print("Directory already exists")

    file_path2 = "config-drives/vm2-config"
    try:
        os.mkdir (file_path2)
        print("Direcroty created")
    except FileExistsError:
        print("Directory already exists")




def create_network(xml):
    conn = libvirt.open('qemu:///system')
    network = conn.networkDefineXML(xml)
    if network == None:
        print('Failed to define a virtual network', file=sys.stderr)
        exit(1)
    active = network.isActive()
    if active == 1:
        print('The new transient virtual network is active')
    else:
        print('The new transient virtual network is not active')
    network.create()  # set the network active
    active = network.isActive()
    if active == 1:
        print('The new transient virtual network is active')
    else:
        print('The new transient virtual network is not active')

def main():
    create_files()
    cr_int_net()
    cr_ext_net()
    cr_mgmt_net()
    configvm1()
    configvm2()
    config_iso()

    try:
        with open('/home/hvashchenko/libpy/networks/internal.xml', 'r') as f2:
            data_int = f2.read()
            create_network(data_int)
    except libvirt.libvirtError:
        print("Interntal created")
    try:
        with open ('/home/hvashchenko/libpy/networks/external.xml', 'r') as f2:
            data_ext = f2.read ()
            create_network (data_ext)
    except libvirt.libvirtError:
        print("External created")

    try:
        with open ('/home/hvashchenko/libpy/networks/management.xml', 'r') as f2:
            data_mgmt = f2.read ()
            create_network (data_mgmt)
    except libvirt.libvirtError:
        print("Management created")


    create_vms()

    exit(0)



if __name__ == '__main__':
    main()
