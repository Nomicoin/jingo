#!/usr/bin/env python

import argparse, yaml, json
from syncthing import Device, Folder

def pprint(json_string):
    print json.dumps(json_string, sort_keys=True, indent=2)

with open('/home/v/dev/viki/meridion-dev.yaml') as f:
    config = yaml.load(f.read()) 

    device = Device(config)
    pprint (device.ping())
    pprint (device.getId())
#    stconfig = device.getConfig()
#    pprint (stconfig)
#    pprint (device.setConfig(stconfig))
#    pprint (device.getVersion())
#    pprint (device.isValidDeviceId(device.getId()))
#    pprint (device.isInSync())
#    pprint (device.getCompletion(device.getId()))
#    pprint (device.getSystemInfo())
#    pprint (device.getErrors()['errors'])
#    pprint (device.getDevices())
    folder = Folder(config)
    pprint (folder.getFolders())
#    pprint (folder.addFolder("abc", "/test"))
#    pprint (folder.delFolder("abc"))
#    pprint (folder.delFolder("abc~1"))
#    pprint (folder.delFolder("abc~2"))
    print "============="
#    pprint (folder.linkDevice("abc", "VYTBJPH-LSLKVCC-V6YVD6W-R6YATLR-ZLYHA4W-PXXEHK4-UY54PAQ-OCBXDAJ"))
    pprint (folder.unLinkDevice('abc', 'VYTBJPH-LSLKVCC-V6YVD6W-R6YATLR-ZLYHA4W-PXXEHK4-UY54PAQ-OCBXDAJ'))
#    pprint (folder.ping())
#    pprint (folder.getFolderStatus(""))
#    pprint (device.setPing())
#    pprint (device.delDevice("KKDOKGF-SREFXBV-RMK5BNQ-AKHE4DP-4C5GWOM-AQ6L6TR-PG3RPPZ-FONTJQ2"))
#    pprint (device.addDevice("KKDOKGF-SREFXBV-RMK5BNQ-AKHE4DP-4C5GWOM-AQ6L6TR-PG3RPPZ-FONTJQ2", "Mojo"))
#    pprint (device.restart())
    print "End."
