#
# This library defines a Device and Folder class for Syncthing API
#
import sys, json, httplib2

http = httplib2.Http(".cache")

def get(baseurl, path):
    # Get content from specified http URL
    resp, content = http.request(baseurl + path, "GET")
    return content

def post(key, body, baseurl, path):
    # Post to specified http URL. Returns response and content objects.
    headers = {'X-API-Key': key}
    resp, content = http.request(baseurl + path, "POST", body=body, headers=headers)
    return resp, content

def newDevice(deviceId, deviceName, introducer=False):
    # Returns a Device JSON object compatible with Syncthing
    return {"Addresses": [
                "dynamic"
            ], 
            "CertName": "",
            "Compression": True,
            "DeviceID": deviceId,
            "Introducer": introducer,
            "Name": deviceName}

def newFolder(folderId, folderPath, deviceList, readOnly=True, rescan=60):
    # Returns a Folder JSON object compatible with Syncthing
    return {
      "Copiers": 1, 
      "Devices": deviceList,
      "Finishers": 1, 
      "ID": folderId,
      "IgnorePerms": False, 
      "Invalid": "", 
      "LenientMtimes": False, 
      "Path": folderPath,
      "Pullers": 16, 
      "ReadOnly": readOnly, 
      "RescanIntervalS": rescan, 
      "Versioning": {
        "Params": {}, 
        "Type": ""
      }
    }

class Device:
    # Performs Syncthing Device operations using REST API
    def __init__(self, appConfig):
        self.baseurl = appConfig['syncthing']['baseurl']
        self.apikey = appConfig['syncthing']['apikey']

    def ping(self):
        # Basic ping/pong to test connection with Syncthing API. 
        # Returns {"ping": "pong"} object if successful
        return json.loads(get(self.baseurl, "/ping"))

    def setPing(self):
        # Basic ping/pong to test POST connecting with Syncthing API.
        # Returns {"ping": "pong"} object if successful
        resp, content = post(self.apikey, "", self.baseurl, "/ping")
        return json.loads(content)

    def restart(self):
        # Restarts Syncthing. Returns true if successful.
        resp, content = post(self.apikey, "", self.baseurl, "/restart")
        return resp['status']=='200'    

    def isValidDeviceId(self, deviceid):
        # Returns true if provided with a valid Syncthing device id
        content = get(self.baseurl, "/deviceid?id=" + deviceid)
        return bool('id' in json.loads(content))

    def isInSync(self):
        # Returns true if Syncthing engine is in sync with latest updates
        content = get(self.baseurl, "/config/sync")
        return bool(json.loads(content)['configInSync'])

    def getVersion(self):
        # Returns Syncthing version information
        return json.loads(get(self.baseurl, "/version"))

    def getErrors(self):
        # Returns Syncthing errors list
        return json.loads(get(self.baseurl, "/errors"))

    def getConfig(self):
        # Returns Syncthing configuration
        return json.loads(get(self.baseurl, "/config"))

    def setConfig(self, config):
        # Posts Syncthing configuration.  Returns True if successful
        resp, content = post(self.apikey, json.dumps(config), self.baseurl, "/config")
        return resp['status']=='200'

    def getSystemInfo(self):
        # Returns Syncthing system information
        return json.loads(get(self.baseurl, "/system"))

    def getId(self):
        # Extracts ID from Syncthing system information
        return self.getSystemInfo()['myID']

    def getConnections(self):
        # Returns Syncthing connection data
        return json.loads(get(self.baseurl, "/connections"))

    def getCompletion(self, deviceid):
        # Returns remote device sync completion percentage
        content = get(self.baseurl, "/completion?device=" + deviceid)
        return json.loads(content)['completion']

    def getDevices(self):
        # Extracts collection of registered Syncthing devices from received config data
        return self.getConfig()['Devices']

    def addDevice(self, deviceId, deviceName):
        # Adds a new device to the Syncthing configuration.  
        # Returns True if successful.
        newDev = newDevice(deviceId, deviceName)
        config = self.getConfig()
        config["Devices"].append(newDev)
        return self.setConfig(config)
        
    def delDevice(self, deviceId):
        # Removes a device from the Syncthing configuration. 
        # Returns number of devices deleted or -1 if error occurs in setConfig()
        newDeviceList = []
        deviceMatch = 0
        config = self.getConfig()
        for device in config["Devices"]:
            if device["DeviceID"] != deviceId:
                # These are not the devices you are looking for
                newDeviceList.append(device)
            else:
                deviceMatch += 1
        if deviceMatch > 0:
            config["Devices"] = newDeviceList
            if not self.setConfig(config):
                deviceMatch = -1
        return deviceMatch

    def getDiscovery(self):
        # Returns Syncthing discovered devices
        return json.loads(get(self.baseurl, "/discovery"))

    def getUpgrade(self):
        # Returns Syncthing upgrade available information
        return json.loads(get(self.baseurl, "/upgrade"))

    def isUpgradable(self):
        # Returns true if Syncthing upgrade is available
        content = get(self.baseurl, "/upgrade")
        return bool('newer' in json.loads(content))

class Folder:
    def __init__(self, appConfig):
        self.baseurl = appConfig['syncthing']['baseurl']
        self.apikey  = appConfig['syncthing']['apikey']
        self.rootdir = appConfig['syncthing']['syncrootdir']

    def ping(self):
        # Basic ping/pong to test connection with Syncthing API. 
        return json.loads(get(self.baseurl, "/ping"))
   
    def getFolders(self):
        # Extracts collection of registered Syncthing folders from received config data
        return self.getConfig()['Folders']

    def getFolderStatus(self, folderid):
        # Returns status of specified Syncthing shared folder
        return json.loads(get(self.baseurl, "/model?folder=" + folderid))
    
    def getConfig(self):
        # Returns Syncthing configuration
        return json.loads(get(self.baseurl, "/config"))

    def setConfig(self, config):
        # Posts Syncthing configuration.  Returns True if successful
        resp, content = post(self.apikey, json.dumps(config), self.baseurl, "/config")
        return resp['status']=='200'

    def restart(self):
        # Restarts Syncthing. Returns true if successful.
        resp, content = post(self.apikey, "", self.baseurl, "/restart")
        return resp['status']=='200'    

    def getSystemInfo(self):
        # Returns Syncthing system information
        return json.loads(get(self.baseurl, "/system"))

    def getId(self):
        # Extracts ID from Syncthing system information
        return self.getSystemInfo()['myID']

    def addFolder(self, folderId, folderPath):
        # Adds a new device to the Syncthing configuration. Returns True if successful.
        device = {}
        deviceList = []
        device['DeviceID'] = self.getId()
        deviceList.append(device)
        
        myNewFolder = newFolder(folderId, self.rootdir + folderPath, deviceList)
        
        config = self.getConfig()
        config["Folders"].append(myNewFolder)
        return self.setConfig(config)
        
    def delFolder(self, folderId):
        # Removes a device from the Syncthing configuration. 
        # Returns number of devices deleted or -1 if error occurs in setConfig()
        newFoldersList = []
        folderMatch = 0
        config = self.getConfig()
        for folder in config["Folders"]:
            if folder["ID"] != folderId:
                # These are not the folders you are looking for
                newFoldersList.append(folder)
            else:
                folderMatch += 1
        if folderMatch > 0:
            config["Folders"] = newFoldersList
            if not self.setConfig(config):
                folderMatch = -1
        return folderMatch

    def linkDevice(self, folderId, deviceId):
        # Adds device ID to shared folder's distribution.  Returns True if config was changed.
        config = self.getConfig()
        configModified = False
        for folder in config['Folders']:
            if folder["ID"] == folderId:
                deviceList = folder['Devices']
                devInList = False
                for device in deviceList:
                    if device["DeviceID"] == deviceId:
                        devInList = True
                if not devInList:
                    newDevice={}
                    newDevice['DeviceID'] = deviceId
                    deviceList.append(newDevice)
                    folder['Devices'] = deviceList
                    configModified = True
        if configModified:
            configModified = self.setConfig(config)
        return configModified

    def unLinkDevice(self, folderId, deviceId):
        # Removes device ID from shared folder's distribution.
        # Returns number of devices deleted (should be 1), or -1 if unable to update devices.
        config = self.getConfig()
        newDeviceList = []
        deviceMatch = 0
        for folder in config['Folders']:
            if folder['ID'] == folderId:
                for device in folder['Devices']:
                    if device["DeviceID"] != deviceId:
                        # These are not the devices you are looking for
                        newDeviceList.append(device)
                    else:
                        deviceMatch += 1
                if deviceMatch > 0:
                    folder['Devices'] = newDeviceList
        if deviceMatch > 0:
            if not self.setConfig(config):
                deviceMatch = -1
        return deviceMatch


##EOF
