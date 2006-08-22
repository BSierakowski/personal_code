# vim: tabstop=4 shiftwidth=4 expandtab
# This document uses epydoc syntax, see http://epydoc.sf.net
"""
C{README} for Plugins and Plugin writing

Inside the C{contrib/} directory, you'll see the C{plugins/} directory. To
install a given plugin, move the plugin file you want from the C{contrib/}
directory to the C{Pyblosxom/plugins/} directory of your installation.

Some plugins take effect immediately, like the C{conditionalhttp.py} and the
C{statusnotfound.py}.  Some plugins require some setup before they work.
Read the plugin file in a text editor to see what installation steps are
required.

Below is documentation for plugin developers detailing the standard
callbacks that they can use to implement plugins.


B{Implementing a callback in a plugin}

If you want to implement a callback, you add a function corresponding
to the callback name to your plugin module.  For example, if you wanted
to modify the L{Request} object just before rendering, you'd implement
cb_prepare something like this::

    def cb_prepare(args):
        pass

Each callback passes in arguments through a single dictionary.  Each
callback passes in different arguments and expects different return
values.  Consult the documentation for the callback you're seeking
before implementing it in your code to understand what it does and
how to use it.


B{The BlosxomRenderer plugin callbacks}

The L{BlosxomRenderer} plugins are based on the blosxom 2.0 callbacks.
The names of the arguments are different, but the callbacks are called
at the same points that the blosxom 2.0 callbacks are called and serve
the same function.

The available blosxom renderer callbacks are:
 
    - L{cb_head} (corresponds to blosxom 2.0 head)
    - L{cb_date_head} (corresponds to blosxom 2.0 date)
    - L{cb_story} (corresponds to blosxom 2.0 story)
    - L{cb_foot} (corresponds to blosoxm 2.0 foot)

Some of the other blosxom 2.0 callbacks are handled slightly differently
in PyBlosxom.

     - The blosxom 2.0 entries callback is handled by L{cb_filelist}
     - The blosxom 2.0 filter callback is handled by L{cb_prepare}
     - The blosxom 2.0 sort callback is handled by L{cb_prepare}

See the callback documentation below for more details.


B{verify_installation}

As of PyBlosxom 0.9, the pyblosxom.cgi is able to test your PyBlosxom
installation.  It verifies certain items in your config file and also
loads all the plugins and lets them verify their configuration as well.

At the prompt, you would run::

   ./pyblosxom.cgi

It tells you your Python version, OS name, and then proceeds to verify
your config properties (did you specify a valid datadir?  does it
exist?...) and then initializes all your plugins and executes
verify_installation(request) on every plugin you have
installed that has the function.

As a plugin developer, you should add a verify_installation function
to your plugin module.  Something like this (taken from pycategories)::

   def verify_installation(request):
       config = request.getConfiguration()

       if not config.has_key("category_flavour"):
           print "missing optional config property 'category_flavour' which allows "
           print "you to specify the flavour for the category link.  refer to "
           print "pycategory plugin documentation for more details."
       return 1

Basically this gives you (the plugin developer) the opportunity to
walk the user through configuring your highly complex, quantum-charged,
turbo plugin in small baby steps without having to hunt for where
their logs might be.

So check the things you need to check, print out error messages
(informative ones), and then return a 1 if the plugin is configured 
correctly or a 0 if it's not configured correctly.

This is not a substitute for reading the installation instructions.  But
it should be a really easy way to catch a lot of potential problems
without involving the web server's error logs and debugging information
being sent to a web-browser and things of that nature.
"""
import Pyblosxom, os
from Pyblosxom.pyblosxom import Request
from Pyblosxom.renderers.blosxom import BlosxomRenderer
from Pyblosxom.entries.base import EntryBase
from Pyblosxom.entries.fileentry import FileEntry
from Pyblosxom.pyblosxom import PyBlosxom

def cb_prepare(args):
    """
    The prepare callback is called in the default blosxom handler after 
    we've figured out what we're rendering and before we actually go to the
    renderer.

    Plugins should implement cb_prepare to modify the data dict which 
    is in the L{Request}.  Inside the data dict is C{'entry_list'} 
    (amongst other things) which holds the list of entries to be renderered 
    (in the order they will be rendered).

    Functions that implement this callback will get an args dict
    containing:

     - C{'request'} - The L{Request} object at the particular moment

    Functions that implement this callback can return whatever they want--it
    doesn't affect the callback chain.

    Example of a C{cb_prepare} function in a plugin::

        def cb_prepare(args):
            \"""
            This plugin shows the number of entries we are going to render and
            place the result in $countNoOfEntries.
            \"""
            request = args['request']
            data = request.getData()
            config = request.getConfiguration()

            # Can anyone say Ternary? :)
            IF = lambda a,b,c:(a() and [b()] or [c()])[0]

            num_entry = config['num_entries']
            entries = len(data['entry_list'])

            data['countNoOfEntries'] = IF(num_entry > entries, num_entry, entries)
    @param args: dict containing C{'request'}
    @type  args: dict

    @return: None
    @rtype:  None
    """
    pass


def cb_logrequest(args):
    """
    The logrequest callback is used to notify plugins of the current 
    PyBlosxom request for the purposes of logging.

    Functions that implement this callback will get an args dict
    containing:

     - C{'filename'} - a filename (typically a base filename)
     - C{'return_code'} - A HTTP error code (e.g 200, 404, 304)
     - C{'request'} - a L{Request} object

    Functions that implement this callback can return whatever they want--it
    doesn't affect the callback chain.

    cb_logrequest is called after rendering and will contain all the
    modifications to the L{Request} object made by the plugins.

    An example input args dict is like this::

        {'filename': filename, 'return_code': '200', 'request': Request()}

    @param args: a dict containing C{'filename'}, C{'return_code'}, and
        C{'request'}
    @type  args: dict

    @return: None
    @rtype:  None
    """
    pass


def cb_filelist(args):
    """
    The filelist callback allows plugins to generate the list of entries
    to be rendered.  Entries should be L{EntryBase} derivatives--either
    by instantiating L{EntryBase}, L{FileEntry}, or creating your own
    L{EntryBase} subclass.
    
    Functions that implement this callback will get an args dict
    containing:

     - C{'request'} - the PyBlosxom Request

    Functions that implement this callback should return None if they
    don't plan on generating the entry list or a list of entries.
    if they do.  When a function returns None, the callback will continue
    to the next function to see if it will return a list of entries.
    When a function returns a list of entries, the callback will stop.

    @param args: a dict containing C{'request'}
    @type  args: dict

    @returns: None or list of L{EntryBase} objects
    @rtype:   list
    """
    pass


def cb_filestat(args):
    """
    The filestat callback allows plugins to override the mtime of
    the entry.  One of the contributed plugins uses this to set the
    mtime to the time specified in the entry's filename.

    Functions that implement this callback will get an args dict containing:
    
     - C{'filename'} - the filename of the entry
     - C{'mtime'} - the result of an os.stat on the filename of the entry

    Functions that implement this callback must return the input args
    dict whether or not they adjust anything in it.

    @param args: a dict containing C{'filename'} and C{'mtime'}
    @type args: dict

    @returns: the args dict
    @rtype: dict
    """
    pass

def cb_pathinfo(args):
    """
    The pathinfo callback allows plugins to parse the HTTP PATH_INFO
    item.  This item is stored in the http dict of the L{Request} object.
    Functions would parse this as they desire, then set the following
    variables in the data dict of the L{Request} object::

      'bl_type'       (dir|file)
      'pi_bl'         typically the same as PATH_INFO
      'pi_yr'         yyyy
      'pi_mo'         (mm|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)
      'pi_da'         dd
      'root_datadir'  full path to the entry folder or entry file on filesystem
      'flavour'       The flavour gathered from the URL

    Functions that implement this callback will get an args dict containing:

     - C{'request'} - a L{Request} object

    Functions that implement this callback should make the modifications
    to the data dict in place--no need to return anything.

    @param args: a dict containing C{'request'}
    @type  args: dict

    @return: None
    @rtype:  None
    """
    pass


def cb_renderer(args):
    """
    The renderer callback allows plugins to specify a renderer to use by
    returning a renderer instance to use.  If no renderer is specified,
    we use the default blosxom renderer.

    Functions that implement this callback will get an args dict
    containing:

     - C{'request'} - the PyBlosxom Request

    Functions that implement this callback should return None if they
    don't want to specify a renderer or the renderer object instanct
    if they do.  When a function returns a renderer instance, processing
    stops.

    @param args: a dict containing C{'request'}
    @type args: dict

    @returns: None or a L{Pyblosxom.renderers.base.RendererBase} instance
    @rtype: object instace
    """
    pass


def cb_entryparser(entryparsingdict):
    """
    The entryparser callback allows plugins to register the entryparsers
    they have.  Entry parsers are linked with a filename extension.  For
    example, the default blosxom text entry parser will be used for
    any file ending in ".txt".

    Functions that implement this callback will get the entryparser
    dict consisting of file extension -> entry parsing function pairs.

    Functions that implement this callback should return the entryparser
    dict after modifying it.


    B{A bit about entry parsing functions}

    Entry parsing functions take in a filename and the L{Request} object.
    They then open the file and parse it out.  The can call L{cb_preformat}
    and L{cb_postformat} as they see fit.  They should return a dict
    containing at least C{'title'} and C{'story'} keys.  The C{'title'}
    should be a single string.  The C{'story'} should be a list of 
    strings (with \\n at the end).

    Here's an example code that reads *.plain files::

        import os
        def cb_entryparser(entryparsingdict):
            \"""
            Register self as plain file handler
            \"""
            entryparsingdict['plain'] = parse
            return entryparsingdict

        def parse(filename, request):
            \"""
            We just read everything off the file here, using the filename as
            title
            \"""
            entryData = {}
            entryData['title'] = os.path.basename(filename)
            entryData['story'] = open(filename).read()
            return entryData

    @param entryparsingdict: a dict that comtains file extension -> entry 
        parsing function pairs
    @type  entryparsingdict: dict

    @returns: the entry parsing dict
    @rtype: dict
    """
    pass


def cb_preformat(args):
    """
    The preformat callback acts in conjunction with the entryparser
    that handled the entry to do a two-pass formatting of the entry.

    Functions that implement cb_preformat are text transformation tools.
    Once one of them returns a transformed entry, then we stop processing.

    Functions that implement this callback will get an args dict
    containing:

     - C{'parser'} - a string that indicates whether a preformatter should run
     - C{'story'} - a list containing lines of text (with '\\n' included)
     - C{'request'} - a L{Request} object

    Functions that implement this callback should return None if they
    didn't modify the story or a single story string.

    A typical preformat plugin look like::

        def cb_preformat(args):
            if args['parser'] == 'linebreaks':
                return parse(''.join(args['story']))

        def parse(text):
            # A preformatter to convert linebreak to its HTML counterpart
            text = re.sub('\\n\\n+','</p><p>',text)
            text = re.sub('\\n','<br />',text)
            return '<p>%s</p>' % text

    @param args: a dict containing C{'request'} (L{Request} object), 
        C{'story'} (list of strings), and C{'parser'} (single string)
    @type args: dict

    @returns: string containing the formatted text
    @rtype: string
    """
    pass

def cb_postformat(args):
    """
    The postformat callback allows plugins to make further modifications
    to entry text.  It typically gets called after a preformatter by
    the entryparser.  It can also be used to add additional properties
    to entries.  The changes from postformat functions are saved in the
    cache (if the user has caching enabled).  As such, this shouldn't
    be used for dynamic data like comment counts.

    Examples of usage:

     - Adding a word count property to the entry
     - Using a macro replacement plugin (Radio Userland glossary)
     - Acronym expansion
     - A 'more' text processor

    Functions that implement this callback will get an args dict containing:

     - C{'entry_data'} - a dict that minimally contains a C{'title'} and
                         a C{'story'}
     - C{'request'} - a L{Request} object

    Functions that implement this callback don't need to return 
    anything--modifications to the C{'entry_data'} dict are done in place.

    @param args: a dict containing C{'request'} and C{'entry_data'}
    @type  args: dict
    """
    pass

def cb_start(args):
    """
    The start callback allows plugins to execute startup/initialization code.
    Use this callback for any setup code that your plugin needs, like:
    
     - reading saved data from a file
     - checking to make sure configuration variables are set
     - allocating resources

    Note: The cb_start callback is slightly different than in blosxom in 
    that cb_start is called for every PyBlosxom request regardless of 
    whether it's handled by the default blosxom handler.  In general,
    it's better to delay allocating resources until you absolutely know 
    you are going to use them.

    Functions that implement this callback will get an args dict containing:

     - C{'request'} - a L{Request} object

    Functions that implement this callback don't need to return 
    anything.

    @param args: a dict containing C{'request'}
    @type  args: dict

    @return: None
    @rtype:  None
    """
    pass

def cb_end(args):
    """
    The start callback allows plugins to execute teardown/cleanup code,
    save any data that hasn't been saved, clean up temporary files,
    and otherwise return the system to a normal state.

    Examples of usage:
    
     - save data to a file
     - clean up any temporary files
    
    Functions that implement this callback will get an args dict containing:

     - C{'request'} - a L{Request} object

    Functions that implement this callback don't need to return 
    anything.

    Note: The cb_end callback is called for every PyBlosxom request regardless
    of whether it's handled by the default blosxom handler.  This is slightly
    different than blosxom.

    @param args: a dict containing C{'request'}
    @type  args: dict

    @return: None
    @rtype:  None
    """
    pass

def cb_head(args):
    """
    The head callback is called before a head flavour template is rendered.
    
    C{cb_head} is called before the variables in the entry are substituted
    into the template.  This is the place to modify the head template based
    on the entry content.  You can also set variables on the entry that will
    be used by the C{cb_story} or C{cb_foot} templates.  You have access to 
    all the content variables via entry.
    
    Blosxom 2.0 calls this callback 'head'.

    Functions that implement this callback will get an args dict containing:
    
      - C{'request'} - the L{Request} object
      - C{'renderer'} - the L{BlosxomRenderer} that called the callback
      - C{'entry'} - a L{EntryBase} to be rendered
      - C{'template'} - a string containing the flavour template to be processed

    Functions that implement this callback must return the input args
    dict whether or not they adjust anything in it.

    Example in which we add the number of entries being rendered
    to the $blog_title variable::

       def cb_head(args):
           request = args["request"]
           config = request.getConfiguration()
           data = request.getData()

           num_entries = len(data.get("entry_list", []))
           config["blog_title"] = config.get("blog_title", "") + ": %d entries" % num_entries

           return args

    @param args: a dict containing C{'request'}, C{'renderer'}, C{'entry'} 
        and C{'template'}
    @type  args: dict

    @returns: the args dict
    @rtype: dict
    """
    pass

def cb_date_head(args):
    """
    The date_head callback is called before a date_head flavour template
    is rendered.
    
    C{cb_date_head} is called before the variables in the entry are substituted
    into the template.  This is the place to modify the date_head template 
    based on the entry content.  You have access to all the content variables 
    via entry.
    
    Blosxom 2.0 calls this callback 'date'.

    Functions that implement this callback will get an args dict containing:
    
      - C{'request'} - the L{Request} object
      - C{'renderer'} - the L{BlosxomRenderer} that called the callback
      - C{'entry'} - a L{EntryBase} to be rendered
      - C{'template'} - a string containing the flavour template to be processed

    Functions that implement this callback must return the input args
    dict whether or not they adjust anything in it.

    @param args: a dict containing C{'request'}, C{'renderer'}, C{'entry'} and
        C{'template'}
    @type args: dict

    @returns: the args dict
    @rtype: dict
    """
    pass


def cb_story(args):
    """
    The story callback gets called before the entry is rendered.

    The template used is typically the story template, but we allow 
    entries to override this if they have a "template" property.  If they 
    have the "template" property, then we'll use that template instead.

    C{cb_story} is called before the variables in the entry are substituted
    into the template.  This is the place to modify the story template based
    on the entry content.  You have access to all the content variables via 
    entry.
    
    Blosxom 2.0 calls this callback 'story'.

    Functions that implement this callback will get an args dict containing:
    
      - C{'renderer'} - the L{BlosxomRenderer} that called the callback
      - C{'request'} - the PyBlosxom a L{Request} being handled
      - C{'template'} - a string containing the flavour template to be processed
      - C{'entry'} - a L{EntryBase} object to be rendered

    Functions that implement this callback must return the input args
    dict whether or not they adjust anything in it.

    @param args: a dict containing C{'request'}, C{'renderer'}, C{'entry'} and
        C{'template'}
    @type args: dict

    @returns: the args dict
    @rtype: dict
    """
    pass

def cb_story_end(args):
    """
    The story_end callback is is called after the variables in the entry 
    are substituted into the template.  You have access to all the 
    content variables via entry.
    
    Functions that implement this callback will get an args dict containing:
    
     - C{'request'} - the L{Request} object
     - C{'renderer'} - the L{BlosxomRenderer} that called the callback
     - C{'entry'} - a L{EntryBase} to be rendered
     - C{'template'} - a string containing the flavour template to be processed

    Functions that implement this callback must return the input args
    dict whether or not they adjust anything in it.

    @param args: a dict containing C{'request'}, C{'renderer'}, C{'entry'} and
        C{'template'}
    @type args: dict

    @returns: the args dict
    @rtype: dict
    """
    pass

def cb_foot(args):
    """
    The foot callback is called before the variables in the entry are 
    substituted into the foot template.  This is the place to modify the 
    foot template based on the entry content.  You have access to all the 
    content variables via entry.
    
    Blosxom 2.0 calls this callback 'foot'.

    Functions that implement this callback will get an args dict containing:
    
     - C{'request'} - the L{Request} object
     - C{'renderer'} - the L{BlosxomRenderer} that called the callback
     - C{'entry'} - a L{EntryBase} to be rendered
     - C{'template'} - a string containing the flavour template to be processed

    Functions that implement this callback must return the input args
    dict whether or not they adjust anything in it.

    @param args: a dict containing C{'request'}, C{'renderer'}, C{'entry'} and
        C{'template'}
    @type args: dict

    @returns: the args dict
    @rtype: dict
    """
    pass
