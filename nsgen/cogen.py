'''
TODO: 
- OK - build node graph from a frontend-generated graph def
- OK - gen pseudocode with goto statements representing the fc as a test
- OK - gen AST from fc graph with a goto list and labels dict
- write atomic goto-lifting and goto-elimination operations operating on the AST
- use operations to implement the goto-elimination alg operating on the AST
- gen code from goto-eliminated AST (language specific)
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

    # flowchart to pseudocode:
    lines = flowchartToPseudocode(term_I)
    makeLineExpressions(lines, graph.root.subnodes)
    lw = LineWriter(lines)
    text = lw.write()
    print(text)

    # flowchart to syntax tree:
    astroot = AST_root()
    try:
        labels, gotos = flowchartToSyntaxTree(term_I, astroot)
    except Exception as e:
        print("FAIL: " + str(e))

    return text


'''
Flow chart to AST (syntax tree) generation and AST manipulation.
'''
# tree building types with parent nodes
class AST_root: # ast global handle signaling enter/start
    def __init__(self):
        self.parent = None;
        self.child = None
    def __str__(self):
        return "root"
class AST_bassign: # statement: assignment to a boolean (only cogen'd)
    def __init__(self):
        self.parent = None
        self.child = None
        self.varname = None # bvar
        self.right = None # brval or bext
    def __str__(self):
        return "bassign"
class AST_extern: # statement: external expression (dg subtree call)
    def __init__(self):
        self.parent = None
        self.child = None
        self.dgid = None
    def __str__(self):
        return "extern"
class AST_goto: # statement: goto label
    '''
    NOTE: the label will be handled by a list containing goto's and their labels,
    and a label dict pointing to the appropriate AST locations
    '''
    def __init__(self):
        self.parent = None # goto's are dead ends in terms of having no AST children
    def __str__(self):
        return "goto"
class AST_return: # statement: flow exit, implies generating a return/exit statement
    def __init__(self):
        self.parent = None
    def __str__(self):
        return "return"
class AST_if:
    def __init__(self):
        self.parent = None
        self.child0 = None # false branch
        self.child1 = None # true branch
        self.condition = None# bvar, brval or bext
    def __str__(self):
        return "if"
class AST_dowhile:
    def __init__(self):
        self.parent = None
        self.child0 = None
        self.child1 = None
        self.condition = None # bvar, brval or bext
    def __str__(self):
        return "dowhile"
# supporting types
class AST_bvar: # boolean value
    def __init__(self):
        self.parent = None
        self.varname = None
    def __str__(self):
        return "bvar"
class AST_brval: # probably only true/false, of which we will only use true...
    # TODO: should we just use AST_true and AST_false instead?
    def __init__(self):
        self.parent = None
        self.valueexpr = None
    def __str__(self):
        return "brval"
class AST_bext: # external (dg) boolean value, not necessarily an rval
    def __init__(self):
        self.parent = None
        self.dgid = None
class AST_or:
    def __init__(self):
        self.parent = None
        self.left = None # bvar, brval, bext
        self.right = None # bvar, brval, bext
    def __str__(self):
        return "or"
class AST_not:
    def __init__(self):
        self.parent = None
        self.right = None # bvar, brval, bext
    def __str__(self):
        return "not"

''' syntax tree operations '''
def AST_connect(p, c, branchfirst=0):
    ''' connects a primary syntax tree node with a subnode '''
    ''' NOTE: branchfirst parameter decides how c should be connected to a binary branch p '''
    if type(c) in (AST_root, ):
        raise Exception("AST_connect error: AST_root can have no parent")
    # c has a parent
    if type(p) in (AST_root, AST_bassign, AST_extern, AST_return, ):
        p.child = c
        c.parent = p
    elif type(p) in (AST_if, AST_dowhile, ):
        if branchfirst==0 and p.child0 == None:
            p.child0 = c
        elif branchfirst==0 and p.child1 == None:
            p.child1 = c
        elif branchfirst==1 and p.child0 == None:
            p.child0 = c
        elif branchfirst==1 and p.child1 == None:
            p.child1 = c
        else:
            raise Exception("AST_connect: inconsistent use of branchfirst or too many children")

        c.parent = p
    else:
        raise Exception("AST_connect error: %s, %s" % (str(p), str(c)))
_bool_rval_types = (AST_bvar, AST_brval, AST_extern, AST_not, AST_or, )
def AST_leaf(p, c1, c2=None):
    ''' connects certain primary syntax tree nodes (bassign/if/dowhile) with leaf children '''
    if type(p) in (AST_bassign, ):
        if type(c1) in (AST_bvar, ) and type(c2) in _bool_rval_types:
            p.varname = c1
            p.right = c2
            c1.parent = p
            c2.parent = p
        else: 
            raise Exception("AST_leaf: AST_bassign can leaf a pair of (AST_bvar, AST_bvar/AST_brval)")
    if type(p) in (AST_if, AST_dowhile, ) and c2 == None:
        if type(c1) in _bool_rval_types:
            pass
        else:
            raise Exception("AST_leaf: AST_if/AST_dowhile can leaf a condition AST_bvar/AST_brval")
def AST_notleaf(p, c):
    if type(p) in (AST_not, ) and type(c) in _bool_rval_types:
        p.right = c
        c.parent = p
    else:
        raise Exception("AST_notleaf: mismatch")
def AST_orleaf(p, c1, c2):
    if type(p) in (AST_or, ) and type(c1) in _bool_rval_types and type(c2) in _bool_rval_types:
        p.left = c1
        p.right = c2
        c1.parent = p
        c2.parent = p
    else:
        raise Exception("AST_orleaf: mismatch")

def treePrintRec(astnode, indentlvl):
    print("".ljust(2*indentlvl) + str(astnode))
    if type(astnode) in (AST_if, AST_dowhile, ):
        treePrintRec(astnode.child0, indentlvl+1)
        treePrintRec(astnode.child1, indentlvl+1)
    else:
        if hasattr(astnode, "child"):
            treePrintRec(astnode.child, indentlvl+1)
    

def flowchartToSyntaxTree(fcroot, astroot):
    '''
    Flowchart to syntax tree graph iterator.
    At this level, only if, extern, goto and a return nodes are needed.
    (Here, extern refers to a dgid, AKA a subtree expression.)

    Returns astroot, a dict of goto:label node pairs and a list of all goto nodes.
    '''
    def getSingleChild(node):
        return node.child
    def getChild0(node):
        return node.child0
    def getChild1(node):
        return node.child1

    idx = 0
    visited = {} # visited node ids
    treesibs = {} # corresponding point in the AST to every fc node, used for creating the labels
    labels = {} # goto:label pairs, where label is an ast node
    gotos = [] # chronological list of goto's (according to tree building order)
    stack = LifoQueue(maxsize=1000)
    node = fcroot # new AST node is created from this
    astnode = astroot # new AST node becomes connected to this

    # TODO: infinite loop here??
    while node is not None:
        vis = visited.get(node.fcid, None)
        if vis is not None:
            astnew = AST_goto()
            labels[astnew] = treesibs[vis]
            gotos.append(astnew)
            AST_connect(astnode, astnew)

            # signal get from stack
            astnode = None
            node = None # flag LineClose
        else:
            visited[node.fcid] = node
            if type(node) == NodeDecision:
                # if branch:

                astnew = AST_if()
                astcond = AST_extern()
                astcond.dgid = node.dgid
                astnew.condition = astcond
                AST_connect(astnode, astnew, branchfirst=1)
                astnode = astnew

                # save state for branch 0:
                stack.put( (getChild0(node), astnode) )

                # continue iterating on branch 1:
                treesibs[node] = astnew
                node = getChild1(node)
            else:
                # stm or return:

                astnew = AST_extern()
                astnew.dgid = node.dgid
                AST_connect(astnode, astnew)

                treesibs[node] = astnew
                node = getSingleChild(node)
                if not node:
                    AST_connect(astnew, AST_return())
                    astnode = None # the end:)
                else:
                    astnode = astnew # continue

        if node == None:
            if stack.qsize() > 0:  # safe get no wait
                (node, astnode) = stack.get_nowait()

    return labels, gotos


def findCommonParentFork(ast1, ast2):
    ''' find the common parent fork of ast1 and ast2 '''
    forks = []
    if ast1.parent == None or ast2.parent == None:
        return None
    
    # map all forks above ast1
    parent = ast1.parent
    while parent is not None:
        if type(parent) in (AST_if, AST_dowhile, ):
            forks.append(parent)
        parent = parent.parent
    
    # search ast2's parent forks for a match
    parent = ast2.parent
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
    '''
    For every line, inserts expression text corresponding to the target data graph node subtree execution pseudocode expression.
    '''
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
        if l.dgid is None:
            continue
        # proc/term generated lines
        if type(l) in (LineStatement, ):
            target = allnodes[l.dgid]
            if type(target) in (NodeObj, NodeMethod, ):
                l.text = assign(target)
            elif type(target) in (NodeMethod, ):
                l.text = read(target)
            else:
                raise Exception("fc proc/term can only be associated with Obj or Method dg nodes: %s" % target.name)
        # dec generated lines
        elif type(l) in (LineBranch, ):
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

