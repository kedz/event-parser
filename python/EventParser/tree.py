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
        self.parents = []
        self.nodeval = nodeval
        self.children = []
        self.add_list(children)

    def add_list(self, aList):
        for c in aList:
            if isinstance(c, EventTree):
                c.parents.append(self);
                self.children.append(c)
           

    def add_child(self, child):
        if isinstance(child, EventTree):
            child.parents.append(self);
            self.children.append(child)


    def iterator(self):
        
        yield self
        for c in self.children:
            for c2 in c.iterator():
                yield c2
            
    def document_string(self):
        return '\n\n'.join([node.nodeval for node in self.iterator()])
        


    
    def header_free_tree(self):
        new_children = []
        for c in self.children:
            children = c.header_free_tree()
            if children:
                if isinstance(children, list):
                    new_children.extend(children)
                else:
                    new_children.append(children) 
        if isinstance(self, SectionNode):
            return new_children
        else:
            return EventTree(nodeval=self.nodeval, children=new_children)
        
    
    def to_ipython(self):
        G=pgv.AGraph()
        self._build_graphviz(G)
        G.layout(prog='dot')
        G.draw('/tmp/wikitree.png')
        from IPython.display import Image
        return Image(filename='/tmp/wikitree.png')

    def _build_graphviz(self, G):        
        par_str = self.nodeval if isinstance(self, SectionNode) else self.nodeval[:30]
        for c in self.children:
            child_str = c.nodeval if isinstance(c, SectionNode) else c.nodeval[:30]
            G.add_edge(par_str, child_str);
            c._build_graphviz(G)
        if isinstance(self, SectionNode):
            G.get_node(par_str).attr['color'] = 'green' 

        
class SectionNode(EventTree):
    def __str__(self):
        return 'Section: {}'.format(self.nodeval)


def make_tree_from_wiki(f, prune_wiki=False):
    """
    Creates an EventTree from Wikipedia page html fragment.

    Parameters
    ----------
    f - a file handle to the html fragment
    prune_wiki - When True, generic sections are not included.
                 Rmeoved sections are: 'See also', 'References', 
                 and 'External links'.
    """

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
        toctext = li.a.get('href')[1:]
        if not prune_wiki or toctext not in ['See_also', 'References', 'External_links']:

            sublist = li.find('ul')
            node = SectionNode(nodeval=toctext) 

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
    clean_text = clean_text.replace('&#160;',' ')
    clean_text = clean_text.replace('\s', ' ')
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
