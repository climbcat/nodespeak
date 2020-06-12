'''
TODO: 
- build node graph from a frontend-generated graph def
- handle graph requirements: custom types (do we need special nodes/types to represent user typedefs or are node confs enough?)
- gen pseudocode / lines representation
- do goto-elimination
- gen code from goto-eliminated pseudocode (language specific)
- gen typedefs and stubs (language specific)
'''
from queue import LifoQueue
import inspect
from treealg import TreeJsonAddr, NodeConfig


'''
Cogen interface
'''
def cogen(graphdef, typetree):
    graph = FlatGraph(typetree)

    print("nodes:")
    nds = graphdef['nodes']
    for n in nds:
        print(n, nds[n])
    print("links:")
    lnks = graphdef['links']
    for l in lnks:
        print(l, lnks[l])
    
    graph.inject_graphdef(graphdef)

    # get a unique starting point or except
    term_Is = [n for n in list(graph.root.subnodes.values()) if type(n)==NodeTerm and n.child != None]
    if len(term_Is) != 1:
        raise Exception("flow control graph must have exactly one entry point")
    
    lines = flowchartToPseudocode(term_Is[0])
    
    makeLineExpressions(lines, graph.root.subnodes)

    lw = LineWriter(lines)
    text = lw.write()
    print(text)
    return text


'''
Flow chart to AST (syntax tree) generation.
'''
# tree building types with parent nodes
class AST_root: # ast global handle signaling enter/start
    def __init__(self):
        self.child
class AST_bassign: # statement: assignment to a boolean (only cogen'd)
    def __init__(self):
        self.parent
        self.child
        self.varname # bvar
        self.right # brval or bext
class AST_extern: # statement: external expression (dg subtree call)
    def __init__(self):
        self.parent
        self.child
        self.dgid
class AST_goto: # statement: goto label
    '''
    NOTE: the label will be handled by a list containing goto's and their labels,
    and a label dict pointing to the appropriate AST locations
    '''
    def __init__(self):
        self.parent # goto's are always a dead end
class AST_return: # statement: flow exit, implies generating a return/exit statement
    def __init__(self):
        self.parent
class AST_if:
    def __init__(self):
        self.parent
        self.child0 # false branch
        self.child1 # true branch
        self.condition # bvar, brval or bext
class AST_dowhile:
    def __init__(self):
        self.parent
        self.child0
        self.child1
        self.condition # bvar, brval or bext
# supporting types
class AST_bvar: # boolean value
    def __init__(self):
        self.parent
        self.varname
class AST_brval: # probably only true/false, of which we will only use true...
    # TODO: should we just use AST_true and AST_false instead?
    def __init__(self):
        self.parent
        self.valueexpr
class AST_bext: # external (dg) boolean value, not necessarily an rval
    def __init__(self):
        self.parent
        self.dgid
class AST_or:
    def __init__(self):
        self.parent
        self.left # bvar, brval, bext
        self.right # bvar, brval, bext
class AST_not:
    def __init__(self):
        self.parent
        self.right  # bvar, brval, bext

''' syntax tree operations '''
def AST_connect(p, c, branch=0):
    ''' connects a primary syntax tree node with a subnode '''
    if type(c) in (AST_root):
        raise Exception("AST_connect error: AST_root can have no parent")
    # c has a parent
    if type(p) in (AST_root, AST_bassign, AST_extern, AST_return, ):
        p.child = c
        c.parent = p
    elif type(p) in (AST_if, AST_dowhile, ):
        if branch==0:
            p.child0 = c
        else:
            p.child1 = c
        c.parent = p
    else:
        raise Exception("AST_connect error: %s, %s" % (str(p), str(c)))
_brval_types = (AST_bvar, AST_brval, AST_extern, AST_not, AST_or, )
def AST_leaf(p, c1, c2=None):
    ''' connects certain primary syntax tree nodes (bassign/if/dowhile) with leaf children '''
    if type(p) in (AST_bassign, ):
        if type(c1) in (AST_bvar, ) and type(c2) in _brval_types:
            p.varname = c1
            p.right = c2
            c1.parent = p
            c2.parent = p
        else: 
            raise Exception("AST_leaf: AST_bassign can leaf a pair of (AST_bvar, AST_bvar/AST_brval)")
    if type(p) in (AST_if, AST_dowhile, ) and c2 == None:
        if type(c1) in _brval_types:
            pass
        else:
            raise Exception("AST_leaf: AST_if/AST_dowhile can leaf a condition AST_bvar/AST_brval")
def AST_notleaf(p, c):
    if type(p) in (AST_not, ) and type(c) in _brval_types:
        p.right = c
        c.parent = p
    else:
        raise Exception("AST_notleaf: mismatch")
def AST_orleaf(p, c1, c2):
    if type(p) in (AST_or, ) and type(c) in _brval_types:
        p.left = c1
        p.right = c2
        c1.parent = p
        c2.parent = p
    else:
        raise Exception("AST_orleaf: mismatch")

def flowchartToSyntaxTree(root):
    ''' flowchart to syntax tree graph iterator '''
    # TODO: impl.
    '''
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
    ast = AST_root() # syntax tree building node
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
                retstm = LineReturnStatement(node)
                node = getSingleChild(node)
                if node ==None:
                    lines.append(retstm)
                else:
                    lines.append(stm)
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
    '''



'''
Flow chart to pseudocode generation. Pseudocode is a list of "line" objects which can be printed into actual pseudocode.
'''

def makeLineExpressions(lines, allnodes):
    '''
    For every line, inserts expression text corresponding to the target data graph node subtree execution pseudocode expression.
    '''
    def read(dgnode):
        ''' Returns an rvalue expression. dgnode: can be a obj, method or func '''
        if dgnode is None:
            return None
        if type(dgnode) in (ObjNode, ObjNodeTyped, ):
            varname = dgnode.get_varname()
            return varname
        subtree = build_dg_subtree(dgnode)
        return call_dg_subtree(subtree)
    def assign(obj_node):
        ''' returns an assignment expression to obj_node '''
        def getSingleParent(n):
            plst = _parents_get(n.parents)
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
        if type(l) in (LineStatement, LineReturnStatement, ):
            target = allnodes[l.dgid]
            if type(target) in (ObjNode, MethodNode, ):
                l.text = assign(target)
            elif type(target) in (MethodNode, ):
                l.text = read(target)
            else:
                raise Exception("fc proc/term can only be associated with Obj or Method dg nodes: %s" % target.name)
        # dec generated lines
        elif type(l) in (LineBranch, ):
            target = allnodes[l.dgid]
            if type(target) in (ObjNode, ObjNodeTyped, FuncNode, MethodNode, ):
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
    def __init__(self, node):
        self.dgid = node.dgid # target
        self.ilvl = 0
        self.text = None
    def __str__(self):
        s = self.dgid
        if self.dgid == None:
            s = "/* empty: */"
        if self.text != None:
            return "return " + self.text
        return s
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
                retstm = LineReturnStatement(node)
                node = getSingleChild(node)
                if node ==None:
                    lines.append(retstm)
                else:
                    lines.append(stm)
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


'''
Flow control graph model.

fcid: the global id of this flowchart item
dgid: the datagraph target global id
child: single child (PROC/TERM/DEC)
child0: "false" branch of dec node
child1: "true" branch of dec node
'''
def add_fc_node_child(n1, idx, n2):
    if type(n1) in (NodeDecision, ):
        n1.add_child(n2, idx)
    else:
        # TODO: this is where we need the node child safeguard on term_I nodes ...
        n1.child = n2
def set_fc_targetnode(fcnode, dgnode):
    fcnode.dgid = dgnode.name


class NodeProc:
    def __init__(self, fcid):
        self.fcid = fcid
        self.dgid = None
        self.child = None
class NodeTerm: # goes for both term_I and term_O ...
    def __init__(self, fcid):
        self.fcid = fcid
        self.dgid = None
        self.child = None
class NodeDecision:
    def __init__(self, fcid):
        self.fcid = fcid
        self.dgid = None
        self.child0 = None
        self.child1 = None
    def add_child(self, n, idx=None):
        if idx == 0:
            self.child0 = n
        elif idx == 1:
            self.child1 = n
        elif self.child0 is None:
            self.child0 = n
        elif self.child1 is None:
            self.child1 = n
        else:
            raise Exception("NodeDecision.add_child: slots 0 and 1 full")


'''
Graph assembly functionality, used by FlatGraph.
'''
def add_subnode(root, node, transitive=True):
    root.own(node)
    if transitive:
        node.subnode_to(root)

def remove_subnode(root, node):
    root.disown(node)
    node.unsubnode_from(root)

def add_connection(node1, idx1, node2, idx2):
    node1.add_child(node2, idx1)
    node2.add_parent(node1, idx2)

def remove_connection(node1, idx1, node2, idx2):
    node1.remove_child(node2, idx1)
    node2.remove_parent(node1, idx2)

def del_node(node):
    ''' disconnect a node and recursively disconnect all its subnodes '''
    for c in node.children:
        remove_connection(node, c)
    for p in node.parents:
        remove_connection(p, node)
    for s in node.subnodes:
        del_node(s)
    if node.owner:
        remove_subnode(node.owner, node)
''' TODO: A dict-based data structure should be faster. '''
def _child_put(lst, item, idx):
    lst.append((item, idx))
def _children_get(lst):
    srtd = sorted(lst, key=lambda i: i[1])
    return [l[0] for l in srtd]
def _child_rm(lst, item, idx):
    try:
        del lst[lst.index((item, idx))]
    except:
        raise Exception("_child_rm: item, idx(%s) not found in lst" % idx)
def _parent_put(lst, item, idx):
    idxs = [l[1] for l in lst]
    if idx in idxs:
        raise Exception('some item of idx "%s" already exists' % idx)
    lst.append((item, idx))
def _parents_get(lst):
    srtd = sorted(lst, key=lambda i: i[1])
    return [l[0] for l in srtd]
def _parent_rm(lst, item, idx):
    try:
        del lst[lst.index((item, idx))]
    except:
        raise Exception("_parent_rm: item, idx(%s) not found in lst" % idx)
def _child_or_parent_rm_allref(lst, item):
    todel = [l for l in lst if l[0]==item]
    for l in todel:
        del lst[lst.index(l)]


'''
Data graph model - imported from IFL and heavily modded.
'''
class NodeNotExecutableException(Exception): pass
class InternalExecutionException(Exception):
    def __init__(self, name, msg=None):
        self.name = name
        super().__init__(msg)
class GraphInconsistenceException(Exception): pass
class AbstractMethodException(Exception): pass

class Node:
    class RemoveParentIdxInconsistencyException(Exception): pass
    class RemoveChildIdxInconsistencyException(Exception): pass
    class NodeOfNameAlreadyExistsException(Exception): pass
    class NoNodeOfNameExistsException: pass
    def __init__(self, name, exe_model):
        self.name = name
        self.exe_model = exe_model

        self.children = []
        self.parents = []
        self.owners = []
        self.subnodes = {}

    def graph_inconsistent_fail(self, message):
        raise GraphInconsistenceException('(%s %s): %s' % (type(self).__name__, self.name, message))

    ''' Graph connectivity interface '''
    def add_child(self, node, idx):
        if node in [n for n in _children_get(self.children)]:
            raise Node.NodeOfNameAlreadyExistsException()
        if not self._check_child(node):
            self.graph_inconsistent_fail("illegal add_child")
        _child_put(self.children, node, idx)
    def remove_child(self, node, idx=None):
        if idx is None:
            _child_or_parent_rm_allref(self.children, node)
        else:
            _child_rm(self.children, node, idx)
    def num_children(self):
        # NOTE: we removed adding together "zero'th and first order" children, order has been removed 
        return len(_children_get(self.children))

    def add_parent(self, node, idx):
        if node in [n for n in _parents_get(self.parents)]:
            raise Node.NodeOfNameAlreadyExistsException()
        if not self._check_parent(node):
            self.graph_inconsistent_fail('illegal add_parent')
        _parent_put(self.parents, node, idx)
    def remove_parent(self, node, idx=None):
        if idx is None:
            _child_or_parent_rm_allref(self.parents, node)
        else:
            _parent_rm(self.parents, node, idx)
    def num_parents(self):
        return len(_parents_get(self.parents))

    def subnode_to(self, node):
        if not self._check_owner(node):
            self.graph_inconsistent_fail('illegal subnode_to')
        self.owners.append(node)
    def unsubnode_from(self, node):
        if node in self.owners:
            self.owners.remove(node)

    def own(self, node):
        if not self._check_subnode(node):
            self.graph_inconsistent_fail('illegal own')

        # a hack to make FC nodes work in here, but worth it
        key = None
        if (hasattr(node, "name")):
            key = node.name
        else:
            key = node.fcid
        if key not in self.subnodes.keys():
            self.subnodes[key] = node
        else:
            raise Node.NodeOfNameAlreadyExistsException()
    def disown(self, node):
        if node.name in self.subnodes.keys():
            del self.subnodes[node.name]
        else:
            raise Node.NoNodeOfNameExistsException()

    ''' Graph consistence. Implement to define conditions on graph consistency, throw a GraphInconsistenceException. '''
    def _check_subnode(self, node):
        pass
    def _check_owner(self, node):
        pass
    def _check_child(self, node):
        pass
    def _check_parent(self, node):
        pass

    ''' Subject/Object execution interface '''
    def assign(self, node):
        raise AbstractMethodException()
    def call(self, *args):
        raise AbstractMethodException()
    def get_object(self):
        raise AbstractMethodException()

    ''' Execution model interface '''
    def exemodel(self):
        return self.exe_model

class ExecutionModel():
    ''' Subclass to implement all methods. '''
    class CallAndAssignException(Exception): pass
    def can_assign(self):
        raise AbstractMethodException()
    def can_call(self):
        raise AbstractMethodException()
    def objects(self):
        raise AbstractMethodException()
    def subjects(self):
        raise AbstractMethodException()
    def check(self):
        if self.can_assign() and self.can_call():
            raise ExecutionModel.CallAndAssignException()

class RootNode(Node):
    ''' Used as a passive "owning" node. Can accept any child or parent as a sub-node. '''
    class ExeModel(ExecutionModel):
        ''' A model that does nothing. '''
        def can_assign(self):
            return False
        def can_call(self):
            return False
        def objects(self):
            return ()
        def subjects(self):
            return ()

    def __init__(self, name):
        super().__init__(name, exe_model=RootNode.ExeModel())
    def _check_subnode(self, node):
        return True
    def _check_owner(self, node):
        return True
    def _check_child(self, node):
        return False
    def _check_parent(self, node):
        return False

class ObjNode(Node):
    ''' General type-agnostic object handle. '''
    class CallException(Exception): pass
    class ExeModel(ExecutionModel):
        def can_assign(self):
            return True
        def can_call(self):
            return False
        def objects(self):
            return standard_objects
        def subjects(self):
            return standard_subjects

    def __init__(self, name, obj=None, label=None):
        self.obj = obj
        self.label = label
        super().__init__(name, exe_model=type(self).ExeModel())
    def __str__(self):
        return str(self.obj)
    def get_varname(self):
        if self.label != None:
            return self.label
        else:
            return self.name
    def assign(self, obj):
        self.obj = obj
        for m in [node for node in list(self.subnodes.values()) if type(node) is MethodNode]:
            m._check_owner(self)
    def call(self, *args):
        raise ObjNode.CallException()
    def get_object(self):
        return self.name # return varname, currently just .name, should be .label but that doesn't exist yet
        # TODO: rewrite !!!
        #return self.obj

    def _check_subnode(self, node):
        return type(node) is MethodNode
    def _check_owner(self, node):
        return type(node) is RootNode
    def _check_child(self, node):
        return type(node) in standard_children
    def _check_parent(self, node):
        return type(node) in standard_parents and len( _parents_get(self.parents) ) < 1

ObjNodeTyped = ObjNode
# TODO: implement to retain type info

class ObjLiteralNode(ObjNode):
    ''' Literal value handle '''
    class ExeModel(ExecutionModel):
        def can_assign(self):
            ''' This does not mean that you can't assign, but the execution function! '''
            return False
        def can_call(self):
            return False
        def objects(self):
            return [ObjLiteralNode]
        def subjects(self):
            return []
    def _check_parent(self, node):
        return False

class FuncNode(Node):
    ''' A named function, no direct execution allowed. '''
    class ExeModel(ExecutionModel):
        def can_assign(self):
            return False
        def can_call(self):
            return True
        def objects(self):
            return standard_objects
        def subjects(self):
            return standard_subjects
    def __init__(self, name, func):
        self.func = func
        super().__init__(name, exe_model=FuncNode.ExeModel())
    def __str__(self):
        return str(self.func)
    def assign(self, obj):
        pass
    def call(self, *args):
        return self.func + str(args).replace("'", "")
    def get_object(self):
        pass
    def _check_subnode(self, node):
        return False
    def _check_owner(self, node):
        return type(node) is RootNode
    def _check_child(self, node):
        return type(node) in standard_children
    def _check_parent(self, node):
        return type(node) in standard_parents and True

class MethodNode(Node):
    ''' Represents a method reference on some object, requires an ObjNode owner. '''
    class NoMethodOfThatNameException(InternalExecutionException): pass
    class AssignException(InternalExecutionException): pass
    class ExeModel(ExecutionModel):
        def can_assign(self):
            return False
        def can_call(self):
            return True
        def objects(self):
            return standard_objects
        def subjects(self):
            return standard_subjects

    def __init__(self, name, methodname):
        self.methodname = methodname
        super().__init__(name, exe_model=MethodNode.ExeModel())
    def __str__(self):
        return str(self.methodname)

    def assign(self, obj):
        pass
    def call(self, *args):
        owners = [o for o in self.owners if type(o) in (ObjNode, ObjNodeTyped, )]
        if len(owners) == 1:
            # TODO: use label when that is introduced
            owner_varname = owners[0].name
            return owner_varname + "." + self.methodname + str(args).replace("'", "")
        return self.methodname + str(args).replace("'", "")

    def _check_subnode(self, node):
        return False
    def _check_owner(self, node):
        return type(node) in (ObjNode, RootNode)
    def _check_child(self, node):
        return type(node) in standard_children and True
    def _check_parent(self, node):
        return type(node) in standard_parents and True

class ReturnFuncNode(Node):
    ''' Callable function supposed to return a bool or N_0 int. '''
    class AssignException(Exception): pass
    class ExeModel(ExecutionModel):
        def can_assign(self):
            return False
        def can_call(self):
            return True
        def objects(self):
            return standard_objects
        def subjects(self):
            return standard_subjects

    def __init__(self, name, func=None):
        self.func = func
        super().__init__(name, exe_model=ReturnFuncNode.ExeModel())
    def __str__(self):
        return str(self.func)

    def assign(self, obj):
        raise ReturnFuncNode.AssignException()
    def call(self, *args):
        if self.func:
            try:
                return self.func(*args)
            except Exception as e:
                raise InternalExecutionException(self.name, str(e))
        else:
            '''_not_none default behavior '''
            if len(args) > 0:
                return args[0] is not None
    def _check_subnode(self, node):
        return False
    def _check_owner(self, node):
        return type(node) is RootNode
    def _check_child(self, node):
        return False
    def _check_parent(self, node):
        return type(node) in standard_children and True

standard_children = (FuncNode, ObjNode, MethodNode, ReturnFuncNode)
standard_parents = (FuncNode, ObjNode, ObjLiteralNode, MethodNode)
standard_objects = (ObjNode, ObjLiteralNode)
standard_subjects = (FuncNode, MethodNode)


'''
Data graph subtree-expression builder/caller. Uses recursion to build or traverse the built product.
'''
def build_dg_subtree(root):
    '''
    Recursively builds a subtree from the directed graph given by root.
    '''
    def build_subtree_recurse(node, tree, model):
        subjs = model.subjects()
        objs = model.objects()
        for p in _parents_get(node.parents):
            if type(p) in subjs:
                tree.append(p)
                tree.append(build_subtree_recurse(p, [], model))
            elif type(p) in objs:
                tree.append(p)
        return tree

    model = root.exemodel()
    tree = build_subtree_recurse(root, [], model)
    # for "object calls" e.g. obj or "func as functional output"
    if model.can_assign():
        tree.insert(0, root)
        return tree
    # for "subject call" e.g. returnfunc
    elif model.can_call():
        return [None, root, tree]
    else:
        raise NodeNotExecutableException()


def call_dg_subtree(tree):
    '''
    Recursively calls nodes in a subtree, built by the build_subtree function.

    If the root (tree[0]) is not None, assignment to this node is carried out after call recursion.
    The result is always returned.

    Disregarding the tree root, a pair of elements, consisting of a subject node and a list (an arg-list)
    signals a call recursion. Elements in that list can be singular object nodes or pairs of a subject
    node and an arg-list. Note:
    - During call recursion, Object nodes in argument lists are replaced with their values.
    - During recursion, (Subject node, arg-list) pairs are recursively reduced to values. This evaluation
    begins at the end branches.
    '''
    def call_recurse(f, argtree):
        i = 0
        while i < len(argtree):
            if i + 1 < len(argtree) and type(argtree[i+1]) == list:
                f_rec = argtree[i]
                argtree_rec = argtree[i+1]
                value = call_recurse(f_rec, argtree_rec)
                del argtree[i]
                argtree[i] = value
            else:
                value = argtree[i].get_object()
                argtree[i] = value
            i += 1
        return f.call(*argtree)

    root = tree[0]
    del tree[0]

    result = None
    if len(tree) == 0:
        result = None
        if root is not None: root.assign(result)
    elif len(tree) == 1:
        result = tree[0].get_object()
        if root is not None: root.assign(result)
    else:
        func = tree[0]
        args = tree[1]
        result = call_recurse(func, args)
        if root: root.assign(result)
    return result


'''
Flatgraph flow-and-data graph representation. This is used to assemble and hold the server side
version of ui graph data. It enterprits ui data, structured as commands, and builds an identical
graph from that.
'''
def _log(msg):
    print(msg)
class FlatGraph:
    def __init__(self, tpe_tree):
        self.root = RootNode("root")
        self.tpe_tree = TreeJsonAddr(existing=tpe_tree)

        self.coords = None # should be reset with every execute syncset, and by inject_graphdef

        self.node_cmds_cache = {}
        self.dslinks_cache = {} # ds = downstream

    def _create_node(self, id, label, tpe_addr):
        '''
        id - node id
        tpe_addr - node type address
        '''
        conf = self.tpe_tree.retrieve(tpe_addr)
        n = None
        node_tpe = basetypes[conf['basetype']]

        # flowcontrol nodes
        if node_tpe == NodeTerm:
            n = NodeTerm(id)
        elif node_tpe == NodeProc:
            n = NodeProc(id)
        elif node_tpe == NodeDecision:
            n = NodeDecision(id)

        # datagraph nodes
        elif node_tpe == ObjNode:
            # TODO: somehow include type info derived from graph connectibility
            n = ObjNode(id, None, label)
        elif node_tpe == ObjNodeTyped:
            n = ObjNodeTyped(id, conf['type'], label)
        elif node_tpe == ObjLiteralNode:
            n = ObjLiteralNode(id, None)
        elif node_tpe == FuncNode:
            n = FuncNode(id, conf['type'])
        elif node_tpe == MethodNode:
            n = MethodNode(id, conf['type'])

        return n

    def node_add(self, x, y, id, name, label, tpe_addr):
        n = self._create_node(id, label, tpe_addr)
        _log('created node (%s) of type: "%s"' % (id, str(type(n))))
        if type(n) in (NodeTerm, NodeProc, NodeDecision, ):
            add_subnode(self.root, n, transitive=False) # this is a safe add not requiring a subnode_to member on ownee
        else:
            add_subnode(self.root, n)
        # caching
        # TODO: remove?
        self.node_cmds_cache[id] = (x, y, id, name, label, tpe_addr)

    def node_rm(self, id):
        # TODO: remove?
        n = self.root.subnodes.get(id, None)
        if not n:
            return
        
        obj = n.get_object()
        if obj != None:
            self.middleware.deregister(obj)
        
        if n.num_parents() != 0 or n.num_children() != 0:
            raise Exception("node_rm: can not remove node with existing links")
        remove_subnode(self.root, n)
        # caching
        # TODO: remove?
        del self.node_cmds_cache[id]
        _log("deleted node: %s" % id)

    def link_add(self, id1, idx1, id2, idx2):
        n1 = self.root.subnodes[id1]
        n2 = self.root.subnodes[id2]

        # "method links" are represented in the frontend as idx==-1, but as an owner/subnode relation in nodespeak
        if idx1 == -1 and idx2 == -1:
            if type(n1) == ObjNode and type(n2) == MethodNode:
                add_subnode(n1, n2)
            elif type(n1) == MethodNode and type(n2) == ObjNode:
                add_subnode(n2, n1)
            elif type(n1) in (NodeTerm, NodeProc, NodeDecision, ) and type(n2) in (ObjNode, ObjNodeTyped, ObjLiteralNode, FuncNode, ReturnFuncNode, ):
                set_fc_targetnode(n1, n2)
            elif type(n2) in (NodeTerm, NodeProc, NodeDecision, ) and type(n1) in (ObjNode, ObjNodeTyped, ObjLiteralNode, FuncNode, ReturnFuncNode, ):
                set_fc_targetnode(n2, n1)
        # all other connections
        else:
            if type(n1) in (NodeTerm, NodeProc, NodeDecision, ):
                add_fc_node_child(n1, idx1, n2)
            else:
                add_connection(n1, idx1, n2, idx2)

        # caching
        # TODO: remove?
        if not self.dslinks_cache.get(id1, None):
            self.dslinks_cache[id1] = []
        self.dslinks_cache[id1].append((id1, idx1, id2, idx2))

        _log("added link from (%s, %d) to (%s, %d)" % (id1, idx1, id2, idx2))

    def link_rm(self, id1, idx1, id2, idx2, order=0):
        # TODO: remove?
        n1 = self.root.subnodes[id1]
        n2 = self.root.subnodes[id2]
        
        # method links are represented in the frontend as idx==-1, but as an owner/subnode relation in nodespeak
        if type(n1) == ObjNode and type(n2) == MethodNode and idx1 == -1 and idx2 == -1:
            remove_subnode(n1, n2)
        elif type(n1) == MethodNode and type(n2) == ObjNode and idx1 == -1 and idx2 == -1:
            remove_subnode(n2, n1)
        # all other connections
        else:
            remove_connection(n1, idx1, n2, idx2, order)

        # caching
        # TODO: remove?
        lst = self.dslinks_cache[id1]
        idx = lst.index((id1, idx1, id2, idx2, order))
        del lst[idx]
        _log("removed link from (%s, %d) to (%s, %d)" % (id1, idx1, id2, idx2))

    def node_label(self, id, label):
        # TODO: remove?
        _log("node label update always ignored, (%s, %s)." % (id, label))
        # caching
        e = self.node_cmds_cache[id]
        self.node_cmds_cache[id] = (e[0], e[1], e[2], e[3], label, e[5])

    def graph_update(self, redo_lsts):
        # TODO: remove?
        ''' takes an undo-redo list and sequentially modifies the server-side graph '''
        _log('graph update: %d commands' % len(redo_lsts))
        error = None
        def erracc(msg, s):
            ''' message accumulation '''
            if s == None:
                s = msg
            else:
                s = s + ", " + msg

        for redo_molecule in redo_lsts:
            for redo in redo_molecule:
                cmd = redo[0]
                args = redo[1:]
                try:
                    getattr(self, cmd)(*args)
                except Exception as e:
                    _log('graph update failed, cmd "%s" with: %s' % (redo, str(e)), error=True)
                    erracc(str(e), error)

        if error != None:
            return {'error' : error}

    def graph_coords(self, coords):
        # TODO: remove?
        ''' updates the cached node_add commands x- and y-coordinate entries '''
        keys = coords.keys()
        for key in keys:
            coord = coords[key]
            cached_cmd = self.node_cmds_cache[key]
            self.node_cmds_cache[key] = (coord[0], coord[1], cached_cmd[2], cached_cmd[3], cached_cmd[4], cached_cmd[5])
        _log('graph coords: %d coordinate sets' % len(keys))

    def inject_graphdef(self, graphdef):
        ''' builds the graph from commands describing node and link adds '''
        nodes = graphdef['nodes']
        links = graphdef['links']

        for key in nodes.keys():
            cmd = nodes[key]
            print("label? ", cmd[4])
            self.node_add(cmd[0], cmd[1], cmd[2], cmd[3], cmd[4], cmd[5])

        for key in links.keys():
            for cmd in links[key]:
                self.link_add(cmd[0], cmd[1], cmd[2], cmd[3])

''' conversion table: json basetype string to server side node class equivalent '''
basetypes = {
    # nsgen datagraph basetypes
    'object' : ObjNode,
    'object_typed' : ObjNodeTyped,
    'object_literal' : ObjLiteralNode,
    'function_named' : FuncNode,
    'method' : MethodNode,

    # nsgen flowchart basetypes
    'term' : NodeTerm,
    'proc' : NodeProc,
    'dec' : NodeDecision,
}
