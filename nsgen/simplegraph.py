'''
A simplified copy of the nodespeak graph engine.

Added: Flow chart node types, near the bottom. FlatGraph replaced by SimpleGraph, which can not be modified once created.
'''
from treealg import TreeJsonAddr


'''
DG model assembly.
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
def child_put(lst, item, idx):
    lst.append((item, idx))
def children_get(lst):
    srtd = sorted(lst, key=lambda i: i[1])
    return [l[0] for l in srtd]
def child_rm(lst, item, idx):
    try:
        del lst[lst.index((item, idx))]
    except:
        raise Exception("child_rm: item, idx(%s) not found in lst" % idx)
def parent_put(lst, item, idx):
    idxs = [l[1] for l in lst]
    if idx in idxs:
        raise Exception('some item of idx "%s" already exists' % idx)
    lst.append((item, idx))
def parents_get(lst):
    srtd = sorted(lst, key=lambda i: i[1])
    return [l[0] for l in srtd]
def parent_rm(lst, item, idx):
    try:
        del lst[lst.index((item, idx))]
    except:
        raise Exception("parent_rm: item, idx(%s) not found in lst" % idx)
def child_or_parent_rm_allref(lst, item):
    todel = [l for l in lst if l[0]==item]
    for l in todel:
        del lst[lst.index(l)]


'''
Data graph model - imported from IFL, then modded.
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
        if node in [n for n in children_get(self.children)]:
            raise Node.NodeOfNameAlreadyExistsException()
        if not self._check_child(node):
            self.graph_inconsistent_fail("illegal add_child")
        child_put(self.children, node, idx)
    def remove_child(self, node, idx=None):
        if idx is None:
            child_or_parent_rm_allref(self.children, node)
        else:
            child_rm(self.children, node, idx)
    def num_children(self):
        # NOTE: we removed adding together "zero'th and first order" children, order has been removed 
        return len(children_get(self.children))

    def add_parent(self, node, idx):
        if node in [n for n in parents_get(self.parents)]:
            raise Node.NodeOfNameAlreadyExistsException()
        if not self._check_parent(node):
            self.graph_inconsistent_fail('illegal add_parent')
        parent_put(self.parents, node, idx)
    def remove_parent(self, node, idx=None):
        if idx is None:
            child_or_parent_rm_allref(self.parents, node)
        else:
            parent_rm(self.parents, node, idx)
    def num_parents(self):
        return len(parents_get(self.parents))

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

class NodeRoot(Node):
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
        super().__init__(name, exe_model=NodeRoot.ExeModel())
    def _check_subnode(self, node):
        return True
    def _check_owner(self, node):
        return True
    def _check_child(self, node):
        return False
    def _check_parent(self, node):
        return False

class NodeObj(Node):
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
        for m in [node for node in list(self.subnodes.values()) if type(node) is NodeMethod]:
            m._check_owner(self)
    def call(self, *args):
        raise NodeObj.CallException()
    def get_object(self):
        return self.name # return varname, currently just .name, should be .label but that doesn't exist yet
        # TODO: rewrite!
        #return self.obj

    def _check_subnode(self, node):
        return type(node) is NodeMethod
    def _check_owner(self, node):
        return type(node) is NodeRoot
    def _check_child(self, node):
        return type(node) in standard_children
    def _check_parent(self, node):
        return type(node) in standard_parents and len( parents_get(self.parents) ) < 1

NodeObjTyped = NodeObj
# TODO: implement to retain type info

class NodeObjLiteral(NodeObj):
    ''' Literal value handle '''
    class ExeModel(ExecutionModel):
        def can_assign(self):
            ''' This does not mean that you can't assign, but the execution function! '''
            return False
        def can_call(self):
            return False
        def objects(self):
            return [NodeObjLiteral]
        def subjects(self):
            return []
    def _check_parent(self, node):
        return False

class NodeFunc(Node):
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
        super().__init__(name, exe_model=NodeFunc.ExeModel())
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
        return type(node) is NodeRoot
    def _check_child(self, node):
        return type(node) in standard_children
    def _check_parent(self, node):
        return type(node) in standard_parents and True

class NodeMethod(Node):
    ''' Represents a method reference on some object, requires an NodeObj owner. '''
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
        super().__init__(name, exe_model=NodeMethod.ExeModel())
    def __str__(self):
        return str(self.methodname)

    def assign(self, obj):
        pass
    def call(self, *args):
        owners = [o for o in self.owners if type(o) in (NodeObj, NodeObjTyped, )]
        if len(owners) == 1:
            # TODO: use label when that is introduced
            owner_varname = owners[0].name
            return owner_varname + "." + self.methodname + str(args).replace("'", "")
        return self.methodname + str(args).replace("'", "")

    def _check_subnode(self, node):
        return False
    def _check_owner(self, node):
        return type(node) in (NodeObj, NodeRoot)
    def _check_child(self, node):
        return type(node) in standard_children and True
    def _check_parent(self, node):
        return type(node) in standard_parents and True

class NodeReturnFunc(Node):
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
        super().__init__(name, exe_model=NodeReturnFunc.ExeModel())
    def __str__(self):
        return str(self.func)

    def assign(self, obj):
        raise NodeReturnFunc.AssignException()
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
        return type(node) is NodeRoot
    def _check_child(self, node):
        return False
    def _check_parent(self, node):
        return type(node) in standard_children and True

standard_children = (NodeFunc, NodeObj, NodeMethod, NodeReturnFunc)
standard_parents = (NodeFunc, NodeObj, NodeObjLiteral, NodeMethod)
standard_objects = (NodeObj, NodeObjLiteral)
standard_subjects = (NodeFunc, NodeMethod)


'''
FC graph assembly.

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
        self.label = None
class NodeTerm: # goes for both term_I and term_O ...
    def __init__(self, fcid):
        self.fcid = fcid
        self.dgid = None
        self.child = None
        self.label = None
class NodeDecision:
    def __init__(self, fcid):
        self.fcid = fcid
        self.dgid = None
        self.child0 = None
        self.child1 = None
        self.label = None
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
Data graph subtree-expression builder/caller. Uses recursion to build or traverse the built product.
'''
def build_dg_subtree(root):
    '''
    Recursively builds a subtree from the directed graph given by root.
    '''
    def build_subtree_recurse(node, tree, model):
        subjs = model.subjects()
        objs = model.objects()
        for p in parents_get(node.parents):
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


def _log(msg):
    print(msg)
'''
Simple one-off flow-chart and data-graph representation.
Can not be changed, is created once from a graph definition.
'''
class SimpleGraph:
    basetypes = {
        'object' : NodeObj,
        'object_typed' : NodeObjTyped,
        'object_literal' : NodeObjLiteral,
        'function_named' : NodeFunc,
        'method' : NodeMethod,
        'term' : NodeTerm,
        'proc' : NodeProc,
        'dec' : NodeDecision,
    }
    def __init__(self, tpe_tree, graphdef):
        self.root = NodeRoot("root")
        self.tpe_tree = TreeJsonAddr(existing=tpe_tree)
        self.dslinks_cache = {} # ds = downstream
        
        # build the graph from node- and link-add commands in graphdef
        nodes = graphdef['nodes']
        links = graphdef['links']

        for key in nodes.keys():
            cmd = nodes[key]
            self._node_add(cmd[0], cmd[1], cmd[2], cmd[3], cmd[4], cmd[5])

        for key in links.keys():
            for cmd in links[key]:
                self._link_add(cmd[0], cmd[1], cmd[2], cmd[3])


    def _create_node(self, id, label, tpe_addr):
        conf = self.tpe_tree.retrieve(tpe_addr)
        n = None
        node_tpe = SimpleGraph.basetypes[conf['basetype']]

        # flowcontrol nodes
        if node_tpe == NodeTerm:
            n = NodeTerm(id)
            n.label = label
        elif node_tpe == NodeProc:
            n = NodeProc(id)
            n.label = label
        elif node_tpe == NodeDecision:
            n = NodeDecision(id)
            n.label = label
        # datagraph nodes
        elif node_tpe == NodeObj:
            # TODO: somehow include type info derived from graph connectibility
            n = NodeObj(id, None, label)
        elif node_tpe == NodeObjTyped:
            n = NodeObjTyped(id, conf['type'], label)
        elif node_tpe == NodeObjLiteral:
            n = NodeObjLiteral(id, None)
        elif node_tpe == NodeFunc:
            n = NodeFunc(id, conf['type'])
        elif node_tpe == NodeMethod:
            n = NodeMethod(id, conf['type'])
        return n

    def _node_add(self, x, y, id, name, label, tpe_addr):
        if label == "":
            label = id
        n = self._create_node(id, label, tpe_addr)
        _log('created node (%s) of type: "%s"' % (id, str(type(n))))
        if type(n) in (NodeTerm, NodeProc, NodeDecision, ):
            add_subnode(self.root, n, transitive=False) # this is a safe add not requiring a subnode_to member on ownee
        else:
            add_subnode(self.root, n)

    def _link_add(self, id1, idx1, id2, idx2):
        n1 = self.root.subnodes[id1]
        n2 = self.root.subnodes[id2]

        # "method links" are represented in the frontend as idx==-1, but as an owner/subnode relation in nodespeak
        if idx1 == -1 and idx2 == -1:
            if type(n1) == NodeObj and type(n2) == NodeMethod:
                add_subnode(n1, n2)
            elif type(n1) == NodeMethod and type(n2) == NodeObj:
                add_subnode(n2, n1)
            elif type(n1) in (NodeTerm, NodeProc, NodeDecision, ) and type(n2) in (NodeObj, NodeObjTyped, NodeObjLiteral, NodeFunc, NodeReturnFunc, ):
                set_fc_targetnode(n1, n2)
            elif type(n2) in (NodeTerm, NodeProc, NodeDecision, ) and type(n1) in (NodeObj, NodeObjTyped, NodeObjLiteral, NodeFunc, NodeReturnFunc, ):
                set_fc_targetnode(n2, n1)
        # all other connections
        else:
            if type(n1) in (NodeTerm, NodeProc, NodeDecision, ):
                add_fc_node_child(n1, idx1, n2)
            else:
                add_connection(n1, idx1, n2, idx2)
        _log("added link from (%s, %d) to (%s, %d)" % (id1, idx1, id2, idx2))

