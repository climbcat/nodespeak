'''
Abstract syntax tree types, construction from a simplegraph (flow chart), and iteration.
'''
import queue
from simplegraph import *


''' syntax tree types '''


class AST_root:
    def __init__(self):
        self.block = None
        self.next = None # this should not be used, it's only here to ease iteration
    def __str__(self):
        return "root"
    def __clone__(self):
        return AST_root()
class AST_STM:
    def __init__(self):
        self.prev = None
        self.next = None
        self.up = None # the reverse of AST_FORM.block
class AST_BOOL:
    def __init__(self):
        self.parent = None
class AST_FORK(AST_STM):
    def __init__(self, condition: AST_BOOL):
        super().__init__()
        self.block = None
        self.condition = condition
class AST_BOOLOP(AST_BOOL):
    def __init__(self):
        super().__init__()
    def __clone__(self):
        return AST_BOOLOP()
class AST_bassign(AST_STM):
    def __init__(self, bvar: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.bvar = bvar # must be an AST_bvar !!
        self.right = right
    def pycode(self):
        return "%s = %s" % (self.bvar.pycode(), self.right.pycode())
    def __str__(self):
        return "bassign: " + str(self.bvar) + ", " + str(self.right) 
    def __clone__(self):
        cln = AST_bassign(self.bvar.__clone__(), self.right.__clone__())
        return cln
class AST_extern(AST_STM):
    def __init__(self, dgid: str):
        super().__init__()
        self.dgid = dgid
        self.extern_text = None
    def pycode(self):
        return self.extern_text
    def __str__(self):
        if self.dgid == None:
            return "extern: None"
        else:
            return "extern: " + self.dgid
    def __clone__(self):
        cln = AST_extern(self.dgid)
        cln.extern_text = self.extern_text
        return cln
class AST_ifgoto(AST_STM):
    def __init__(self, ifcond: AST_BOOL): # named ifcond rather than condition to distinguish this from AST_FORK types
        super().__init__()
        self.label = ""
        self.ifcond = ifcond
        self.index = -1
    def pycode(self):
        return "if %s: goto %s" % (self.ifcond.pycode(), self.label)
        raise Exception("AST_ifgoto.pycode: can not be generated")
    def __str__(self):
        return "ifgoto %d: " % self.index + str(self.ifcond) + " -> " + self.label
    def __clone__(self):
        cln = AST_ifgoto(self.ifcond.__clone__())
        cln.label = self.label
        cln.index = self.index
        return cln
class AST_return(AST_STM):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "return"
    def __str__(self):
        return "return"
    def __clone__(self):
        return AST_return()
class AST_pass(AST_STM):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "pass"
    def __str__(self):
        return "pass"
    def __clone__(self):
        return AST_pass()

class AST_if(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def pycode(self):
        return "if %s:" % self.condition.pycode()
    def __str__(self):
        return "if: " + str(self.condition)
    def __clone__(self):
        return AST_if(self.condition.__clone__())
class AST_while(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def pycode(self):
        return "while %s:" % self.condition.pycode()
    def __str__(self):
        return "while: " + str(self.condition)
    def __clone__(self):
        return AST_while(self.condition.__clone__())
class AST_dowhile(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def pycode(self):
        return "dowhile %s:" % self.condition.pycode() # TODO: fix, this doesn't exist in python - maybe while True: ... if not conditon: break
    def __str__(self):
        return "dowhile: " + str(self.condition)
    def __clone__(self):
        return AST_dowhile(self.condition.__clone__())

class AST_bextern(AST_BOOL):
    def __init__(self, dgid: str):
        if dgid == None: # when the dec is not connected
            raise Exception("AST_bextern: Decision nodes must have a target bvar or bfunc, to be used for creating this")
        super().__init__()
        self.dgid = dgid
        self.extern_text = "extern-placeholder"
    def pycode(self):
        return self.extern_text
    def __str__(self):
        return "bexternal: " + self.dgid
    def __clone__(self):
        return AST_bextern(self.dgid)
class AST_bvar(AST_BOOL):
    def __init__(self, varname: str):
        super().__init__()
        self.varname = varname
    def pycode(self):
        return self.varname
    def __str__(self):
        return "bvar: " + self.varname
    def __clone__(self):
        return AST_bvar(self.varname)
class AST_true(AST_BOOL):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "True"
    def __str__(self):
        return "true"
    def __clone__(self):
        return AST_true()
class AST_false(AST_BOOL):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "False"
    def __str__(self):
        return "false"
    def __clone__(self):
        return AST_false()

class AST_or(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.left = left
        self.right = right
    def pycode(self):
        return "%s or %s" % (self.left.pycode(), self.right.pycode())
    def __str__(self):
        return "or: " + str(self.left) + ", " + str(self.right)
    def __clone__(self):
        return AST_or(self.left.__clone__(), self.right.__clone__())
class AST_and(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.left = left
        self.right = right
    def pycode(self):
        return "%s and %s" % (self.left.pycode(), self.right.pycode())
    def __str__(self):
        return "and: " + str(self.left) + ", " + str(self.right)
    def __clone__(self):
        return AST_and(self.left.__clone__(), self.right.__clone__())
class AST_not(AST_BOOLOP):
    def __init__(self, nott: AST_BOOL):
        super().__init__()
        self.right = nott
    def pycode(self):
        return "not %s" % (self.right.pycode(), )
    def __str__(self):
        return "not: " + str(self.right)
    def __clone__(self):
        return AST_return(self.right.__clone__())


''' syntax tree operations '''


class AST_iterator:
    ''' Iterates through the graph in a sequential manor. '''
    def __init__(self, ast_root):
        if not type(ast_root) == AST_root:
            raise Exception("AST_iterator: must initialize using root")
        self.root = ast_root
        self.ast = None
        self.stack = queue.LifoQueue(maxsize=10000) # some outrageously large maxsize here
    def reset(self):
        self.ast = None
    def next(self):
        # first call
        if self.ast == None:
            self.ast = self.root
            return self.root

        # second call
        if self.ast == self.root:
            self.ast = self.ast.block
            return self.ast

        # remaining calls - stack-based branched iteration doing block-first
        if issubclass(type(self.ast), AST_FORK) and self.ast.block != None:
            if self.ast.next:
                self.stack.put_nowait(self.ast.next)
            self.ast = self.ast.block
        else:
            self.ast = self.ast.next
        if self.ast == None and self.stack.qsize() > 0: # safe get no wait
            self.ast = self.stack.get_nowait()
        return self.ast

def AST_to_text(ast):
    ''' Syntax tree visualization as pythonic-ish pseudocode-ish text. '''
    def treePrintRec(astnode, lines, indentlvl=0):
        if astnode == None: # end condition
            return
        if issubclass(type(astnode), AST_root):
            treePrintRec(astnode.block, lines, indentlvl)
            return
        lines.append("".ljust(2 * indentlvl) + str(astnode))
        if issubclass(type(astnode), AST_FORK):
            treePrintRec(astnode.block, lines, indentlvl + 1)
            treePrintRec(astnode.next, lines, indentlvl)
        elif hasattr(astnode, "next"):
            treePrintRec(astnode.next, lines, indentlvl)

    lines = []
    treePrintRec(ast, lines)
    return '\n'.join(lines)

def AST_clone_tree(ast):
    def list_safe_get(lst, idx):
        try:
            return lst[idx]
        except:
            return None

    clones = []
    idx_by_node = {}

    # create all clones and associate positions with an index
    ast_iterator = AST_iterator(ast)
    node = ast_iterator.next()
    idx = 0
    while node != None:
        clones.append(node.__clone__())
        idx_by_node[node] = idx
        idx += 1
        node = ast_iterator.next()

    # use index of next,prev,block,up nodes to set
    ast_iterator.reset()
    node = ast_iterator.next()
    while node != None:
        clone = clones[idx_by_node[node]]
        if hasattr(node, "next"):
            clone.next = list_safe_get(clones, idx_by_node.get(node.next, None))
        if hasattr(node, "prev"):
            clone.prev = list_safe_get(clones, idx_by_node.get(node.prev, None))
        if hasattr(node, "block"):
            clone.block = list_safe_get(clones, idx_by_node.get(node.block, None))
        if hasattr(node, "up"):
            clone.up = list_safe_get(clones, idx_by_node.get(node.up, None))
        node = ast_iterator.next()

    cloned_ast = clones[0]
    return cloned_ast

def AST_connect(stm1: AST_STM, stm2: AST_STM):
    '''
    Connect two AST statement nodes.
    
    Will always connect "block first" when stm1 is an AST_if or an AST_dowhile.
    '''
    if issubclass(type(stm1), AST_FORK) and issubclass(type(stm2), AST_STM):
        if stm1.block == None:
            stm1.block = stm2
            stm2.up = stm1
        else:
            stm1.next = stm2
            stm2.prev = stm1
    elif issubclass(type(stm1), AST_STM) and issubclass(type(stm2), AST_STM):
        stm1.next = stm2
        stm2.prev = stm1
    elif type(stm1) == AST_root and issubclass(type(stm2), AST_STM):
        stm1.block = stm2
        stm2.up = stm1 # this is also debatable, but we do need some end condition
    else:
        raise Exception("stm1 and stm2 must be AST_STM (are type hints enforced?)")

def AST_from_flowchart(fcroot):
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
    stack = queue.LifoQueue(maxsize=1000)
    node = fcroot
    astroot = AST_root()
    astnode = astroot

    # TODO: infinite loop possible here??
    while node is not None:
        vis = visited.get(node.fcid, None)
        if vis is not None:
            astnew = AST_ifgoto(AST_true())
            astnew.label = vis.label # putting this information aids debugging
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

    # dg_expr_assign an index to each goto to ease debugging
    gidx = 0
    for g in gotos:
        g.index = gidx
        gidx = gidx + 1

    # done
    return astroot, gotos, labels

