'''
TODO: 
- OK - build node graph from a frontend-generated graph def
- OK - gen pseudocode with goto statements representing the fc as a test
- OK - gen AST from fc graph with a goto list and labels dict
- goto- and label diagnostics functions
- goto movement and elimination operations
- use operations to implement the goto-elimination
- generate code from goto-eliminated AST (language specific)
- gen typedefs and stubs (language specific)
'''

from queue import LifoQueue
from simplegraph import *


'''
Cogen interface
'''
def cogen(graphdef, typetree):
    # create the graph given the graphdef
    graph = SimpleGraph(typetree, graphdef)

    # get the unique term-enter node or except
    term_Is = [n for n in list(graph.root.subnodes.values()) if type(n)==NodeTerm and n.child != None]
    if len(term_Is) != 1:
        raise Exception("flow control graph must have exactly one entry point")
    term_I = term_Is[0]

    # pseudocode
    pscode = get_pseudocode(term_I, graph.root.subnodes)

    # syntax tree
    ast = get_ast(term_I)

    # return data
    return pscode

def get_pseudocode(enter_node, all_nodes):
    lines = flowchartToPseudocode(enter_node)
    makeLineExpressions(lines, all_nodes)
    lw = LineWriter(lines)
    return lw.write()

def get_ast(enter_node):
    astroot = None
    gotos = None
    labels = None
    try:
        astroot, gotos, labels = flowchartToSyntaxTree(enter_node)
    except Exception as e:
        print("FAIL: " + str(e))
    
    treePrintRec(astroot)
    return astroot


'''
AST (abstract syntax tree) types
'''
class AST_root:
    def __init__(self):
        self.next = None
    def __str__(self):
        return "root"

class AST_STM: pass
class AST_BOOL: pass
class AST_FORK(AST_STM): pass
class AST_BOOLOP(AST_BOOL): pass

class AST_bassign(AST_STM):
    def __init__(self, bvar: AST_BOOL, right: AST_BOOL):
        self.prev = None
        self.next = None
        self.bvar = bvar # must be an AST_bvar !!
        self.right = right
    def __str__(self):
        return "bassign: " + str(self.bvar) + ", " + str(self.right) 
class AST_extern(AST_STM):
    def __init__(self, dgid: str):
        self.prev = None
        self.next = None
        self.dgid = dgid
        if dgid == None:
            pass
    def __str__(self):
        return "extern: " + self.dgid
class AST_ifgoto(AST_STM):
    def __init__(self, condition: AST_BOOL):
        self.prev = None
        self.next = None
        self.condition = condition
    def __str__(self):
        return "ifgoto: " + str(self.condition)
class AST_return(AST_STM):
    def __init__(self):
        self.prev = None
        self.next = None
    def __str__(self):
        return "return"

class AST_if(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        self.prev = None
        self.next = None
        self.block = None
        self.condition = condition
    def __str__(self):
        return "if: " + str(self.condition)
class AST_dowhile(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        self.prev = None
        self.next = None
        self.block = None
        self.condition = condition
    def __str__(self):
        return "dowhile: " + str(self.condition)

class AST_bextern(AST_BOOL):
    def __init__(self, dgid: str):
        self.parent = None
        self.dgid = dgid
    def __str__(self):
        return "bexternal: " + self.dgid
class AST_bvar(AST_BOOL):
    def __init__(self, varname: str):
        self.parent = None
        self.varname = varname
    def __str__(self):
        return "bvar: " + self.varname
class AST_true(AST_BOOL):
    def __init__(self):
        self.parent = None
    def __str__(self):
        return "true"
class AST_false(AST_BOOL):
    def __init__(self):
        self.parent = None
    def __str__(self):
        return "false"

class AST_or(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        self.parent = None
        self.left = left
        self.right = right
    def __str__(self):
        return "or: " + str(self.left) + ", " + str(self.right)
class AST_and(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        self.parent = None
        self.left = left
        self.right = right
    def __str__(self):
        return "and: " + str(self.left) + ", " + str(self.right)
class AST_not(AST_BOOLOP):
    def __init__(self, right: AST_BOOL):
        self.parent = None
        self.right = right
    def __str__(self):
        return "not: " + str(self.right)


def AST_is_statement(node):
    return issubclass(node, AST_STM, )
def AST_is_boolean(node):
    return issubclass(node, AST_BOOL, )


''' syntax tree operations '''

def AST_connect(stm1: AST_STM, stm2: AST_STM):
    ''' Will always connect "block first" when stm1 is an AST_if or an AST_dowhile. '''
    if issubclass(type(stm1), AST_FORK) and issubclass(type(stm2), AST_STM):
        if stm1.block == None:
            stm1.block = stm2
            stm2.prev = stm1 # this is debatable, but we do need to move "up" somehow
        else:
            stm1.next = stm2
            stm2.prev = stm1
    elif issubclass(type(stm1), AST_STM) and issubclass(type(stm2), AST_STM):
        stm1.next = stm2
        stm2.prev = stm1
    elif type(stm1) == AST_root and issubclass(type(stm2), AST_STM):
        stm1.next = stm2
        stm2.prev = stm1 # this is also debatable, but we do need some end condition
    else:
        raise Exception("stm1 and stm2 must be AST_STM (are type hints enforced?)")

def treePrintRec(astnode, indentlvl=0):
    if astnode == None: # end condition
        return
    print("".ljust(2*indentlvl) + str(astnode))
    if issubclass(type(astnode), AST_FORK):
        treePrintRec(astnode.block, indentlvl+1)
        treePrintRec(astnode.next, indentlvl+1)
    else:
        if hasattr(astnode, "next"):
            treePrintRec(astnode.next, indentlvl+1)

def flowchartToSyntaxTree(fcroot):
    '''
    Flowchart to syntax tree iterator using queues.

    Returns the ast root node, a list of all gotos, and a dict of goto:label pairs.
    '''
    def getSingleChild(node):
        return node.child
    def getChild0(node):
        return node.child0
    def getChild1(node):
        return node.child1

    visited = {} # visited node ids
    treesibs = {} # corresponding point in the AST to every fc node, used for creating the labels
    labels = {} # goto:label pairs, where label is an ast node
    gotos = [] # chronological list of goto's (depends on ast building order)
    stack = LifoQueue(maxsize=1000)
    node = fcroot
    astroot = AST_root()
    astnode = astroot

    # TODO: infinite loop here??
    while node is not None:
        vis = visited.get(node.fcid, None)
        if vis is not None:
            astnew = AST_ifgoto(AST_true())
            labels[astnew] = treesibs[vis]
            gotos.append(astnew)
            AST_connect(astnode, astnew)

            # signal get from stack
            astnode = None
            node = None # flag LineClose
        else:
            visited[node.fcid] = node
            if type(node) == NodeDecision:
                # if fork:
                astnew = AST_if(AST_bextern(node.dgid))
                AST_connect(astnode, astnew)
                astnode = astnew

                # save state for branch 0:
                stack.put( (getChild0(node), astnew) )

                # continue iterating on branch 1:
                treesibs[node] = astnew
                node = getChild1(node)
            else:
                # stm or return:
                astnew = AST_extern(node.dgid)
                AST_connect(astnode, astnew)

                treesibs[node] = astnew
                node = getSingleChild(node)
                if not node:
                    AST_connect(astnew, AST_return())
                    astnode = None # end of branch
                else:
                    astnode = astnew # continue

        if node == None:
            if stack.qsize() > 0:  # safe get no wait
                (node, astnode) = stack.get_nowait()

    return astroot, gotos, labels


def findCommonParentFork(n1, n2):
    ''' find the common parent fork of n1 and n2 '''
    forks = []
    if n1.parent == None or n2.parent == None:
        return None
    
    # map all forks above n1
    parent = n1.parent
    while parent is not None:
        if type(parent) in (AST_if, AST_dowhile, ):
            forks.append(parent)
        parent = parent.parent
    
    # search n2's parent forks for a match
    parent = n2.parent
    while parent is not None:
        if type(parent) in (AST_if, AST_dowhile, ):
            if parent in forks:
                return parent
        parent = parent.parent


'''
Flow chart to pseudocode generation. Pseudocode is a list of "line" objects which can be printed into actual pseudocode.
But this is not sufficient for goto-elimination, which requires a syntax tree for various manipulations.
'''

def makeLineExpressions(lines, allnodes):
    ''' For every line, insert text corresponding to the target data graph node subtree. '''
    def read(dgnode):
        ''' Returns an rvalue expression. dgnode: can be a obj, method or func '''
        if dgnode is None:
            return None
        if type(dgnode) in (NodeObj, NodeObjTyped, ):
            varname = dgnode.get_varname()
            return varname
        subtree = build_dg_subtree(dgnode)
        return call_dg_subtree(subtree)
    def assign(obj_node):
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
            return varname + " = " + read(parent)


    for l in lines:
        # proc/term generated lines
        if type(l) in (LineStatement, ):
            if l.dgid is None:
                l.text = "/* " + l.node.label + " */"
                continue

            target = allnodes[l.dgid]
            if type(target) in (NodeObj, ):
                l.text = assign(target)
            elif type(target) in (NodeMethod, ):
                l.text = read(target)
            else:
                raise Exception("fc proc/term can only be associated with Obj or Method dg nodes: %s" % target.name)
        # dec generated lines
        elif type(l) in (LineBranch, ):
            if l.dgid is None:
                l.text = "/* " + l.node.label + " */"
                continue

            target = allnodes[l.dgid]
            if type(target) in (NodeObj, NodeObjTyped, NodeFunc, NodeMethod, ):
                txt = read(target)
                l.setText(txt)
            else:
                raise Exception("fc dec can only be associated with Obj, Func or Method nodes: %s" % target.name)

class LineWriter:
    def __init__(self, lines, indent=4):
        self.ilines = lines
        self.olines = []
        self.indent_amount = indent
        self.indent_level = 0
    def write(self):
        a = self.indent_amount
        i = self.indent_level
        lineno = 1
        for l in self.ilines:
            # postivie: adjust indentation level after
            if l.ilvl<1:
                i = i + l.ilvl
            # indent and print line
            self.olines.append(str(lineno).ljust(4) + ''.ljust(i*a) + str(l))
            # postivie: adjust indentation level after
            if l.ilvl >= 0:
                i = i + l.ilvl
            lineno = lineno + 1
        return '\n'.join(self.olines)

class LineStatement:
    def __init__(self, node):
        self.node = node
        self.dgid = node.dgid # target
        self.ilvl = 0
        self.text = None
    def __str__(self):
        s = self.dgid
        if self.dgid == None:
            s = "/* empty: */"
        if self.text != None:
            return self.text
        return s
class LineReturnStatement:
    def __init__(self):
        self.dgid = None
        self.ilvl = 0
    def __str__(self):
        return "return"

class LineBranch:
    def __init__(self, node):
        self.node = node
        self.dgid = node.dgid # target
        self.ilvl = 1
        self.text = None
    def setText(self, readexpr):
        self.text = "if %s {" % readexpr 
    def __str__(self):
        s = self.dgid
        if self.dgid == None:
            s = "/* empty */"
        if self.text != None:
            return self.text
        return "if %s {" % s
class LineClose:
    def __init__(self):
        self.dgid = None
        self.ilvl = -1
    def __str__(self):
        return "}"
class LineOpen:
    def __init__(self):
        self.dgid = None
        self.ilvl = 1
    def __str__(self):
        return "{"
class LineGoto:
    def __init__(self, fcid):
        self.dgid = None
        self.fcid = fcid # target
        self.lineno = None
        self.ilvl = 0
    def __str__(self):
        return "goto " + str(self.lineno)
    def setLineNo(self, lineno):
        self.lineno = lineno


def flowchartToPseudocode(root):
    ''' flowchart-to-pseudocode graph iterator '''
    def isBranch(node):
        return type(node) == NodeDecision
    def getFcId(node):
        return node.fcid
    def getSingleChild(node):
        return node.child
    def getChild0(node):
        return node.child0
    def getChild1(node):
        return node.child1

    idx = 0
    vis = {} # visited node id:idx entries
    lines = [LineOpen()] # just a line open, because everything ends in a line close
    idx = idx + 1 # line was added
    stack = LifoQueue(maxsize=100) # some outrageously large maxsize here
    node = root

    while node is not None:
        fcid = getFcId(node)
        if vis.get(fcid, None):
            lines.append(LineGoto(fcid))
            node = None # flag LineClose
        else:
            vis[fcid] = idx
            if isBranch(node):
                lines.append(LineBranch(node))
                stack.put(getChild0(node))
                node = getChild1(node)
            else:
                # append statment or return statement
                stm = LineStatement(node)
                lines.append(stm)
                node = getSingleChild(node)
                if node == None:
                    idx = idx + 1
                    lines.append(LineReturnStatement())
        if node == None:
            idx = idx + 1
            lines.append(LineClose())
            if stack.qsize() > 0:  # safe get no wait
                node = stack.get_nowait()
        idx = idx + 1

    # assign lineno to goto's
    for l in lines:
        if type(l) == LineGoto:
            l.lineno = vis[l.fcid] + 1 # LINES start at 1, indexes at zero

    return lines

