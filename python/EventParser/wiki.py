from wikitools import wiki
from wikitools import api
from wikitools import page
import datetime
import urllib2
import json
from StringIO import StringIO
import dateutil.parser
from collections import namedtuple

class DateRevPair(namedtuple("DateRevPair", ['date','id','pagetext'])):
    def __str__(self): return "{}  {}".format(self.date, self.id)


def get_revisions(title, date, period=14, verbose=False):
  
    #find_starting_timestamp(title, date)
    revs = []
    used_revs = set();

    next_date = date
    while len(revs) < period:
        next_date = find_starting_timestamp(title, next_date)
        if not next_date:
            break

        next_date = next_date.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        revision = query_rev_from_timestamp(title, next_date)
        if revision and revision.id not in used_revs:
            revs.append(revision)
            used_revs.add(revision.id)
            if verbose:
                print "Adding revision: "+str(revision)
        next_date = next_date +datetime.timedelta(hours=12)    
    return revs
        
def query_rev_from_timestamp(title, ts):

    site = wiki.Wiki("http://en.wikipedia.org/w/api.php")
    site.useragent = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36'
    site.limit=5
    params = {'action':'query',
              'prop':'revisions',
              'titles':title,
              'rvprop':'timestamp|ids|content',
              'rvlimit':1,
              'rvstart':ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
              'rvparse':'',
              'rvdir':'older'
              }
    request = api.APIRequest(site, params)

    querystring = request.encodeddata
    #print "QUERT "+querystring
    #print ts
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')]
    infile = opener.open('http://en.wikipedia.org/w/api.php?'+querystring)
    page = infile.read()
    io = StringIO(page)
    wjson = json.load(io)['query']['pages']
    for key in wjson:
        if 'revisions' in wjson[key]:
            rev_id = wjson[key]['revisions'][0]['parentid']
            date = dateutil.parser.parse(wjson[key]['revisions'][0]['timestamp'])
            s = wjson[key]['revisions'][0]['*']
            return DateRevPair(date, rev_id, s.encode('utf-8'))                
    return None





#print pair
#get_revision(title, pair.rev)

def find_starting_timestamp(title, ts):

    site = wiki.Wiki("http://en.wikipedia.org/w/api.php")
    site.useragent = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36'
    site.limit=5
    params = {'action':'query',
              'prop':'revisions',
              'titles':title,
              'rvprop':'timestamp|ids',
              'rvlimit':1,
              'rvstart':ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
              'rvparse':'',
              'rvdir':'newer'
              }
    request = api.APIRequest(site, params)

    querystring = request.encodeddata
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')]
    infile = opener.open('http://en.wikipedia.org/w/api.php?'+querystring)
    page = infile.read()
    io = StringIO(page)
    wjson = json.load(io)['query']['pages']
    for key in wjson:
        if 'revisions' in wjson[key]:
            #rev_id = wjson[key]['revisions'][0]['parentid']
            date = dateutil.parser.parse(wjson[key]['revisions'][0]['timestamp'])
            return date
            #s = wjson[key]['revisions'][0]['*']
            #return DateRevPair(date, rev_id, s.encode('utf-8'))                
    return None





#print pair
#get_revision(title, pair.rev)













