import re
import nltk
import urllib
import textwrap
from BeautifulSoup import BeautifulSoup
import pygraphviz as pgv

class EventTree:
    def __init__(self, nodeval='root', children=[]):
        """
        Tree data structure for representing an event.
        
        args
        ----
        nodeval - a label/data stored for this item

        children - a list of child EventTree nodes to append to the current node.
        """    
        self.parent = None
        self.nodeval = nodeval
        self.children = []
        self.add_list(children)

    def add_list(self, aList):
        for c in aList:
            if isinstance(c, EventTree):
                c.parent = self;
                self.children.append(c)
           

    def add_child(self, child):
        if isinstance(child, EventTree):
            child.parent = self;
            self.children.append(child)

    def to_ipython(self):
        G=pgv.AGraph()
        self._build_graphviz(G)
        G.layout(prog='dot')
        G.draw('file.png')
        from IPython.display import Image
        return Image(filename='file.png')

    def _build_graphviz(self, G):
        for c in self.children:
            G.add_edge(self.nodeval, c.nodeval);
            c._build_graphviz(G)
        

def make_tree_from_wiki(f, prune_wiki=False):

    pagetext = "".join(f.readlines())

    parsed_html = BeautifulSoup(pagetext)
    toctable = parsed_html.find('div', attrs={'id':'toc'}).find('ul')
    first_child, last_child = _recover_section_text(parsed_html)
    _recover_wiki_tree(toctable, parsed_html, last_child, prune_wiki=prune_wiki)
    return first_child

def _recover_wiki_tree(el, soup, root=EventTree(), prune_wiki=False):
    if not el:
        return
      
    for li in el.findAll('li', recursive=False):
        toctext = li.find('span', attrs={'class':'toctext'}).text
        if not prune_wiki or toctext not in ['See also', 'References', 'External links']:

            sublist = li.find('ul')
            node = EventTree(nodeval=toctext) 

            safe_text = toctext.replace(' ', '_') 
            first_child, last_child = _recover_section_text(soup, safe_text)
            if first_child:
                node.add_child(first_child)
                _recover_wiki_tree(sublist, soup, last_child)
            else:
                _recover_wiki_tree(sublist, soup, node)
            
            root.add_child(node)
            
    return root 


def _extract_clean_text(tag):
    [s.extract() for s in tag('sup')]
    clean_text = nltk.clean_html(repr(tag))
    clean_text = textwrap.wrap(clean_text.replace('&#160;',' '), 30)[0]
    return clean_text

def _recover_section_text(soup, section=None):
    head_graf = None
    cur_graf = None
    if section:
        tag = soup.find('span', attrs={'id':section}).parent
    else:
        tag = soup.find('p', recursive=False)
        clean_text = _extract_clean_text(tag)
        head_graf = EventTree(nodeval=clean_text)
        cur_graf = head_graf
    while True:
        tag = tag.nextSibling
        if tag == None:
            break
        if hasattr(tag, 'name'):
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                break
            if tag.name == 'p':
                clean_text = _extract_clean_text(tag)
                if cur_graf:
                    node = EventTree(nodeval=clean_text)
                    cur_graf.add_child(node)
                    cur_graf = node
                else:
                    
                    cur_graf = EventTree(nodeval=clean_text)
                    head_graf = cur_graf

    return (head_graf, cur_graf)        
