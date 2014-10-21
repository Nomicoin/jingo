import png, array
import PIL.Image, PIL.ExifTags
from io import BytesIO

otherTypes = {
    '.md': 'text/markdown',
    '.jade': 'text/jade',
    '.toml': 'text/toml',
    '.yaml': 'text/yaml'
} 

class Text:
    def addMetadata(self, asset, blob, metadata):
        if blob.is_binary:
            lines = 0
        else:
            lines = blob.data.count('\n')

        metadata['text'] = { 'lines': lines }
        return metadata

class Markdown:
    def __init__(self):
        self.text = Text()

    def addMetadata(self, asset, blob, metadata):
        self.text.addMetadata(asset, blob, metadata)
        metadata['markdown'] = { 'asHtml5': 'xlink' }
        return metadata
        
class Image:
    def addMetadata(self, asset, blob, metadata):
        metadata['image'] = { 
            'width': 0,
            'height': 0,
            'colorDepth': 0
        }
        return metadata

class Png:
    def __init__(self):
        self.image = Image()

    def addMetadata(self, asset, blob, metadata):
        #self.image.addMetadata(asset, blob, metadata)
        try:
            data = array.array('B', blob.data)
            r = png.Reader(data)
            width, height, pixels, meta = r.read()
            metadata['image'] = {
                'width': width,
                'height': height
            }
            metadata['png'] = meta
            print metadata
        except:
            print "error reading png", asset.name

        return metadata

class Jpeg:
    def __init__(self):
        self.image = Image()

    def addMetadata(self, asset, blob, metadata):
        #self.image.addMetadata(asset, blob, metadata)
        try:
            data = array.array('B', blob.data)
            bio = BytesIO(blob.data)
            print bio
            bio.seek(0)
            img = PIL.Image.open(bio)
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            metadata['jpeg'] = exif
            metadata['image'] = {
                'width': exif['ExifImageWidth'],
                'height': exif['ExifImageHeight']
            }
            print metadata
        except:
            print "error reading jpeg", asset.name
        return metadata

class Gif:
    def __init__(self):
        self.image = Image()

    def addMetadata(self, asset, blob, metadata):
        self.image.addMetadata(asset, blob, metadata)
        metadata['gif'] = {}
        return metadata

typeIndex = {}
typeIndex['text/plain'] = Text()
typeIndex['application/javascript'] = Text()
typeIndex['text/x-python'] = Text()
typeIndex['text/markdown'] = Markdown()
typeIndex['image/png'] = Png()
typeIndex['image/jpeg'] = Jpeg()
typeIndex['image/gif'] = Gif()
