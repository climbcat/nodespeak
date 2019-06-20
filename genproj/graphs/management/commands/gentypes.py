'''
Generates hard-coded node type configurations for NSGen flowcharts.
'''
from django.core.management.base import BaseCommand
import json
import os
import re
from collections import OrderedDict


class TreeJsonAddr:
    '''
    A local tree with "string addressing" where dots syntactically are delimiters between paths in
    the branching hierarchy.

    The tree is a "put-retrieve" tree with a "leaf" and a "branch" for every node, except root,
    which is considered a branch. Putting items into the root layer is indicated by the address "''",
    Within branches, nodes (an instance of the mentioned node, a {leaf, branch} dict), are keyed
    with get_key(item). The user must provide this, thus attaining full content flexibility.
    These keys in turn make up the address words.

    The tree will create any non-existing paths that are put, but not retrieved, in which case
    None is returned.
    '''
    def __init__(self, existing={}):
        self.root = existing

    def retrieve(self, address):
        root = self.root
        item = self._descend_recurse(root, address)['leaf']
        return item

    def put(self, path, item, getkey):
        root = self.root
        branch = root
        if path != '' and not path[0] == '.':
            branch = self._descend_recurse(root, path)['branch']
        key = getkey(item)
        self._get_or_create(branch, key)['leaf'] = item

    def _get_or_create(self, dct, key):
        if not dct.get(key, None):
            dct[key] = { 'leaf' : None, 'branch': {} }
        return dct[key]

    def _descend_recurse(self, branch, address):
        m = re.match('([^\.]+)\.(.*)', address)
        if address == '':
            raise Exception
        if m:
            key = m.group(1)
            address = m.group(2)
            branch = self._get_or_create(branch, key)['branch']
            return self._descend_recurse(branch, address)
        else:
            key = address
            return self._get_or_create(branch, key)

class NodeConfig:
    ''' will be converted to a json record, includes generative funtions for the "special" node confs '''
    def __init__(self):
        self.docstring = ''
        self.basetype = ''
        self.address = ''
        self.ipars = []
        self.type = ''
        self.itypes = []
        self.otypes = []
        self.name = ''
        self.label = ''

    def get_repr(self):
        if self.basetype == '':
            raise Exception("basetype not set")
        if self.type == '':
            raise Exception("type not set")

        dct = OrderedDict([
            ("basetype", self.basetype),
            ("type", self.type),
            ("address", self.address),
            ("ipars", self.ipars),
            ("itypes", self.itypes),
            ("otypes", self.otypes),
            ("name", self.name),
            ("label", self.label),
            ("docstring", self.docstring),
        ])
        return dct


def gen_flowchart_confs(tree, addrss, catgrs):
    '''
    NSGen specific flowchart conf types are generated here
    and added to the tree, addrss dicts.
    '''
    def get_key(conf):
        return conf['type']

    term_I = NodeConfig()
    term_I.docstring = "Terminal enter program/in."
    term_I.type = 'term_I'
    term_I.address = '.'.join(['flowchart', 'term_I'])
    term_I.basetype = 'term'
    term_I.ipars = ['']
    term_I.itypes = []
    term_I.otypes = ['flow']
    term_I.name = 'term_I'
    tree.put('flowchart', term_I.get_repr(), get_key)
    addrss.insert(1, term_I.address)

    term_O = NodeConfig()
    term_O.docstring = "Terminal exit program/out."
    term_O.type = 'term_O'
    term_O.address = '.'.join(['flowchart', 'term_O'])
    term_O.basetype = 'term'
    term_O.ipars = ['']
    term_O.itypes = ['flow']
    term_O.otypes = []
    term_O.name = 'term_O'
    tree.put('flowchart', term_O.get_repr(), get_key)
    addrss.insert(2, term_O.address)

    proc = NodeConfig()
    proc.docstring = "Process. One process, one data graph subtree call."
    proc.type = 'proc'
    proc.address = '.'.join(['flowchart', 'proc'])
    proc.basetype = 'proc'
    proc.ipars = ['']
    proc.itypes = ['flow']
    proc.otypes = ['flow']
    proc.name = 'proc'
    tree.put('flowchart', proc.get_repr(), get_key)
    addrss.insert(3, proc.address)

    dec = NodeConfig()
    dec.docstring = "Binary decision. Requires bool/int returning function or value."
    dec.type = 'dec'
    dec.address = '.'.join(['flowchart', 'dec'])
    dec.basetype = 'dec'
    # TODO: add ouput node "varname", we need "true" and "false" or similar here
    dec.ipars = ['']
    dec.itypes = ['flow']
    dec.otypes = ['flow', 'flow']
    dec.name = 'dec'
    tree.put('flowchart', dec.get_repr(), get_key)
    addrss.insert(4, dec.address)

    catgrs.append('flowchart')


    # sample data graph types for frontend testing

    func1 = NodeConfig()
    func1.docstring = "test function"
    func1.type = 'somefunction'
    func1.address = '.'.join(['datagraph', 'somefunction'])
    func1.basetype = 'function_named'
    func1.ipars = ['a', 'b']
    func1.itypes = ['int', 'int']
    func1.otypes = ['bool']
    func1.name = 'func1'
    func1.label = 'func1'
    tree.put('datagraph', func1.get_repr(), get_key)
    addrss.append(func1.address)

    func2 = NodeConfig()
    func2.docstring = "test function"
    func2.type = 'somefunction_2'
    func2.address = '.'.join(['datagraph', 'somefunction_2'])
    func2.basetype = 'function_named'
    func2.ipars = ['a', 'b', 'c']
    func2.itypes = ['string', 'int', 'bool']
    func2.otypes = ['bool']
    func2.name = 'func2'
    func2.label = 'func2'
    tree.put('datagraph', func2.get_repr(), get_key)
    addrss.append(func2.address)

    func3 = NodeConfig()
    func3.docstring = "test function"
    func3.type = 'somefunction_3'
    func3.address = '.'.join(['datagraph', 'somefunction_3'])
    func3.basetype = 'function_named'
    func3.ipars = ['d']
    func3.itypes = ['bool']
    func3.otypes = ['string']
    func3.name = 'func3'
    func3.label = 'func3'
    tree.put('datagraph', func3.get_repr(), get_key)
    addrss.append(func3.address)

    obj = NodeConfig()
    obj.docstring = "test object"
    obj.type = 'object'
    obj.address = '.'.join(['datagraph', 'object'])
    obj.basetype = 'object'
    obj.ipars = ['']
    obj.itypes = ['']
    obj.otypes = ['']
    obj.name = 'object'
    tree.put('datagraph', obj.get_repr(), get_key)
    addrss.append(obj.address)

    literal = NodeConfig()
    literal.docstring = "test literal"
    literal.type = 'literal'
    literal.address = '.'.join(['datagraph', 'literal'])
    literal.basetype = 'object_literal'
    literal.ipars = ['']
    literal.itypes = ['']
    literal.otypes = ['']
    literal.name = 'literal'
    tree.put('datagraph', literal.get_repr(), get_key)
    addrss.append(literal.address)

    method = NodeConfig()
    method.docstring = "test method"
    method.type = 'somemethod'
    method.address = '.'.join(['datagraph', 'somemethod'])
    method.basetype = 'method'
    method.ipars = ['']
    method.itypes = ['']
    method.otypes = []
    method.name = 'method'
    method.label = 'somemethod'
    tree.put('datagraph', method.get_repr(), get_key)
    addrss.append(method.address)

    catgrs.append('datagraph')
    


def save_nodetypes_js(mypath, tree, addrss, categories):
    text_categories = 'var categories = ' + json.dumps(categories, indent=2) + ';\n\n'
    text_addrss = 'var nodeAddresses = ' + json.dumps(addrss, indent=2) + ';\n\n'
    text = 'var nodeTypes = ' + json.dumps(tree.root, indent=2) + ';\n\n'

    fle = open(os.path.join(mypath, "nodetypes.js"), 'w')
    fle.write(text_categories + text_addrss + text)
    fle.close()


class Command(BaseCommand):
    help = 'Generates node type configurations from a python module.'

    def handle(self, *args, **options):
        typetree = TreeJsonAddr()
        addresses = []
        categories = []
        gen_flowchart_confs(typetree, addresses, categories)

        # TODO: add custom node types from tpeedt
        # 
        # NOTE: We need to devise a system that keeps the type menu updated with rapid
        # edits to datagraph node types from the tpeedt module/app. Name changes etc.
        # should perhaps be tracked meticulously so as to be able to applyatomic
        # changes to the graph def.
        # Right now for testing purposes, we simply assume that types can be used as is.

        print("writing nodetypes.js...")
        save_nodetypes_js('graphs/static/graphs', typetree, addresses, categories)

