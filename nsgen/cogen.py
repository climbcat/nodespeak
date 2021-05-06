'''
TODO: 
- OK - build node graph from a frontend-generated graph def
- OK - gen pseudocode with goto statements representing the fc as a test
- OK - gen AST from fc graph with a goto list and labels dict
- OK - goto- and label diagnostics functions
- OK - goto movement and elimination operations
- OK - use operations to implement the goto-elimination
- OK - generate code from goto-eliminated AST (language specific)
- OK - make it better to work with
- OK - bugfix it
- gen typedefs and stubs (language specific)
'''
from queue import LifoQueue
from gotoelim import *
from pseudocode import *


def cogen_graphs_py(graphdef, typetree, DB_logging=False):
    # create the graph given the graphdef
    graph = SimpleGraph(typetree, graphdef, DB_logging)
    allnodes = graph.root.subnodes

    # empty graphdef case
    if len(allnodes) == 0:
        return "empty graphdef"

    # get the unique term-enter node or except
    term_Is = [n for n in graph.root.subnodes.values() if type(n)==NodeTerm and n.child != None]
    if len(term_Is) != 1:
        raise Exception("flow control graph must have exactly one entry point")
    term_I = term_Is[0]

    # create ast and eliminate gotos
    ast, gotos, labels = AST_from_flowchart(term_I)
    log = goto_elimination_alg(gotos, labels, ast, allnodes)

    # get the final result and return
    ast_final = log.last_ast()
    AST_make_expressions(ast_final, allnodes)
    return AST_write_pycode(ast_final)

class UserTypetreeItem:
    def __init__(self, tpe, basetype, ipars, itypes, otypes, label):
        self.tpe = tpe
        self.basetype = basetype
        self.ipars = ipars
        self.itypes = itypes
        self.otypes = otypes
        self.label = label
        self.method = []

    def __str__(self):
        if self.basetype == "function_named":
            return "def %s(%s):\n    pass" % (self.tpe, ", ".join(self.ipars))

        elif self.basetype == "object_typed":
            # we should not do this when generating Python code
            return "# %s - typedefs not generated for Python" % self.tpe

        elif self.basetype == "constructor":
            if len(self.ipars) > 0:
                lst = []
                lst.append("class %s(%s):" % (self.tpe, ", ".join(self.ipars)))
                lst.append("    def __init__(self, %s):" % (", ".join(self.ipars)))
                lst.append("        pass")

                return "\n".join(lst)
            else:
                return "class %s:\n    pass" % self.tpe

        elif self.basetype == "method":
            if len(self.ipars) > 0:
                lst = []
                lst.append("    def %s(self, %s):" % (self.tpe, ", ".join(self.ipars)))
                lst.append("        pass")

                return "\n".join(lst)
            else:
                return "    def %s(self):\n        pass" % self.tpe

        else:
            return self.basetype + " - " + self.tpe

def cogen_typedefs_py(typetree):
    
    # extract data from the typedef tree thingee

    # load user types subtree
    tree = TreeJsonAddr(typetree["user"]["branch"]["custom"]["branch"])
    user_addr = list(typetree["user"]["branch"]["custom"]["branch"].keys()) 

    user_tpes = []
    user_methods = {}
    for addr in user_addr:
        localobj = tree.retrieve(addr)

        user_tpe = UserTypetreeItem(
            tpe = localobj["type"],
            basetype = localobj["basetype"],
            ipars = localobj["ipars"],
            itypes = localobj["itypes"],
            otypes = localobj["otypes"],
            label = localobj["label"])

        user_tpes.append(user_tpe)

        # get the methods from this branch
        if user_tpe.basetype == "constructor":

            branch = typetree["user"]["branch"]["custom"]["branch"][user_tpe.tpe]["branch"]
            user_methods[user_tpe.tpe] = []
            for a in branch.keys():

                method_obj = tree.retrieve(addr + "." + a)

                user_mthod = UserTypetreeItem(
                    tpe = method_obj["type"],
                    basetype = method_obj["basetype"],
                    ipars = method_obj["ipars"],
                    itypes = method_obj["itypes"],
                    otypes = method_obj["otypes"],
                    label = method_obj["label"])

                user_methods[user_tpe.tpe].append(user_mthod)

    # generate the code

    class LinesPrinter():
        def __init__(self):
            self.lines = []
        def print(self, printable=None):
            if printable is not None:
                self.lines.append(printable.__str__())
            else:
                self.lines.append("")
        def get_text(self):
            return "\n".join(self.lines)
    lines = LinesPrinter()

    # print typedefs (should not be in pythonic cogen_graphs_py?)
    for user_tpe in user_tpes:
        if user_tpe.basetype != "object_typed":
            continue
        lines.print(user_tpe)
        lines.print()

    # print classes
    for user_tpe in user_tpes:
        if user_tpe.basetype != "constructor":
            continue
        lines.print(user_tpe)

        # print its methods
        for method_tpe in user_methods[user_tpe.tpe]:
            lines.print(method_tpe)

    # print function_named
    for user_tpe in user_tpes:
        if user_tpe.basetype != "function_named":
            continue
        lines.print()
        lines.print(user_tpe)

    return lines.get_text()


'''  typedefs to code '''

def typedefs_to_code(ast): pass


''' AST to code '''


class AST_writer_py:
    def __init__(self, ast_iter):
        self.iter = ast_iter
        self.lines = []
    def write(self):
        a = 4
        node = self.iter.next()
        if type(node) is AST_root:
            node = self.iter.next()

        while node != None:
            l = level(node)
            self.lines.append(''.ljust(l*a) + node.pycode())
            node = self.iter.next()
        return '\n'.join(self.lines)

def AST_write_pycode(ast_root):
    ''' call AST_make_expressions first! '''
    writer = AST_writer_py(AST_iterator(ast_root))
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

def AST_make_expressions(ast_root, allnodes):
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

    ast_iterator = AST_iterator(ast_root)

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

