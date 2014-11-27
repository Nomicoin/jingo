import png, array, os, re, json
import PIL.Image, PIL.ExifTags
import markdown, pygit2
import genxid
from io import BytesIO
from markdown.extensions.wikilinks import WikiLinkExtension
from markdown.extensions.tables import TableExtension

class Asset(object):
    def __init__(self):
        self.name = ''
        self.contentType = ''
        self.title = ''
        self.xlink = ''
        self.vlink = ''

    def init(self):
        asset = self.metadata['asset']
        self.name = asset['name']
        base = self.metadata['base']
        self.xlink = base['xlink']
        self.vlink = base['commit'][:8]

    def isValid(self):
        return False

    def checkExtension(self, extensions):
        ext = self.metadata['asset']['ext']
        return ext in extensions

    def addMetadata(self):
        self.metadata['asset']['content-type'] = self.contentType
        self.metadata['asset']['title'] = self.title

class Text(Asset):
    def __init__(self):
        super(Text, self).__init__()

    def init(self):
        super(Text, self).init()

    def isValid(self):
        return not self.blob.is_binary

    def addMetadata(self):
        text = self.blob.data.decode('utf-8')
        lines = text.count('\n')
        self.metadata['text'] = { 'lines': lines }

        self.contentType = "text/plain"
        super(Text, self).addMetadata()

def urlBuilder(label, base, end):
    url = label.replace(" ", "-")
    return url

class Markdown(Text):
    def __init__(self):
        super(Markdown, self).__init__()

    def init(self):
        super(Markdown, self).init()

        self.page = self.name[:-3] # remove .md extension
        self.plink = os.path.join(self.vlink, self.page)

        title = os.path.basename(self.name)
        title = os.path.splitext(title)[0]
        self.title = title.replace("-", " ")

    def isValid(self):
        return self.checkExtension(['.md']) and super(Markdown, self).isValid()

    def generateHtml(self):
        try:
            extensions=[TableExtension(),
                        WikiLinkExtension(html_class='internal',
                                          build_url=urlBuilder)]
            source = self.blob.data.decode('utf-8')
            html = markdown.markdown(source, extensions=extensions)

            self.metadata['as'] = { 'html': html }
        except Exception, e:
            print "markdown processing failed on", self.name, str(e)

    def addMetadata(self):
        super(Markdown, self).addMetadata()

        self.generateHtml()

        self.metadata['markdown'] = { 
            'page': self.page,
            'plink': self.plink
        }

class Comment(Markdown):
    def __init__(self):
        super(Comment, self).__init__()

    def init(self):
        super(Comment, self).init()

        try:
            self.xaction = json.loads(self.snapshot.commit.message)
        except:
            self.xaction = False
        
        if self.isValid():
            ref = self.xaction['ref']
            # todo: retrieve reference's metadata
            author=self.xaction['author']
            # todo: retrieve author's name from metadata
            self.title = "Comment on %s by %s" % (ref, author)

    def isComment(self):
        return (self.xaction and 
                'type' in self.xaction and 
                self.xaction['type'] == 'comment' and 
                'ref' in self.xaction and 
                'author' in self.xaction)

    def isValid(self):
        return self.isComment() and super(Comment, self).isValid()

    def addMetadata(self):
        super(Comment, self).addMetadata()

        self.metadata['comment'] = dict(
            ref=self.xaction['ref'], 
            author=self.xaction['author'], 
            authorName=self.snapshot.commit.author.name,
            authorEmail=self.snapshot.commit.author.email,
        )

class Vote(Text):
    def __init__(self):
        super(Vote, self).__init__()

    def init(self):
        super(Vote, self).init()

        try:
            self.xaction = json.loads(self.snapshot.commit.message)
        except:
            self.xaction = False
        
        if self.isValid():
            ref = self.xaction['ref']
            # todo: retrieve reference's metadata
            author=self.xaction['author']
            # todo: retrieve author's name from metadata
            self.title = "Vote on %s by %s" % (ref, author)

    def isVote(self):
        return (self.xaction and 
                'type' in self.xaction and 
                self.xaction['type'] == 'vote' and 
                'ref' in self.xaction and 
                'author' in self.xaction)

    def isValid(self):
        return self.isVote() and super(Vote, self).isValid()

    def addMetadata(self):
        super(Vote, self).addMetadata()

        self.metadata['vote'] = dict(
            ref=self.xaction['ref'], 
            author=self.xaction['author'], 
            authorName=self.snapshot.commit.author.name,
            authorEmail=self.snapshot.commit.author.email,
        )

class Image(Asset):
    def __init__(self):
        super(Image, self).__init__()
        self.format = ''
        self.width = 0
        self.height = 0
        self.colorDepth = 0

    def init(self):
        super(Image, self).init()

    def isValid(self):
        return self.blob.is_binary

    def addMetadata(self):
        self.metadata['image'] = { 
            'width': self.width,
            'height': self.height,
            'colorDepth': self.colorDepth,
            'format': self.format
        }
        self.contentType = self.format
        super(Image, self).addMetadata()

class Png(Image):
    def __init__(self):
        super(Png, self).__init__()

    def init(self):
        super(Png, self).init()
        self.format = "image/png"

    def isValid(self):
        return self.checkExtension(['.png']) and super(Png, self).isValid()

    def addMetadata(self):
        try:
            data = array.array('B', self.blob.data)
            r = png.Reader(data)
            self.width, self.height, pixels, meta = r.read()
            self.metadata['png'] = meta
            super(Png, self).addMetadata()
        except:
            print "error reading png", self.name

class Jpeg(Image):
    def __init__(self):
        super(Jpeg, self).__init__()

    def init(self):
        super(Jpeg, self).init()
        self.format = "image/jpeg"

    def isValid(self):
        return self.checkExtension(['.jpg', '.jpeg']) and super(Jpeg, self).isValid()

    def addMetadata(self):
        try:
            bio = BytesIO(self.blob.data)
            print bio
            bio.seek(0)
            img = PIL.Image.open(bio)
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            self.metadata['jpeg'] = exif
            self.width = exif['ExifImageWidth']
            self.height = exif['ExifImageHeight']
            super(Jpeg, self).addMetadata()
        except:
            print "error reading jpeg", self.name

class Gif(Image):
    def __init__(self):
        super(Gif, self).__init__()

    def init(self):
        super(Gif, self).init()
        self.format = "image/gif"

    def isValid(self):
        return self.checkExtension(['.gif']) and super(Gif, self).isValid()

    def addMetadata(self):
        self.metadata['gif'] = {}
        super(Gif, self).addMetadata()

# put leaf classes first because only first valid type will be used to generate metadata
allTypes = [
    lambda : Vote(),
    lambda : Comment(),
    lambda : Markdown(),
    lambda : Text(),
    lambda : Png(),
    lambda : Jpeg(),
    lambda : Gif(),
]
