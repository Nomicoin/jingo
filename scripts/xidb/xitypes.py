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
        
def addImageMetadata(metadata, width, height, colorDepth, format):
    metadata['image'] = { 
        'width': width,
        'height': height,
        'colorDepth': colorDepth,
        'format': format
    }
    metadata['asset']['content-type'] = format

class Png:
    def addMetadata(self, blob, metadata):
        ext = metadata['asset']['ext']
        if ext != '.png':
            return
        try:
            data = array.array('B', blob.data)
            r = png.Reader(data)
            width, height, pixels, meta = r.read()
            metadata['png'] = meta
            addImageMetadata(metadata, width, height, 0, "image/png")

        except:
            print "error reading png", metadata['asset']['name']

class Jpeg:
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
            width = exif['ExifImageWidth']
            height = exif['ExifImageHeight']
            addImageMetadata(metadata, width, height, 0, "image/jpeg")
        except:
            print "error reading jpeg", metadata['asset']['name']

class Gif:
    def addMetadata(self, blob, metadata):
        ext = metadata['asset']['ext']
        if ext != '.gif':
            return
        metadata['gif'] = {}
        addImageMetadata(metadata, 0, 0, 0, "image/gif")

allTypes = [
    Text(),
    Markdown(),
    Png(),
    Jpeg(),
    Gif()
]


    
