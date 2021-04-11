'''
TODO: 
- OK - build node graph from a frontend-generated graph def
- OK - gen pseudocode with goto statements representing the fc as a test
- OK - gen AST from fc graph with a goto list and labels dict
- OK - goto- and label diagnostics functions
- OK - goto movement and elimination operations
- OK - use operations to implement the goto-elimination
- OK - generate code from goto-eliminated AST (language specific)
- make it better to work with
- bugfix it
- gen typedefs and stubs (language specific)
'''

from queue import LifoQueue
from goto_elim import *
from pseudocode import *

def cogen(graphdef, typetree, DB_logging=False):
    # create the graph given the graphdef
    graph = SimpleGraph(typetree, graphdef, DB_logging)

    # empty graphdef case
    if len(graph.root.subnodes.values()) == 0:
        return "empty graphdef"

    # get the unique term-enter node or except
    term_Is = [n for n in list(graph.root.subnodes.values()) if type(n)==NodeTerm and n.child != None]
    if len(term_Is) != 1:
        raise Exception("flow control graph must have exactly one entry point")
    term_I = term_Is[0]

    # pseudocode
    pscode = simplegraph_to_pseudocode(term_I, graph.root.subnodes)

    # syntax tree
    ast, gotos, labels = AST_from_flowchart(term_I)

    astrepr = AST_to_text(ast)

    # return data
    return pscode + '\n' + astrepr


''' AST to code operations '''


class AST_line_writer_py:
    def __init__(self, ast_iter):
        self.iter = ast_iter
        self.lines = []
    def write(self):
        a = 4
        node = self.iter.next()
        while node != None:
            l = level(node)
            self.lines.append(''.ljust(l*a) + node.pycode())
            node = self.iter.next()
        return '\n'.join(self.lines)

def get_pycode(ast_root, all_nodes):
    '''  '''
    make_AST_expressions(AST_iterator(ast_root), all_nodes)
    writer = AST_line_writer_py(AST_iterator(ast_root))
    return writer.write()

def dg_expr_read(dgnode):
    ''' Returns an rvalue expression. dgnode: can be a obj, method or func '''
    if dgnode is None:
        return None
    if type(dgnode) in (NodeObj, NodeObjTyped, ):
        varname = dgnode.get_varname()
        return varname
    subtree = build_dg_subtree(dgnode)
    return call_dg_subtree(subtree)
def dg_expr_assign(obj_node):
    ''' returns an assignment expression to obj_node '''
    def getSingleParent(n):
        plst = parents_get(n.parents)
        if len(plst) > 1:
            raise Exception("obj nodes should only have zero or one parents!")
        elif len(plst) == 0:
            return None
        elif len(plst) == 1:
            return plst[0]
    ''' obj_node: must be an obj node which will be assigned to '''
    parent = getSingleParent(obj_node)
    varname = obj_node.get_varname()
    if parent == None:
        return varname
    else:
        return varname + " = " + dg_expr_read(parent)

def make_AST_expressions(ast_iterator, allnodes):
    ''' Makes expressions - pure recursive function calls or assignment calls - out of graph subtrees. '''
    def get_all_bexterns(node):
        bexterns = []
        stack = LifoQueue(maxsize=100)
        if type(node) == AST_if:
            node = node.condition
        elif type(node) == AST_bassign:
            node = node.right

        while node != None:
            if type(node) == AST_bextern:
                bexterns.append(node)
                node = None
            elif type(node) in (AST_not, ):
                node = node.right
            elif type(node) in (AST_or, AST_and, ):
                stack.put_nowait(node.right)
                node = node.left
            else:
                node = None

            if node == None and stack.qsize() > 0:
                node = stack.get_nowait()

        return bexterns

    node = ast_iterator.next()
    while node != None:

        # proc/term generated
        if type(node) == AST_extern:
            if node.dgid == None:
                node.extern_text = "# no dg target"
            else:
                dgnode = allnodes[node.dgid]
                if type(dgnode) in (NodeObj, NodeObjTyped, ):
                    node.extern_text = dg_expr_assign(dgnode)
                elif type(dgnode) in (NodeMethod, NodeFunc, ):
                    node.extern_text = dg_expr_read(dgnode)

        # dec generated
        elif type(node) in (AST_if, AST_bassign, ):
            for bextern in get_all_bexterns(node):
                dgnode = allnodes[bextern.dgid]
                if type(dgnode) in (NodeObj, NodeObjTyped, NodeFunc, NodeMethod, ):
                    bextern.extern_text = dg_expr_read(dgnode)

        node = ast_iterator.next()

