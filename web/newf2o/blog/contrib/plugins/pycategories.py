# vim: tabstop=4 shiftwidth=4
"""
Walks through your blog root figuring out all the categories you have
and how many entries are in each category.  It generates html with
this information and stores it in the $categorylinks variable which
you can use in your head or foot templates.

Additionally, you can specify the flavour for the link by creating an 
entry in the config.py file or the ini file with the name 
"category_flavour" and the value of the flavour you want to use.

config.py example::

   py["category_flavour"] = "index"
"""
__author__ = "Will Guaraldi - willg at bluesock dot org"
__version__ = "$Id: pycategories.py,v 1.20 2004/04/04 15:35:39 willhelm Exp $"

from Pyblosxom import tools
import re, os

def verify_installation(request):
    config = request.getConfiguration()
    if not config.has_key("category_flavour"):
        print "missing optional config property 'category_flavour' which allows "
        print "you to specify the flavour for the category link.  refer to "
        print "pycategory plugin documentation for more details."
    return 1

class PyblCategories:
    def __init__(self, request):
        self._request = request
        self._categories = None
        self.genCategories()

    def __str__(self):
        if self._categories == None:
            self.genCategories()
        return self._categories

    def genitem(self, item):
        itemlist = item.split(os.sep)

        num = 0
        for key in self._elistmap.keys():
            if key.endswith(item) or key.endswith(item + os.sep):
                num = num + self._elistmap[key]
        num = " (%d)" % num

        if not item:
            tab = ""
        else:
            tab = len(itemlist) * "&nbsp;&nbsp;"

        return (tab + "<a href=\"%s/%s%s\">%s</a>%s" % (self._baseurl, item, self._flavour, itemlist[-1] +"/", num))

    def genCategories(self):
        config = self._request.getConfiguration()
        root = config["datadir"]

        data = self._request.getData()

        flav = config.get("category_flavour", "")
        if flav:
            self._flavour = "?flav=" + flav
        else:
            self._flavour = ""

        self._baseurl = config.get("base_url", "")

        # build the list of entries
        elist = tools.Walk(self._request, root)
        elist = [mem[len(root)+1:] for mem in elist]

        total = len(elist)

        elistmap = {}
        for mem in elist:
            mem = os.path.dirname(mem)
            elistmap[mem] = 1 + elistmap.get(mem, 0)
        self._elistmap = elistmap

        clistmap = {}
        for mem in elistmap.keys():
            mem = mem.split(os.sep)
            for i in range(len(mem)+1):
                p = os.sep.join(mem[0:i])
                clistmap[p] = 0

        clist = clistmap.keys()
        clist.sort()

        clist = map(self.genitem, clist)
        self._categories = "<br />".join(clist)


def cb_prepare(args):
    request = args["request"]
    data = request.getData()
    data["categorylinks"] = PyblCategories(request)
