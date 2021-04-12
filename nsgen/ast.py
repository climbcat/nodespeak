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
class AST_bassign(AST_STM):
    def __init__(self, bvar: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.bvar = bvar # must be an AST_bvar !!
        self.right = right
    def pycode(self):
        return "%s = %s" % (self.bvar.pycode(), self.right.pycode())
    def __str__(self):
        return "bassign: " + str(self.bvar) + ", " + str(self.right) 
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
class AST_return(AST_STM):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "return"
    def __str__(self):
        return "return"
class AST_pass(AST_STM):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "pass"
    def __str__(self):
        return "pass"

class AST_if(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def pycode(self):
        return "if %s:" % self.condition.pycode()
    def __str__(self):
        return "if: " + str(self.condition)
class AST_while(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def pycode(self):
        return "while %s:" % self.condition.pycode()
    def __str__(self):
        return "while: " + str(self.condition)
class AST_dowhile(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def pycode(self):
        return "dowhile %s:" % self.condition.pycode() # TODO: fix, this doesn't exist in python - maybe while True: ... if not conditon: break
    def __str__(self):
        return "dowhile: " + str(self.condition)

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
class AST_bvar(AST_BOOL):
    def __init__(self, varname: str):
        super().__init__()
        self.varname = varname
    def pycode(self):
        return self.varname
    def __str__(self):
        return "bvar: " + self.varname
class AST_true(AST_BOOL):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "True"
    def __str__(self):
        return "true"
class AST_false(AST_BOOL):
    def __init__(self):
        super().__init__()
    def pycode(self):
        return "False"
    def __str__(self):
        return "false"

class AST_or(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.left = left
        self.right = right
    def pycode(self):
        return "%s or %s" % (self.left.pycode(), self.right.pycode())
    def __str__(self):
        return "or: " + str(self.left) + ", " + str(self.right)
class AST_and(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.left = left
        self.right = right
    def pycode(self):
        return "%s and %s" % (self.left.pycode(), self.right.pycode())
    def __str__(self):
        return "and: " + str(self.left) + ", " + str(self.right)
class AST_not(AST_BOOLOP):
    def __init__(self, nott: AST_BOOL):
        super().__init__()
        self.right = nott
    def pycode(self):
        return "not %s" % (self.right.pycode(), )
    def __str__(self):
        return "not: " + str(self.right)


''' syntax tree operations '''


class AST_iterator:
    ''' Iterates through the graph in a sequential manor. '''
    def __init__(self, ast_root):
        if not type(ast_root) == AST_root:
            raise Exception("AST_iterator: must initialize using root")
        self.ast = ast_root
        self.stack = queue.LifoQueue(maxsize=10000) # some outrageously large maxsize here
    def next(self):
        if type(self.ast) == AST_root:
            self.ast = self.ast.block
            return self.ast
        
        # stack-based branched iteration doing block-first
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

