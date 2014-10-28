import png, array
import PIL.Image, PIL.ExifTags
from io import BytesIO

class Text:
    def addMetadata(self, blob, metadata):
        if not blob.is_binary:
            lines = blob.data.count('\n')
            metadata['text'] = { 'lines': lines }

class Markdown:
    def addMetadata(self, blob, metadata):
        ext = metadata['asset']['ext']
        if ext == '.md':
            metadata['markdown'] = { 'asHtml5': 'xlink' }
        
class Image(object):
    def __init__(self, format):
        self.format = format
        self.width = 0
        self.height = 0
        self.colorDepth = 0

    def addImageMetadata(self, metadata):
        metadata['image'] = { 
            'width': self.width,
            'height': self.height,
            'colorDepth': self.colorDepth,
            'format': self.format
        }
        metadata['asset']['content-type'] = self.format

class Png(Image):
    def __init__(self):
        super(Png, self).__init__("image/png")

    def addMetadata(self, blob, metadata):
        ext = metadata['asset']['ext']
        if ext != '.png':
            return

        try:
            data = array.array('B', blob.data)
            r = png.Reader(data)
            self.width, self.height, pixels, meta = r.read()
            metadata['png'] = meta
            self.addImageMetadata(metadata)
        except:
            print "error reading png", metadata['asset']['name']

class Jpeg(Image):
    def __init__(self):
        super(Jpeg, self).__init__("image/jpeg")

    def addMetadata(self, blob, metadata):
        ext = metadata['asset']['ext']
        if not ext in ['.jpg', '.jpeg']:
            return

        try:
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
            self.width = exif['ExifImageWidth']
            self.height = exif['ExifImageHeight']
            self.addImageMetadata(metadata)
        except:
            print "error reading jpeg", metadata['asset']['name']

class Gif(Image):
    def __init__(self):
        super(Gif, self).__init__("image/gif")

    def addMetadata(self, blob, metadata):
        ext = metadata['asset']['ext']
        if ext != '.gif':
            return
        metadata['gif'] = {}
        self.addImageMetadata(metadata)

allTypes = [
    Text(),
    Markdown(),
    Png(),
    Jpeg(),
    Gif()
]


    
