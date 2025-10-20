'''
Pseudocode generation, a helper utility tool.
'''

import queue
from simplegraph import *
from cogen import *


def pseudocode_from_simplegraph(enter_node, all_nodes):
    lines = flowchart_to_pseudocode(enter_node)
    pseudocode_make_expressions(lines, all_nodes)
    lw = LineWriter(lines)
    return lw.write()

def pseudocode_make_expressions(lines, allnodes):
    ''' For every line, insert text corresponding to the target data graph node subtree. '''
    for l in lines:
        # proc/term generated lines
        if type(l) in (LineStatement, ):
            if l.dgid is None:
                l.text = "/* " + l.node.label + " */"
                continue

            target = allnodes[l.dgid]
            if type(target) in (NodeObj, NodeObjTyped, ):
                l.text = dg_expr_assign(target)
            elif type(target) in (NodeMethod, NodeFunc):
                l.text = dg_expr_read(target)
            else:
                raise Exception("fc proc/term can only be associated with Obj, Func or Method dg nodes: %s" % target.name)
        # dec generated lines
        elif type(l) in (LineBranch, ):
            if l.dgid is None:
                l.text = "/* " + l.node.label + " */"
                continue

            target = allnodes[l.dgid]
            if type(target) in (NodeObj, NodeObjTyped, NodeFunc, NodeMethod, ):
                txt = dg_expr_read(target)
                l.setText(txt)
            else:
                raise Exception("fc dec can only be associated with Obj, Func or Method nodes: %s" % target.name)

class LineWriter:
    def __init__(self, lines, indent=4):
        self.ilines = lines
        self.lines = []
        self.indent_amount = indent
        self.indent_level = 0
    def write(self):
        a = self.indent_amount
        i = self.indent_level
        lineno = 1
        for l in self.ilines:
            if l.ilvl < 1:
                i = i + l.ilvl
            # indent and print line
            self.lines.append(str(lineno).ljust(4) + ''.ljust(i*a) + str(l))
            # postive: adjust indentation level after
            if l.ilvl >= 0:
                i = i + l.ilvl
            lineno = lineno + 1
        return '\n'.join(self.lines)

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

class LineReturn:
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

def flowchart_to_pseudocode(root):
    ''' flowchart to pseudocode graph iterator '''
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
    stack = queue.LifoQueue(maxsize=10000) # some outrageously large maxsize here
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
                    lines.append(LineReturn())
        if node == None:
            idx = idx + 1
            lines.append(LineClose())
            if stack.qsize() > 0:  # safe get no wait
                node = stack.get_nowait()
        idx = idx + 1

    # dg_expr_assign lineno to goto's
    for l in lines:
        if type(l) == LineGoto:
            l.lineno = vis[l.fcid] + 1 # LINES start at 1, indexes at zero

    return lines

