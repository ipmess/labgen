#!/usr/bin/env python3
'''
Created on Sat Dec 29 13:16:08 2018

@author: ipmess
'''

import os, json, re, uuid
import jsonschema
import ciscoconfparse

def skelecfg(hostname='Router'):
  
  # Build a blank configuration
  cfg = ciscoconfparse.CiscoConfParse([])
  cfg.append_line('!')
  cfg.append_line('hostname ' + hostname)
  cfg.append_line('service timestamps debug datetime msec')
  cfg.append_line('service timestamps log datetime msec')
  cfg.append_line('no service password-encryption')
  cfg.append_line('no ip icmp rate-limit unreachable')
  cfg.append_line('no ip domain-lookup')
  cfg.append_line('no cdp log mismatch duplex')
  cfg.append_line('line con 0')
  cfg.append_line(' exec-timeout 0 0')
  cfg.append_line(' privilege level 15')
  cfg.append_line(' logging synchronous')
  cfg.append_line(' width 200')
  cfg.append_line(' length 100')
  
  return cfg

__WRITETOFILES__ = True
__IOUImage__ = 'i86bi-linux-l3-adventerprisek9-15.5.2T.bin'
__BaseConsole__ = 5000
__Compute__ = 'vm' # or 'local'


EthernetInterface = {
    1:'Ethernet0/0', 2:'Ethernet0/1', 3:'Ethernet0/2', 4:'Ethernet0/3',
    5:'Ethernet1/0', 6:'Ethernet1/1', 7:'Ethernet1/2', 8:'Ethernet1/3'
    }

AdapterPort = {
    1:{'Adapter':0, 'Port':0}, 2:{'Adapter':0, 'Port':1}, 3:{'Adapter':0, 'Port':2}, 4:{'Adapter':0, 'Port':3},
    5:{'Adapter':1, 'Port':0}, 6:{'Adapter':1, 'Port':1}, 7:{'Adapter':1, 'Port':2}, 8:{'Adapter':1, 'Port':3}
    }

with open('sample.topo', 'r') as f:
    stopo = json.load(f)

# Create a skeleton GNS3 toplogy file

project = {
   'auto_close': True,
   'auto_open': False,
   'auto_start': False,
   'name': stopo['name'],
   'project_id': str(uuid.uuid1()),
   'revision': 8,
   'scene_height': 1000,
   'scene_width': 2000,
   'show_grid': False,
   'show_interface_labels': True,
   'show_layers': False,
   'snap_to_grid': False,
   'type': 'topology',
   'version': '2.1.11',
   'zoom': 100
}

# Get list for nodes from list of links that are stored in stopo['topology']

nodes_on_link = {}
nodes = []

for link in stopo['topology']:
  nol = re.findall('[a-zA-Z0-9]+', link)
  unique_nols = list(set(nol))
  unique_nols.sort()
  if len(unique_nols) > 1:
    nodes_on_link[link] = unique_nols
  for n in unique_nols:
    nodes.append(n)

nodes = list(set(nodes))
nodes.sort() # for cosmetic reasons

topology = {
  'computes': [],
  'drawings': [],
  'links': [],
  'nodes': []
}

# Add nodes into the topology:

# Create a dictionary with each node's number:
node_no = {}
for n in nodes:
  node_no[n] = re.search('[0-9]+', n).group(0)
  # if node_no[n] is None: FOR v2: assign a semi-random number
  assert int(node_no[n]) < 21 , 'At this time, only node numbers < 21 are supported'


for i in range(len(nodes)):
  device = {
      'compute_id': __Compute__,
      'console': __BaseConsole__+i+1,
      'console_type': 'telnet',
      'first_port_name': None,
      'height': 45,
      'label': {
            'text': nodes[i],
            'x': None,
            'y': -25
            },
      'name': nodes[i],
      'node_id': str(uuid.uuid1()),
      'node_type': 'iou',
      'port_name_format': 'Ethernet{segment0}/{port0}',
      'port_segment_size': 4,
      'properties': {
          'application_id': 1,
          'ethernet_adapters': 1,
          'l1_keepalives': False,
          'md5sum': '45e99761a95cbd3ee3924ecf0f3d89e5',
          'nvram': 64,
          'path': __IOUImage__,
          'ram': 256,
          'serial_adapters': 0,
          'use_default_iou_values': True
          },
      'symbol': ':/symbols/router.svg',
      'width': 66,
      }
  topology['nodes'].append(device)



  
# Generate skeleton configurations:
cfg={}
for n in nodes:
  cfg[n] = skelecfg(n)

# Determine subnet numbers:
subnets = {}
link_subnets = {}
for n in nodes:
    subnets[n] = list('')

for link in stopo['topology']:
  nodes_on_link = re.findall('[a-zA-Z0-9]+', link)
  nodes_on_link = list(set(nodes_on_link)) # Sanitize if there is a link to self
  nodes_on_link.sort()
  lsub = '' # the link's subnet
  if len(nodes_on_link) > 2:
    lsub = lsub + node_no[nodes_on_link[0]]
    lsub = lsub + node_no[nodes_on_link[1]]
    lsub = lsub + node_no[nodes_on_link[2]]
    if int(lsub) > 254:
      assert int(node_no[nodes_on_link[0]]) < 254, 'Node\'s number is greater than 254'
      if len(node_no[nodes_on_link[1]]) > 1:
        lsub = '1' + node_no[nodes_on_link[1]][1]
      else:
        lsub = '1' + node_no[nodes_on_link[1]][0]
      if len(node_no[nodes_on_link[2]]) > 1:
        lsub = lsub + node_no[nodes_on_link[2]][1]
      else:
        lsub = lsub + node_no[nodes_on_link[2]][0]
    assert int(lsub) < 255, 'Subnet greater than 254'
  elif len(nodes_on_link) == 2:
    lsub = lsub + node_no[nodes_on_link[0]]
    lsub = lsub + node_no[nodes_on_link[1]]
    if int(lsub) > 254:
      assert int(node_no[nodes_on_link[0]]) < 254, 'Node\'s number is greater than 254'
      lsub = node_no[nodes_on_link[0]]
      lsub = lsub + node_no[nodes_on_link[1]][1]
    assert int(lsub) < 255, 'Subnet greater than 254'
  else:
    continue
  link_subnets[link]=lsub
  for n in nodes_on_link:
    subnets[n].append(lsub)

connections = []

for n in nodes:
  interf_count = 1
  conf_str = cfg[n].ioscfg
  for lsub in subnets[n]:
    conf_str.append('!')
    conf_str.append('interface ' + EthernetInterface[interf_count])
    conf_str.append(' ip address 10.0.' + lsub + '.' + node_no[n] + ' 255.255.255.0')
    conf_str.append(' no shutdown')
    # find link:
    for link, subn in link_subnets.items():
      if subn == lsub:
        connections.append({'node': n, 'link': link, 'subnet': lsub, 'interface': interf_count})
    interf_count += 1
  cfg[n] = ciscoconfparse.CiscoConfParse(conf_str)
  
# Apply any OSPF configuration
if 'conf' in stopo:
  # check if there is an OSPF section:
  if 'OSPF_areas' in stopo['conf']:
    areas = stopo['conf']['OSPF_areas']
    # print ('OSPF area configuration: '+ str(areas))
    for link, area in areas.items():
      # Verify that the link exists in the topology
      if link not in stopo['topology']:
        # print('Link ' + link + ' only exists in OSPF area configuration but not in topology description')
        continue
      # Add OSPF area information into connections list:
      for conn in connections:
        if conn['link'] == link:
          conn['OSPF_area'] = area
          if len(re.findall('-', link)) == 1:
            conn['OSPF_net_type'] = 'p2p'
          elif len(re.findall('-', link)) > 1:
            conn['OSPF_net_type'] = 'broadcast'
        
  if 'Loops' in stopo['conf']:
    # Add Loopback interfaces to configuration
    loopbacks = stopo['conf']['Loops']
    for node, nol in loopbacks.items():
      if node not in nodes:
        print('Node ' + node + ' is only referenced in the Loops configuration section; will be ignored')
        continue
      # Come up with Loopback IP addresses:
      nn = node_no[node] # this node's number
      conf_str = cfg[node].ioscfg
      nol = int(nol)
      if nol > 0:
        conf_str.append('!')
        conf_str.append('interface Loopback 1')
        conf_str.append(' ip address ' + nn + '.' + nn + '.' + nn + '.' + nn + ' 255.255.255.255')
        conf_str.append(' no shutdown')
      if nol > 1:
        conf_str.append('!')
        conf_str.append('interface Loopback 2')
        conf_str.append(' ip address 192.' + nn + '.' + nn + '.' + nn + ' 255.255.255.0')
        conf_str.append(' no shutdown')
        conf_str.append(' ip ospf network point-to-point')
      if nol > 2:
        conf_str.append('!')
        conf_str.append('interface Loopback 3')
        conf_str.append(' ip address 193.0.' + nn + '.' + nn + ' 255.255.255.0')
        conf_str.append(' no shutdown')
        conf_str.append(' ip ospf network point-to-point')
      if nol > 3:
        conf_str.append('!')
        conf_str.append('interface Loopback 4')
        conf_str.append(' ip address 193.0.1.'  + nn + ' 255.255.255.0')
        conf_str.append(' no shutdown')
        conf_str.append(' ip ospf network point-to-point')
      if nol > 4:
        print('Only 4 Loopback interfaces have been created, more are not yet supported')
      cfg[node] = ciscoconfparse.CiscoConfParse(conf_str)
      

for conn in connections:
  if 'OSPF_area' in conn:
    conf = cfg[conn['node']].ioscfg
    stanza_start = conf.index('interface ' + EthernetInterface[conn['interface']])
    addr_command = stanza_start + 1
    while addr_command < len(conf) and conf[addr_command][0] == ' ' :
      if conf[addr_command].startswith(' ip address'):
        conf.insert(addr_command + 1, ' ip ospf 1 area ' + str(conn['OSPF_area']))
        if 'OSPF_net_type' in conn:
          if conn['OSPF_net_type'] == 'p2p':
            conf.insert(addr_command + 2, ' ip ospf network point-to-point')
        break
        #FOR v2: Must handle when the addr_command is the index of last list item of "conf"
    
    nn = node_no[conn['node']]
    conf.insert(14, '!')
    conf.insert(15, 'router ospf 1')
    conf.insert(16, ' router-id ' + nn + '.' + nn + '.' + nn + '.' + nn)
    conf.insert(17, '!')
    # now push everything back into cfg:
    cfg[conn['node']] = ciscoconfparse.CiscoConfParse(conf)

# Create links list of dictionaries:
links = []

for link, subn in link_subnets.items():
  this_link = {}
  this_link['name'] = link
  this_link['nodes'] = []
  for conn in connections:
    link_data = {}
    if conn['link'] == link:
      link_data['name'] = conn['node']
      # Find the node's UUID
      for node in topology['nodes']:
        if node['name'] == link_data['name']:
          link_data['node_id'] = node['node_id']
          port_segment_size = node['port_segment_size']
          break
      # Determine Adapter and Port numbers from conn['interface']
      link_data['adapter_number'] = AdapterPort[conn['interface']]['Adapter']
      link_data['port_number'] = AdapterPort[conn['interface']]['Port']
      this_link['nodes'].append(link_data)
  # Now we've checked all connection endpoints from the connections list.
  # We now add the  results (stored within the this_link dictionary) to the links list:
  links.append(this_link)

# Sanitize links list by making all links point-to-point:
# Resolve links with multiple nodes on a common segment (aka add any necessary switches):
max_switch_number = 0
physical_links = []
switches = []

for link in links:
  plink = {}
  if len(link['nodes']) == 2:
    physical_links.append(link)
  elif len(link['nodes']) > 2:
    # Create a intermediary (switch)
    max_switch_number += 1
    sw_name = 'Switch'+str(max_switch_number)
    sw_uuid = str(uuid.uuid1())
    sw_port = 0
    for node_edge in link['nodes']:
      plink = {} # Create an empty dictionary for the current physical link:
      plink['name'] = sw_name + '-' + node_edge['name']
      plink['nodes'] = []
      plink['nodes'].append(node_edge)
      plink['nodes'].append({'name':sw_name, 'node_id':sw_uuid, 'adapter_number':0, 'port_number':sw_port})
      sw_port += 1
      physical_links.append(plink)
    
    switches.append({'name':sw_name, 'node_id': sw_uuid, 'port_segment_size':sw_port, \
                     'console':__BaseConsole__ + max(list(map(int, list(node_no.values())))) + max_switch_number})

for switch in switches:
  new_switch = {
    'compute_id': __Compute__,
    'console': switch['console'] ,
    'console_type': 'telnet',
    'first_port_name': None,
    'height': 32,
    'name': switch['name'],
    'node_id': switch['node_id'],
    'node_type': 'ethernet_switch',
    'port_name_format': 'Ethernet{0}',
    'port_segment_size': switch['port_segment_size'],
    'properties': {
        'ports_mapping': []
      },
      'symbol': ':/symbols/ethernet_switch.svg',
      'width': 72
  }
  
  for i in range(switch['port_segment_size']):
    eth_port = {"name": 'Ethernet' + str(i), "port_number": i, "type": "access", "vlan": 1}
    new_switch['properties']['ports_mapping'].append(eth_port)

  # Push the newly created switch into the nodes list of topology['nodes']
  topology['nodes'].append(new_switch)
    

# Add links into the topology:

for link in physical_links:
  
  nodes_on_link = link['nodes']
  # print('Nodes on Link:' + str(nodes_on_link))
  assert len(link['nodes']) == 2, "Non p2p link - cannot add to GNS3 JSON"
  
  # Initialise link data structure (tlink: topology link )
  tlink = { 'filters': {}, 'link_id': str(uuid.uuid1()), 'nodes': [],
           'suspend': False,
           'link_type': 'ethernet'}
  
  # Populate the nodes list:
  for node in nodes_on_link:
    # Initialize this node's dictionary: (which will later be added to the tlink 'nodes' list)
    glnode = {'adapter_number': node['adapter_number'], 
              'node_id': node['node_id'], 
              'port_number': node['port_number']}
    tlink['nodes'].append(glnode)   
  
  # Not the tlink dictionary is done. Push it into topology['links']:
  topology['links'].append(tlink)

project['topology']=topology

# Before dumping into file, validate the project JSON:
with open('gns3_topo_schema.json', 'r') as f:
  gns3toposchema=json.load(f)

jsonschema.validate(project,gns3toposchema)

gns3_filename = re.sub(r' ', r'-', stopo['name']) + '.gns3'

if __WRITETOFILES__:
  with open(gns3_filename, 'w') as f:
    json.dump(project, f, indent=4)

  # Write configurations to startup-config.cfg files:

  if not os.path.exists('./project-files/iou'):
    os.makedirs('./project-files/iou')

  for node, config in cfg.items():
    node_id = 'error'
    for n in topology['nodes']:
      if n['name'] == node:
        node_id = n['node_id']
        break
    
    assert node_id != 'error', 'Node_id could not be found'
    
    if not os.path.exists('./project-files/iou/' + node_id):
      os.makedirs('./project-files/iou/' + node_id)
    
    with open('./project-files/iou/' + node_id + '/startup-config.cfg', 'w') as f:
      f.write('\n'.join(cfg[node].ioscfg))
      f.write('\n') # Lest we get the %PARSER-4-BADCFG: Unexpected end of configuration file. SYSLOG message








