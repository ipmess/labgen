# labgen
A GNS3 lab topology and configuration file generator

# Usage

In is current state, the program reads the sample.topo file to find the desired topology, and to generate a skeleton configuration to achieve simple connectivity. Just run labgen.py and it will read sample.topo and create the output files and directories.

The assumption is that the generated lab is a lab of IOU routers, possibly connected with the GNS3 internal switch.

## sample.topo

sample.topo is the JSON input file for labgen. labgen reads the file and loads the desired topology. From there, it builds a GNS3-compliant .gns3 file and creates the relevant IOS configuration files.

The structure of sample.topo is simple (and i like to believe intuitive). There is no JSON schema yet for sample.topo, but it seems necessary to clearly describe the file's structure.

### name
The first tuple describes the topology's name

### topology
This is the topology, as described by a list of links. The list consists of node names joined by a dash ('-'), formated as strings.  For example, "R1-R2" describes a link between R1 and R2. An "R1-R2-R3" string describes a shared segment to which all these three routers are connected to. The GNS3 topology file as well as the basic IP addressing scheme and configuration can be determined from this one list of links. As stated earlier, the described links are links between IOU routers.

### conf
The conf dictionary contains some extra items that are often useful when setting up GNS3 Labs. Only two key alues are currently implemented:
* OSPF_areas
* Loops

### OSPF_areas
OSPF_areas is a dictionary where each key is a link as described in the topology list earlier, and the value is the OSPF area to which the link is assigned. If a key refers to a link that is not described in the topology, it is ignored.

### Loops
Loops is a dictionary where each key is a router referred to in the topology list. If a key contains a string value of a router that is not referenced within the topology as being attached to a link, it is ignored. The value of the key is the number of Loopback interfaces that will be added into the generated configuration.

## Dependencies
labgen requires the installation of `ciscoconfparse`, `jsonschema` and `uuid`. These can be installed using the following commands:
~~~~
pip install ciscoconfparse
pip install jsonschema
pip install uuid
~~~~

## Output
labgen writes a .gns3 file to the current working directory where it resides and also creates a *project-files/iou/* directory where it writes the startup-configs for each IOU router.

GNS3 on my Ubuntu workstation reads the startup-configs from the *project-files/iou/* directory, whereas on Windows, the directory is largely ignored. On a Windows test workstation that uses a GNS3 VM, you will have to manually copy each startup config to the */opt/gns3/projects/project-uuid/project-files/iou/device-uuid/* directories.