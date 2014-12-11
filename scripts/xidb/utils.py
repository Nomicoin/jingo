import os, json

def createLink(xid, cid):
    xidRef = str(xid)[:8]
    cidRef = str(cid)[:8]
    return os.path.join(xidRef, cidRef)

def makeDirs(path):
    dirName = os.path.dirname(path)
    if not os.path.exists(dirName):
        os.makedirs(dirName)

def saveFile(path, data):
    makeDirs(path)
    with open(path, 'w') as f:
        f.write(data)

def saveJSON(path, obj):
    res = json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))
    saveFile(path, res + "\n")

def saveMetadata(meta):
    path = meta['base']['path']
    saveJSON(path, meta)
    print ">>> saveMetadata", path, meta
