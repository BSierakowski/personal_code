"""
This module contains an extension to Blosxom file entries to support
comments.

Contributors:
Ted Leung
Will Guaraldi
Wari Wahab
Robert Wall
Bill Mill
Roberto De Almeida

If you make any changes to this plugin, please a send a patch with your
changes to twl+pyblosxom@sauria.com so that we can incorporate your changes.
Thanks!

This plugin requires the pyXML module.

This module supports the following config parameters (they are not
required):

    comment_dir - the directory we're going to store all our comments in.
                  this defaults to datadir + "comments".
    comment_ext - the file extension used to denote a comment file.
                  this defaults to "cmt".
    comment_draft_ext - the file extension used for new comments that have
                        not been manually approved by you.  this defaults
                        to comment_ext (i.e. there is no draft stage)

    comment_smtp_server - the smtp server to send comments notifications
                          through.
    comment_smtp_from - the person comment notifications will be from.
                        If you omit this, the from address will be the
                        e-mail address as input in the comment form
    comment_smtp_to - the person to send comment notifications to.
    comment_rejected_words - the list of words that will cause automatic
                             rejection of the comment--this is a very
                             poor man's spam reducer.


Comments are stored 1 per file in a parallel hierarchy to the datadir
hierarchy.  The filename of the comment is the filename of the blog
entry, plus the creation time of the comment as a float, plus the 
comment extension.  The contents of the comment file is an RSS 2.0
formatted item.

Each entry has to have the following properties in order to work with
comments:

 1. absolute_path - the category of the entry.  ex. "dev/pyblosxom"
 2. fn - the filename of the entry without the file extension and without
    the directory.  ex. "staticrendering"
 3. file_path - the absolute_path plus the fn.  ex. "dev/pyblosxom/staticrendering"

Also, for any entry that you don't want to have comments, just add
"nocomments" to the properties of the entry.
"""
import cgi, glob, os.path, re, time, cPickle, os
from xml.sax.saxutils import escape
from Pyblosxom import tools
from Pyblosxom.entries.base import EntryBase

def cb_start(args):
    request = args["request"]
    config = request.getConfiguration()
    logdir = config.get("logdir", "/tmp/")

    logfile = os.path.normpath(logdir + os.sep + "comments.log")
    tools.make_logger(logfile)

    if not config.has_key('comment_dir'):
        config['comment_dir'] = os.path.join(config['datadir'],'comments')
    if not config.has_key('comment_ext'):
        config['comment_ext'] = 'cmt'
    if not config.has_key('comment_draft_ext'):
        config['comment_draft_ext'] = config['comment_ext']
    
def verify_installation(request):
    config = request.getConfiguration()

    retval = 1

    if config.has_key('comment_dir') and not os.path.isdir(config['comment_dir']):
        print 'The "comment_dir" property in the config file must refer to a directory'
        retval = 0

    smtp_keys_defined = []
    smtp_keys=['comment_smtp_server', 'comment_smtp_from', 'comment_smtp_to']
    for k in smtp_keys:
        if config.has_key(k):
            smtp_keys_defined.append(k)

    if smtp_keys_defined:
        for i in smtp_keys:
            if i not in smtp_keys_defined:
                print("Missing comment SMTP property: '%s'" % i)
                retval = 0
    
    optional_keys = ['comment_dir', 'comment_ext', 'comment_draft_ext']
    for i in optional_keys:
        if not config.has_key(i):
            print("missing optional property: '%s'" % i)

    return retval

def createhtmlmail (html, headers):
    """Create a mime-message that will render HTML in popular
    MUAs, text in better ones

    Based on: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/67083"""
    import MimeWriter
    import mimetools
    import cStringIO
    
    out = cStringIO.StringIO() # output buffer for our message 
    htmlin = cStringIO.StringIO(html)

    text = re.sub('<.*?>', '', html)
    txtin = cStringIO.StringIO(text)
    
    writer = MimeWriter.MimeWriter(out)
    for header,value in headers:
        writer.addheader(header, value)
    writer.addheader("MIME-Version", "1.0")
    writer.startmultipartbody("alternative")
    writer.flushheaders()

    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
    mimetools.encode(txtin, pout, 'quoted-printable')
    txtin.close()

    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
    mimetools.encode(htmlin, pout, 'quoted-printable')
    htmlin.close()

    writer.lastpart()
    msg = out.getvalue()
    out.close()

    return msg

def readComments(entry, config):
    """
    @param: a file entry
    @type: dict
    
    @returns: a list of comment dicts
    """
    filelist = glob.glob(cmtExpr(entry, config))
    filelist.sort()
    if not entry.has_key('num_comments'):
        entry['num_comments'] = len(filelist)
    try:
        return [ readComment(f) for f in filelist ]
    except:
        tools.log("Couldn't read comments for entry: ",entry)
    return []
    
def getCommentCount(entry, config):
    """
    @param: a file entry
    @type: dict
    
    @returns: the number of comments for the entry
    """
    if entry['absolute_path'] == None: return 0
    filelist = glob.glob(cmtExpr(entry,config))
    if filelist is not None:
        return len(filelist)
    return 0

def cmtExpr(entry, config):
    """
    Return a string containing the regular expression for comment entries
    
    @param: a file entry
    @type: dict
    @returns: a string with the directory path for the comment
    
    @param: configuratioin dictionary
    @type: dict
    
    @returns: a string containing the regular expression for comment entries
    """
    cmtDir = os.path.join(config['comment_dir'], entry['absolute_path'])
    cmtExpr = os.path.join(cmtDir,entry['fn']+'-*.'+config['comment_ext'])
    return cmtExpr

def readComment(filename):
    """
    Read a comment from filename
    
    @param: filename containing a comment
    @type: string
    
    @returns: a comment dict
    """
    from xml.sax import make_parser, SAXException
    from xml.sax.handler import feature_namespaces, ContentHandler
    class cmtHandler(ContentHandler):
        def __init__(self, cmt):
            self._data = ""
            self.cmt = cmt
        def startElement(self, name, atts):
            self._data = ""
        def endElement(self, name):
            self.cmt['cmt_'+name] = self._data
        def characters(self, content):
            self._data += content

    cmt = {}
    
    try:
        story = open(filename)
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        handler = cmtHandler(cmt)
        parser.setContentHandler(handler)
        parser.parse(story)
        #story.close()
        cmt['cmt_time'] = cmt['cmt_pubDate']
        # timestamp as float for comment anchor
        cmt['cmt_pubDate'] = time.ctime(float(cmt['cmt_pubDate']))
        story.close()
    except:
        tools.log("Couldn't read: ", filename)
        story.close()
    return cmt

def writeComment(request, config, data, comment):
    """
    Write a comment
    
    @param config: dict containing pyblosxom config info
    @type  config: dict
    
    @param data: dict containing entry info
    @type  data: dict
    
    @param comment: dict containing comment info
    @type  comment: dict

    @return: The success or failure of creating the comment.
    @rtype: string
    """
    entry = data['entry_list'][0]
    cdir = os.path.join(config['comment_dir'], entry['absolute_path'])
    cdir = os.path.normpath(cdir)
    if not os.path.isdir(cdir):
        os.makedirs(cdir)
    cfn = os.path.join(cdir,entry['fn']+"-"+comment['pubDate']+"."+config['comment_draft_ext'])

    argdict = { "request": request, "comment": comment }
    reject = tools.run_callback("comment_reject",
                                argdict,
                                donefunc=lambda x:x)
    if reject == 1:
        return "Comment rejected."
      
    # write comment
    cfile = None
    try :
        cfile = open(cfn, "w")
    except:
        tools.log("Couldn't open comment file %s for writing" % cfn)
        return "Error: Couldn't open comment file for writing."
    else:
        pass
    
    def makeXMLField(name, field):
        return "<"+name+">"+cgi.escape(field[name])+"</"+name+">\n";
    try:
        try:
            #TODO: fix this to 'utf-8' and commit to sf
            comment[description].decode('utf-8')
            cfile.write('<?xml version=1.0 encoding=utf-8?>\n')
        except:
            encoding = config.get('blog_encoding', 'iso-8859-1')
            cfile.write('<?xml version="1.0" encoding="%s"?>\n' % encoding)
        cfile.write("<item>\n")
        cfile.write(makeXMLField('title',comment))
        cfile.write(makeXMLField('author',comment))
        cfile.write(makeXMLField('link',comment))
        cfile.write(makeXMLField('source',comment))
        cfile.write(makeXMLField('pubDate',comment))
        cfile.write(makeXMLField('description',comment))
        cfile.write("</item>\n")
        cfile.close()
    except:
        tools.log("Error writing comment data for ", cfn)
        cfile.close()
        
    # write latest pickle
    latest = None
    latestFilename = os.path.join(config['comment_dir'],'LATEST.cmt')
    try:
        latest = open(latestFilename,"w")
    except:
        tools.log("Couldn't open latest comment pickle for writing")
        return "Error: Couldn't open latest comment pickle for writing."
    else:
        modTime = float(comment['pubDate'])

    try:
        cPickle.dump(modTime,latest)
        latest.close()
    except (IOError):
        # should log or e-mail
        if latest:
            latest.close()
        return "Error: Problem dumping the pickle."
    
    # if the right config keys are set, notify by e-mail
    if config.has_key('comment_smtp_server') and config.has_key('comment_smtp_to'):

        # import the formatdate function which is in a different
        # place in Python 2.3 and up.
        try:
            from email.Utils import formatdate
        except ImportError:
            from rfc822 import formatdate

        import smtplib
        author = escape_SMTP_commands(clean_author(comment['author']))
        description = escape_SMTP_commands(comment['description'])
        if comment.has_key('email'):
            email = comment['email']
        else:
            email = config.get('comment_smtp_from', "blah@blah.org")
        try:
            server = smtplib.SMTP(config['comment_smtp_server'])
            curl = config['base_url']+'/'+entry['file_path']

            headers = []
            headers.append(("From", email))
            headers.append(("To", config["comment_smtp_to"]))
            headers.append(("Date", formatdate(modTime)))
            headers.append(("Subject", "write back by %s" % author))

            html = """%s<br />\n%s<br />\n<a href="%s">%s</a>\n""" % (description, cfn, curl, curl)
            message = createhtmlmail(html, headers)
            server.sendmail(from_addr=email,
                            to_addrs=config['comment_smtp_to'],
                            msg=message)
            server.quit()
        except:
            tools.log("Error sending mail: %s" % message)
            return "Error: Problem sending notification email."

    msg = "Success: Comment has been registered."
    if config["comment_draft_ext"] != config["comment_ext"]:
        msg = msg + "  Comment will not appear until it has been manually approved by the owner of this web-site."
    return msg

def clean_author(s):
    """
    Guard against blasterattacko style attacks that embedd SMTP commands in
    author field.

    If author field is more than one line, reduce to one line

    @param the string to be checked
    @type string

    @returns the sanitized string
    """
    return s.splitlines()[0]

def escape_SMTP_commands(s):
    """
    Guard against blasterattacko style attacks that embed SMTP commands by
    using an HTML span to make the command syntactically invalid to SMTP but
    renderable by HTML

    @param the string to be checked
    @type string

    @returns the sanitized string
    """
    def repl_fn(mo):
        return '<span>'+mo.group(0)+'</span>'
    s = re.sub('([Tt]o:.*)',repl_fn,s)
    s = re.sub('([Ff]rom:.*)',repl_fn,s)
    s = re.sub('([Ss]ubject:.*)',repl_fn,s)
    return s

def sanitize(body):
    """
    This code shamelessly lifted from Sam Ruby's mombo/post.py
    """
    body=re.sub(r'\s+$','',body)
    body=re.sub('\r\n?','\n', body)

    # naked urls become hypertext links
    body=re.sub('(^|[\\s.:;?\\-\\]<])' + 
                '(http://[-\\w;/?:@&=+$.!~*\'()%,#]+[\\w/])' +
                '(?=$|[\\s.:;?\\-\\[\\]>])',
                '\\1<a href="\\2">\\2</a>',body)

    # html characters used in text become escaped
    body=escape(body)

    # passthru <a href>, <em>, <i>, <b>, <blockquote>, <br/>, <p>, 
    # <abbr>, <acronym>, <big>, <cite>, <code>, <dfn>, <kbd>, <pre>, <small>
    # <strong>, <sub>, <sup>, <tt>, <var>
    body=re.sub('&lt;a href="([^"]*)"&gt;([^&]*)&lt;/a&gt;',
                '<a href="\\1">\\2</a>', body)
    body=re.sub('&lt;a href=\'([^\']*)\'&gt;([^&]*)&lt;/a&gt;',
                '<a href="\\1">\\2</a>', body)
    body=re.sub('&lt;em&gt;([^&]*)&lt;/em&gt;', '<em>\\1</em>', body)
    body=re.sub('&lt;i&gt;([^&]*)&lt;/i&gt;', '<i>\\1</i>', body)
    body=re.sub('&lt;b&gt;([^&]*)&lt;/b&gt;', '<b>\\1</b>', body)
    body=re.sub('&lt;blockquote&gt;([^&]*)&lt;/blockquote&gt;', 
                '<blockquote>\\1</blockquote>', body)
    body=re.sub('&lt;br\s*/?&gt;\n?','\n',body)

    body=re.sub('&lt;abbr&gt;([^&]*)&lt;/abbr&gt;', '<abbr>\\1</abbr>', body)
    body=re.sub('&lt;acronym&gt;([^&]*)&lt;/acronym&gt;', '<acronym>\\1</acronym>', body)
    body=re.sub('&lt;big&gt;([^&]*)&lt;/big&gt;', '<big>\\1</big>', body)
    body=re.sub('&lt;cite&gt;([^&]*)&lt;/cite&gt;', '<cite>\\1</cite>', body)
    body=re.sub('&lt;code&gt;([^&]*)&lt;/code&gt;', '<code>\\1</code>', body)
    body=re.sub('&lt;dfn&gt;([^&]*)&lt;/dfn&gt;', '<dfn>\\1</dfn>', body)
    body=re.sub('&lt;kbd&gt;([^&]*)&lt;/kbd&gt;', '<kbd>\\1</kbd>', body)
    body=re.sub('&lt;pre&gt;([^&]*)&lt;/pre&gt;', '<pre>\\1</pre>', body)
    body=re.sub('&lt;small&gt;([^&]*)&lt;/small&gt;', '<small>\\1</small>', body)
    body=re.sub('&lt;strong&gt;([^&]*)&lt;/strong&gt;', '<strong>\\1</strong>', body)
    body=re.sub('&lt;sub&gt;([^&]*)&lt;/sub&gt;', '<sub>\\1</sub>', body)
    body=re.sub('&lt;sup&gt;([^&]*)&lt;/sup&gt;', '<sup>\\1</sup>', body)
    body=re.sub('&lt;tt&gt;([^&]*)&lt;/tt&gt;', '<tt>\\1</tt>', body)
    body=re.sub('&lt;var&gt;([^&]*)&lt;/var&gt;', '<var>\\1</var>', body)

    body=re.sub('&lt;/?p&gt;','\n\n',body).strip()

    # wiki like support: _em_, *b*, [url title]
    body=re.sub(r'\b_(\w.*?)_\b', r'<em>\1</em>', body)
    body=re.sub(r'\*(\w.*?)\*', r'<b>\1</b>', body)
    body=re.sub(r'\[(\w+:\S+\.gif) (.*?)\]', r'<img src="\1" alt="\2" />', body)
    body=re.sub(r'\[(\w+:\S+\.jpg) (.*?)\]', r'<img src="\1" alt="\2" />', body)
    body=re.sub(r'\[(\w+:\S+\.png) (.*?)\]', r'<img src="\1" alt="\2" />', body)
    body=re.sub(r'\[(\w+:\S+) (.*?)\]', r'<a href="\1">\2</a>', body).strip()

    # unordered lists: consecutive lines starting with spaces and an asterisk
    chunk=re.compile(r'^( *\*.*(?:\n *\*.*)+)',re.M).split(body)
    for i in range(1, len(chunk), 2):
        (html,stack)=('', [''])
        for indent,line in re.findall(r'( +)\* +(.*)', chunk[i]) + [('','')]:
            if indent>stack[-1]: (stack,html)=(stack+[indent],html+'<ul>\r')
            while indent<stack[-1]: (stack,html)=(stack[:-1],html+'</ul>\r')
            if line: html += '<li>'+line+'</li>\r'
            chunk[i]=html

    # white space
    chunk=re.split('\n\n+', ''.join(chunk))
#    if len(chunk)>1: body='<p>' + '</p>\r<p>'.join(chunk) + '</p>\r'
    body=re.sub('\n','<br />\n', body)
    body=re.compile('<p>(<ul>.*?</ul>)\r</p>?',re.M).sub(r'\1',body)
    body=re.compile('<p>(<blockquote>.*?</blockquote>)</p>?',re.M).sub(r'\1',body)
    body=re.sub('\r', '\n', body)
    body=re.sub('  +', '&nbsp; ', body)

    return body        
        
        
def cb_prepare(args):
    """
    Handle comment related HTTP POST's.
    
    @param request: pyblosxom request object
    @type request: a Pyblosxom request object
    """
    request = args["request"]
    form = request.getHttp()['form']
    config = request.getConfiguration()
    data = request.getData()
    
    if form.has_key("title") and form.has_key("author") and \
        form.has_key("body") and not form.has_key("preview"):

        body = form['body'].value
        
        body = sanitize(body)

        # Check if the form has a URL
        url = (form.has_key('url') and [form['url'].value] or [''])[0]
        
        cdict = {'title': form['title'].value, \
                 'author' : form['author'].value, \
                 'pubDate' : str(time.time()), \
                 'link' : url, \
                 'source' : '', \
                 'description' : body }
        if form.has_key('email'):
            cdict['email'] = form['email'].value

        data["comment_message"] = writeComment(request, config, data, cdict)


def cb_head(args):
    renderer = args['renderer']
    template = args['template']

    newtemplate = renderer.flavour.get('comment-head','')
    if not newtemplate == '' and len(renderer.getContent()) == 1:
        args['template'] = newtemplate

        # expand all of entry vars for expansion
        entry = args['entry']
        single_entry = entry['entry_list'][0]
        single_entry['title'] # force lazy evaluation
        entry.update(single_entry)
        args['entry'] = entry
    return template
        

def cb_story(args):
    renderer = args['renderer']
    entry = args['entry']
    template = args['template']
    request = args["request"]
    config = request.getConfiguration()
    if len(renderer.getContent()) == 1 \
            and renderer.flavour.has_key('comment-story') \
            and not entry.has_key("nocomments"):
        template = renderer.flavour.get('comment-story','')
        args['template'] = args['template'] + template

    entry['num_comments'] = getCommentCount(entry, config)
    return template


def build_preview_comment(form, entry):
    #generates a preview comment by brute force and adds it to the entry
    #so it can be used to refill the form
    c = {}
    try:
        c['cmt_time'] = str(time.time())
        c['cmt_author'] = form['author'].value
        c['cmt_title'] = form['title'].value
        c['cmt_item'] = sanitize(form['body'].value)
        c['cmt_pubDate'] = time.ctime(time.time())
        c['cmt_description'] = sanitize(form['body'].value)
    except KeyError, e:
        c['cmt_description'] = 'Missing value: %s' % e
    if form.has_key('url'):
        c['cmt_link'] = form['url'].value
    if form.has_key('email'):
        c['cmt_email'] = form['email'].value
    for key in c: entry[key] = c[key]
    return c

def cb_story_end(args):
    renderer = args['renderer']
    entry = args['entry']
    template = args['template']
    request = args["request"]
    form = request.getHttp()['form']
    config = request.getConfiguration()
    if len(renderer.getContent()) == 1 \
            and renderer.flavour.has_key('comment-story') \
            and not entry.has_key("nocomments"):
        output = []
        entry['comments'] = readComments(entry, config)
        if entry.has_key('comments'):        
            for comment in entry['comments']:
                renderer.outputTemplate(output, comment, 'comment')
            if form.has_key('preview')\
                and renderer.flavour.has_key('comment-preview'):
                com = build_preview_comment(form, entry)
                renderer.outputTemplate(output, com, 'comment-preview')
            renderer.outputTemplate(output, entry, 'comment-form')
        args['template'] = template +u"".join(output)

    entry['num_comments'] = getCommentCount(entry, config)
    return template
