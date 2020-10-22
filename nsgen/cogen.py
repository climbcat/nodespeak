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
import simplegraph


''' Interface '''


def cogen(graphdef, typetree, DB_logging=False):
    if DB_logging == True:
        simplegraph.g_logmode = 1

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
    ast, gotos, labels = flowchartToSyntaxTree(term_I)

    lines = []
    treePrintRec(ast, lines)
    astrepr = '\n'.join(lines)

    # return data
    return pscode + '\n' + astrepr

def get_pseudocode(enter_node, all_nodes):
    lines = flowchartToPseudocode(enter_node)
    makeLineExpressions(lines, all_nodes)
    lw = LineWriter(lines)
    return lw.write()


''' syntax tree types '''


class AST_root:
    def __init__(self):
        self.block = None
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
    def __str__(self):
        return "bassign: " + str(self.bvar) + ", " + str(self.right) 
class AST_extern(AST_STM):
    def __init__(self, dgid: str):
        super().__init__()
        self.dgid = dgid
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
    def __str__(self):
        return "ifgoto %d: " % self.index + str(self.ifcond) + " -> " + self.label
class AST_return(AST_STM):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "return"
class AST_pass(AST_STM):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "pass"


class AST_if(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def __str__(self):
        return "if: " + str(self.condition)
class AST_while(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def __str__(self):
        return "while: " + str(self.condition)
class AST_dowhile(AST_FORK):
    def __init__(self, condition: AST_BOOL):
        super().__init__(condition)
    def __str__(self):
        return "dowhile: " + str(self.condition)

class AST_bextern(AST_BOOL):
    def __init__(self, dgid: str):
        if dgid == None: # when the dec is not connected
            raise Exception("AST_bextern: Decision nodes must have a target bvar or bfunc, to be used for creating this")
        super().__init__()
        self.dgid = dgid
    def __str__(self):
        return "bexternal: " + self.dgid
class AST_bvar(AST_BOOL):
    def __init__(self, varname: str):
        super().__init__()
        self.varname = varname
    def __str__(self):
        return "bvar: " + self.varname
class AST_true(AST_BOOL):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "true"
class AST_false(AST_BOOL):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "false"

class AST_or(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.left = left
        self.right = right
    def __str__(self):
        return "or: " + str(self.left) + ", " + str(self.right)
class AST_and(AST_BOOLOP):
    def __init__(self, left: AST_BOOL, right: AST_BOOL):
        super().__init__()
        self.left = left
        self.right = right
    def __str__(self):
        return "and: " + str(self.left) + ", " + str(self.right)
class AST_not(AST_BOOLOP):
    def __init__(self, nott: AST_BOOL):
        super().__init__()
        self.right = nott
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

    # assign an index to each goto to ease debugging
    gidx = 0
    for g in gotos:
        g.index = gidx
        gidx = gidx + 1

    # done
    return astroot, gotos, labels


# NOTE: untested
def elimination_alg(gotos, lbls):

    # select goto/lbl pair
    for goto in gotos:
        lbl = lbls[goto]

        while indirectly_related(goto, lbl):
            move_out_of_loop_or_if(goto)

        while directly_related(goto, lbl):
            if level(goto) > level(lbl):
                move_out_of_loop_or_if(goto)
            else:
                
                # TODO: now impl. and test dir rel with l(g) > l(l)...
                
                lblstm = find_directly_related_lblstm(goto, lbl)
                if offset(goto) > offset(lblstm):
                    lift_above_lblstm(goto, lblstm)
                else:
                    move_into_loop_or_if(goto)

        if siblings(goto, lbl):
            if offset(goto) < offset(lbl):
                eliminate_by_cond(goto, lbl)
            else:
                eliminate_by_while(goto, lbl)
        else:
            raise Exception("elimination fail")

# NOTE: untested
def find_directly_related_lblstm(goto, lbl) -> AST_STM:
    ''' assumnes level(goto) < level(lbl) and directly related '''
    lvldiff = level(lbl) - level(goto)
    node = lbl
    if lvldiff < 0:
        raise Exception("find_lblstm fail: l(g) must be < l(l)")
    while lvldiff > 0:
        while node.prev != None and node.up == None:
            node = node.prev
        if node.up != None:
            node = node.up
            lvldiff = lvldiff -1
        if lvldiff == 0 and issubclass(type(node), AST_FORK):
            return node
    raise Exception("find_directly_related_lblstm: find_lblstm fail: did not converge, are goto and lbl directly related?")

def indirectly_related(goto, lbl) -> bool:
    if siblings(goto, lbl):
        return False
    elif directly_related(goto, lbl):
        return False
    else:
        return True
def directly_related(goto, lbl) -> bool:
    lvlgoto = level(goto)
    lvllbl = level(lbl)
    if lvlgoto == lvllbl:
        # must be siblings or indirectly related
        return False
    else:
        # can be directly or indirectly related
        n1 = goto
        n2 = lbl
        goto_parents = []
        common_parent = None

        # map all nodes above goto, return if lbl is encountered
        while type(n1) != AST_root:
            if n1.prev != None:
                n1 = n1.prev
            elif n1.up != None:
                n1 = n1.up
            if n1 == lbl:
                return True
            goto_parents.append(n1)

        # search above lbl for any marked, return if goto is encountered
        while common_parent == None:
            if n2.prev != None:
                n2 = n2.prev
            elif n2.up != None:
                n2 = n2.up
            if n2 == goto:
                return True
            elif n2 in goto_parents:
                common_parent = n2

        # common parent must be on level with goto or lbl
        lvlcommon = level(common_parent)
        if lvlcommon == lvlgoto or lvlcommon == lvllbl:
            return True
        else:
            return False
def siblings(goto, lbl) -> bool:
    ogoto = offset(goto)
    olbl = offset(lbl)
    node = None
    node2 = None
    if ogoto < olbl:
        node = lbl
        node2 = goto
    else:
        node = goto
        node2 = lbl

    while node != node2:
        if node.prev != None:
            node = node.prev
        else:
            return False
    return True

def level(node) -> int:
    lvl = -1
    while type(node) != AST_root:
        while node.prev != None:
            node = node.prev
        if node.up != None: # node.up could be root, since this is how root is attached
            lvl = lvl + 1
            node = node.up
    return lvl
def offset(node) -> int:
    ''' returns the offset/index within the current block '''
    offset = 0
    while node.prev != None:
        node = node.prev
        offset = offset + 1
    return offset
def is_in_loop(node) -> bool:
    ''' is node in the block of a while or dowhile '''
    while node.prev != None:
        node = node.prev
    if node.up == None:
        raise Exception("is_in_loop: node.up xor node.prev must be set")
    if type(node.up) in (AST_while, AST_dowhile):
        return True
    else:
        return False
def is_in_if(node) -> bool:
    ''' is node in the block of an if '''
    while node.prev != None:
        node = node.prev
    if node.up == None:
        raise Exception("is_in_if: node.up xor node.prev must be set")
    if type(node.up) == AST_if:
        return True
    else:
        return False

gotovar_idx = -1 # all "bassign goto_N" need a globally unique tag/name, we can use this index 
def move_out_of_loop_or_if(goto):
    global gotovar_idx
    gotovar_idx = gotovar_idx + 1

    # map goto context
    node = goto
    loop = None
    while node.prev != None:
        node = node.prev
    if node.up:
        loop = node.up # the while, dowhile or if containing the goto
    else:
        raise Exception("move_out_of_loop_or_if: loop/if not found")
    stm_after_goto = goto.next
    stm_before_goto = goto.prev

    # create replacing nodes
    bvar = AST_bvar("goto_%s" % gotovar_idx)
    bass = AST_bassign(bvar, goto.ifcond)
    if_replacing_goto = AST_if(AST_not(bvar))

    # extract and redefine the goto
    _remove(goto)
    goto.ifcond = bvar

    # re-insert the goto after the loop/if
    _insert_after(goto, loop)

    # repair the hole where the goto was
    if stm_after_goto != None:
        # there is some statement after the goto
        _insert_before(bass, stm_after_goto)
        _insert_loop_or_if_above(stm_after_goto, if_replacing_goto)
    elif stm_before_goto:
        # NOTE: untested
        # the goto was the last statement in a non-trivial block (thus we don't need if_replacing_goto)
        _insert_after(bass, stm_before_goto)
    else:
        # NOTE: untested
        # the block consists of the goto and nothing else, the situation calls for a full simplification
        goto.condition = AST_and(goto.ifcond, loop.condition)
        _remove(loop)

# NOTE: untested
def eliminate_by_cond(goto, lbl): pass # when o(g) < o(l)
# NOTE: untested
def eliminate_by_while(goto, lbl): pass # when o(g) > o(l)
# NOTE: untested
def move_into_loop_or_if(goto, loopstm): pass
# NOTE: untested
def lift_above_lblstm(goto, lblstm): pass

# NOTE: untested
def _remove(node):
    if node.prev:
        if node.next:
            node.next.prev = node.prev
            node.prev.next = node.next
        else:
            node.prev.next = None
    elif node.up:
        if node.next:
            node.up.block = node.next
            node.next.prev = None
            node.next.up = node.up
        else:
            node.up.block = AST_pass()
    else:
        raise Exception("_remove assert: (node.up xor node.prev) must be tru3")
def _insert_loop_or_if_above(node, loop):
    # set prev.next to be the loop
    if node.prev != None:
        node.prev.next = loop
    # set node and loop relations
    node.prev = None
    node.up = loop
    loop.block = node
def _insert_after(node, after):
    # set next.prev to node
    if after.next != None:
        after.next.prev = node
    # set next to node
    after.next = node
def _insert_before(node, before):
    # set prev.next to node
    if before.prev != None:
        before.prev.next = node
    # set prev to node
    before.prev = node
    # reset up from before to node
    if before.up != None:
        node.up = before.up
        before.up = None


''' flow chart to pseudocode '''


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
            elif type(target) in (NodeMethod, NodeFunc):
                l.text = read(target)
            else:
                raise Exception("fc proc/term can only be associated with Obj, Func or Method dg nodes: %s" % target.name)
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

