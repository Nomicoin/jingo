import png, array, os, re, json
import PIL.Image, PIL.ExifTags
import markdown, pygit2
import genxid
from io import BytesIO
from pygit2 import Signature
from markdown.extensions.wikilinks import WikiLinkExtension
from markdown.extensions.tables import TableExtension
from xidb.utils import *

class Asset(object):
    def __init__(self):
        self.name = ''
        self.metadata = {}
        self.contentType = ''
        self.title = ''
        self.xlink = ''
        self.vlink = ''
        self.connected = True

    def init(self):
        self.vlink = self.metadata['base']['commit'][:8]

    def initFromMetadata(self, meta):
        base = meta['base']
        cid = base['commit']
        xid = base['xid']

        asset = meta['asset']
        sha = asset['sha']
        name = asset['name']

        self.metadata = meta
        self.configure(cid, sha, xid, name)

    def configure(self, cid, sha, xid, name):
        self.xid = str(xid)
        self.name = name
        self.title = os.path.basename(name)
        self.ext = os.path.splitext(name)[1]
        self.cid = str(cid)
        self.sha = str(sha)
        self.xlink = createLink(self.xid, self.cid)
 
    def save(self, path=None):
        base = self.getBase()

        if path:
            base['path'] = path
        else:
            path = base['path']

        saveMetadata(self.metadata)
        print ">>> saved metadata to ", path

    def addVersion(self, cid, sha):
        sha = str(sha)
        cid = str(cid)
        if (self.sha != sha):
            # print "new version for", self.name, self.sha, sha
            self.sha = sha
            self.cid = cid
            self.xlink = createLink(self.xid, self.cid)

    def generate(self, blob, snapshot):
        """ Generates metadata and returns a kind (subclass instance) of Asset """
        data = {}

        data['base'] = {
            'xid': self.xid,
            'commit': str(snapshot.commit.id),
            'xlink': createLink(self.xid, snapshot.commit.id),
            'branch': snapshot.xlink,
            'timestamp': snapshot.timestamp,
            'ref': '',
            'kind': ''
        }

        data['asset'] = {
            'name': self.name,
            'ext': self.ext,
            'title': '',
            'description': '',
            'sha': str(blob.id),
            'size': blob.size,
            'encoding': 'binary' if blob.is_binary else 'text',
        }

        kind = None

        for factory in allTypes:
            obj = factory()
            obj.configure(self.cid, self.sha, self.xid, self.name)
            obj.blob = blob
            obj.metadata = data
            obj.snapshot = snapshot
            obj.init()
            if obj.isValid():
                obj.addMetadata()
                kind = obj
                data['base']['kind'] = kind.typeName() # TBD should be kind xlink
                break # use only first valid xitype

        if kind:
            kind.metadata = data
            kind.connected = False
            return kind
        else:
            self.metadata = data
            self.connected = False
            return self

    def connect(self, guild):
        # print ">>> connected", self.typeName(), self.connected
        self.connected = True

    def typeName(self):
        return type(self).__name__

    def isValid(self):
        return False

    def checkExtension(self, extensions):
        ext = self.metadata['asset']['ext']
        return ext in extensions

    def getBase(self):
        return self.metadata['base']

    def getTimestamp(self):
        return self.getBase()['timestamp']

    def addMetadata(self):
        self.metadata['asset']['content-type'] = self.contentType
        self.metadata['asset']['title'] = self.title

    def addVote(self, agent, vote):
        xid = agent.getXid()
        xlink = vote.xlink # change to getXlink()?
        base = self.metadata['base']
        votes = base['votes'] if "votes" in base else {}
        votes[xid] = xlink
        base['votes'] = votes
        self.metadata['base'] = base
        self.save()
        print ">>> addVote", xid, xlink, vote.getTimestamp()

    def addComment(self, comment):
        base = self.metadata['base']
        comments = base['comments'] if "comments" in base else []
        comments.append(comment.xlink)
        base['comments'] = comments
        self.metadata['base'] = base
        self.save()
        print ">>> addComment", comment

    def getTitle(self):
        return self.metadata['asset']['title']

    def setTitle(self, title):
        self.metadata['asset']['title'] = title
        self.save()

class Text(Asset):
    def __init__(self):
        super(Text, self).__init__()

    def init(self):
        super(Text, self).init()

        if self.blob.is_binary:
            self.text = None
        else:
            self.text = self.blob.data.decode('utf-8')

    def isValid(self):
        return self.text != None

    def addMetadata(self):
        lines = self.text.count('\n')
        self.metadata['text'] = { 'lines': lines }
        self.contentType = "text/plain"
        super(Text, self).addMetadata()

class Json(Text):
    def __init__(self):
        super(Json, self).__init__()

    def init(self):
        super(Json, self).init()

        try:
            self.data = json.loads(self.blob.data)
        except:
            self.data = None

    def isValid(self):
        return (super(Json, self).isValid() and self.data)

class Agent(Json):
    def __init__(self):
        super(Agent, self).__init__()

    def init(self):
        super(Agent, self).init()

    def isValid(self):
        return (self.checkExtension(['.json']) 
                and self.name.find("agents/data") == 0
                and super(Agent, self).isValid())

    def addMetadata(self):
       super(Agent, self).addMetadata()
       self.metadata['agent'] = self.data

    def getContact(self):
        return self.data['contact']

    def getName(self):
        return self.getContact()['name']

    def getEmail(self):
        return self.getContact()['email']

    def getXid(self): # promote to Asset?
        return self.metadata['base']['xid']

    def getXlink(self): # promote to Asset?
        return self.metadata['base']['xlink']

    def getSignature(self):
        return Signature(self.getName(), self.getEmail())

    def addPub(self, pub, kind):
        print ">>> addPub", pub.xlink, kind
        base = self.metadata['base']
        pubs = base['pubs'] if "pubs" in base else {}
        publist = pubs[kind] if kind in pubs else []
        publist.append(pub.xlink)
        pubs[kind] = publist
        base['pubs'] = pubs
        self.metadata['base'] = base
        saveMetadata(self.metadata)

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
            self.ref = self.xaction['ref']
            # todo: retrieve reference's metadata
            self.author=self.xaction['author']
            # todo: retrieve author's name from metadata
            self.title = "Comment on %s by %s" % (self.ref, self.author)

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
            ref=self.ref,
            author=self.author,
            authorName=self.snapshot.commit.author.name,
            authorEmail=self.snapshot.commit.author.email,
        )

    def connect(self, guild):
        ref = guild.getAsset(self.ref)
        if ref:
            ref.addComment(self)
            print ">>> added comment to ", ref.name
            self.setTitle("re: " + ref.name)

        author = guild.agentFromXlink(self.author)
        if author:
            author.addPub(self, "comment")
            print ">>> added vote from", author.getName(), self.xlink

class Vote(Json):
    def __init__(self):
        super(Vote, self).__init__()

    def init(self):
        super(Vote, self).init()

        try:
            self.xaction = json.loads(self.snapshot.commit.message)
        except:
            self.xaction = None
        
        if self.isValid():
            self.ref = self.xaction['ref']
            # todo: retrieve reference's metadata
            self.author=self.xaction['author']
            # todo: retrieve author's name from metadata
            self.title = "Vote on %s by %s" % (self.ref, self.author)

    def isVote(self):
        return (self.data and
                self.xaction and 
                'type' in self.xaction and 
                self.xaction['type'] == 'vote' and 
                'ref' in self.xaction and 
                'author' in self.xaction)

    def isValid(self):
        return (super(Vote, self).isValid()
                and self.isVote())

    def addMetadata(self):
       super(Vote, self).addMetadata()

       self.metadata['vote'] = self.data

       self.metadata['xaction'] = dict(
           ref=self.ref,
           author=self.author,
           authorName=self.snapshot.commit.author.name,
           authorEmail=self.snapshot.commit.author.email,
       )

       # print ">>> addVote new", self.xlink, self.getTimestamp()

    def connect(self, guild):
        author = guild.agentFromXlink(self.author)
        ref = guild.getAsset(self.ref)

        if author and ref:
            author.addPub(self, "vote")
            print ">>> added vote from", author.getName(), self.xlink

            ref.addVote(author, self)
            print ">>> added vote to", ref.name, self.xlink
            self.setTitle("re: " + ref.getTitle())


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
    lambda : Agent(),
    lambda : Vote(),
    lambda : Comment(),
    lambda : Markdown(),
    lambda : Text(),
    lambda : Png(),
    lambda : Jpeg(),
    lambda : Gif(),
]
