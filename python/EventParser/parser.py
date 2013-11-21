from collections import namedtuple, defaultdict
import pygraphviz as pgv

class Edge(namedtuple('Edge', ['tail','head'])):
    def __str__(self):
        return '({}, {})'.format(self.tail, self.head)

        
class Graph:
    def __init__(self, edges=set()):
        self.edges = set()
        self.outgoing = defaultdict(set)
        self.incoming = defaultdict(set)
        self.add_edges(edges)

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(edge)
    
    def add_edge(self, edge):
        self.edges.add(edge)
        self.outgoing[edge.tail].add(edge)
        self.incoming[edge.head].add(edge)
    
    def delete_vertex(self, u):
        for e in [e for e in self.incoming[u]
                  if e in self.edges]:         
            self.edges.remove(e)
        for e in [e for e in self.outgoing[u]
                  if e in self.edges]:
            self.edges.remove(e)    
        
        del self.outgoing[u]
        del self.incoming[u]
          



class MSTParser:
    """
    Maximum Spanning Tree parser. Parses a directed graph
    of EventTree nodes into a tree structure using the
    Chu-Liu-Edmonds algorithm.
    """    
    def __init__(self, edge_scores):
        self.score = edge_scores
        self._dbg_imgs = None
        
    def parse(self, g, debug=False):
        
        if debug:
            if not self._dbg_imgs:
                self._dbg_imgs = []
            self._make_dbg_img(g, 'stage1.png')
        
        m = self._max_incoming_edge_graph(g)
        
        if debug:
            self._make_dbg_img(m, 'stage2.png')
        component = self._find_cycle(m)
        if component:
            if debug:
                print 'Found cycle: {}'.format(component)
            gc, cycle = self._contract(g, component)
            if debug:
                self._make_dbg_img(gc, 'stage3.png')
            gq = self.parse(gc)
            if debug:
                self._make_dbg_img(gq, 'stage4.png')
            tree = self._expand(g, gq, cycle)
            if debug:
                self._make_dbg_img(tree, 'stage5.png')
            return tree
                
        else:
            return m
       
    def _expand(self, old_g, new_g, cycle):
        into_cycle_vertex = None 
        if len(new_g.incoming[cycle.synth]) > 0: 
            (inedge,) = new_g.incoming[cycle.synth]
            u = inedge.tail
            max_edge = max([edge for edge 
                            in old_g.outgoing[u]
                            if edge.head in cycle.int_vertices],
                           key=lambda e: self.score[e])
            new_g.add_edge(max_edge)
            into_cycle_vertex = max_edge.head
        else:
            min_edge = min([e for e in cycle.int_edges],
                key=lambda e: self.score[e])
            into_cycle_vertex = min_edge.head


        new_g.add_edges(cycle.out_edges)
        for edge in cycle.int_edges:
            if edge.head != into_cycle_vertex:
                new_g.add_edge(edge)
        new_g.delete_vertex(cycle.synth)
        return new_g
        
    def _max_incoming_edge_graph(self, g):
        edge_list = set()
        for in_edges in [g.incoming[v] for v in g.incoming]:
            if len(in_edges) > 0:
                max_edge = max(in_edges, key=lambda e: self.score[e])
                edge_list.add(max_edge)
        return Graph(edges=edge_list)
    
    
    def _find_cycle(self, g):
            
        cntr = _Counter()
        self._indices = defaultdict(lambda: cntr.next())
        self._lowlink = {}  
        self._stack = []
        
        for u in g.outgoing:
            if u not in self._indices:
                component = self._find_strongly_connected(u, g)
                if component:
                    return component
            return None
        
    
    def _find_strongly_connected(self, u, g):
        index = self._indices[u]
        self._lowlink[u] = index
        
        self._stack.append(u)
        
        for edge in g.outgoing[u]:
            v = edge.head
            if v not in self._indices:
                self._find_strongly_connected(v, g)
                self._lowlink[u] = min(self._lowlink[u], self._lowlink[v])
            elif v in self._stack:
                self._lowlink[u] = min(self._lowlink[u], self._indices[v])
        
        if self._indices[u] == self._lowlink[u]:
            component = set([u])
            while len(self._stack) > 0:
                w = self._stack.pop()
                component.add(w)
                if w == u:
                    break
            if len(component) > 1:
                return component
            else:
                return None

    
    def _contract(self, prev_g, cycle):
        new_g = Graph()
        
        incycle_parent_edge = {}
        edges_to_child = defaultdict(set)
        
        for u in cycle:
            for edge in prev_g.outgoing[u]:
                edges_to_child[edge.head].add(edge)
            for edge in prev_g.incoming[u]:
                if edge.tail in cycle:
                    incycle_parent_edge[u] = edge
    
            
        synth = "-".join([u for u in cycle])
        orig_outgoing = []
        for child in edges_to_child:
            outside_verts = [edge for edge in edges_to_child[child] 
                             if edge.head not in cycle]
            if len(outside_verts) > 0:
                max_edge = max(outside_verts,
                               key=lambda e: self.score[e])
                new_edge = Edge(synth, max_edge.head)
                self.score[new_edge] = self.score[max_edge]
                new_g.add_edge(new_edge)
                orig_outgoing.append(max_edge)
    
        in_cycle_score = sum([self.score[incycle_parent_edge[u]] 
                              for u in cycle]) 
        
        for u in prev_g.outgoing:
            if u not in cycle:
                max_edge = None
                into_cyc_edges = [e for e in prev_g.outgoing[u]
                                  if e.head in cycle]
                if len(into_cyc_edges) > 0:
                    score = max([self.score[e] 
                                 - self.score[incycle_parent_edge[e.head]]
                                 + in_cycle_score
                                 for e in into_cyc_edges])
                    new_edge = Edge(u, synth)
                    self.score[new_edge] = score
                    new_g.add_edge(new_edge)
        
        for edge in prev_g.edges:
            if edge.head not in cycle and edge.tail not in cycle:
                    new_g.add_edge(edge)
    
        
        return (new_g, _Cycle(synth, 
                              cycle, 
                              incycle_parent_edge.values(), 
                              orig_outgoing))
  
        
    
    def _make_dbg_img(self, g, filename):
        disp_g = pgv.AGraph(directed=True)
        disp_g.edge_attr.update(len='3.0')
        for e in g.edges:
            disp_g.add_edge(e.tail,
                            e.head,
                            label = self.score[e])
        disp_g.layout()
        disp_g.draw(filename)
        self._dbg_imgs.append(filename) 


class _Cycle(namedtuple('Cycle', ['synth','int_vertices','int_edges', 'out_edges'])):
    def __str__(self):
        return 'Cycle({})'.format(self.int_vertices)

class _Counter:
    def __init__(self):
        self.index = 0
    def next(self):
        val = self.index
        self.index += 1
        return val
