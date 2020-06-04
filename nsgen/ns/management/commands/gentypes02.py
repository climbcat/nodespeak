'''
Generates hard-coded node type configurations for NSGen flowcharts.
'''
from django.core.management.base import BaseCommand
import json

from treealg import TreeJsonAddr, NodeConfig
from ns.models import TypeSchema


def get_key(conf):
    ''' provided for TreeJsonAddr '''
    return conf['type']


def gen_static_branch(tree, address):
    flowaddr = []
    dgaddr = []
    
    # fill out static flowchart branch
    term_I = NodeConfig()
    term_I.docstring = "Terminal enter program/in."
    term_I.type = 'term_I'
    term_I.address = '.'.join(['static', 'flowchart', 'term_I'])
    term_I.basetype = 'term'
    term_I.ipars = ['']
    term_I.itypes = []
    term_I.otypes = ['flow']
    term_I.name = 'term_I'
    tree.put('static.flowchart', term_I.get_repr(), get_key)
    address.insert(1, term_I.address)
    flowaddr.insert(1, term_I.address)

    term_O = NodeConfig()
    term_O.docstring = "Terminal exit program/out."
    term_O.type = 'term_O'
    term_O.address = '.'.join(['static', 'flowchart', 'term_O'])
    term_O.basetype = 'term'
    term_O.ipars = ['']
    term_O.itypes = ['flow']
    term_O.otypes = []
    term_O.name = 'term_O'
    tree.put('static.flowchart', term_O.get_repr(), get_key)
    address.insert(2, term_O.address)
    flowaddr.insert(2, term_O.address)

    proc = NodeConfig()
    proc.docstring = "Process. One process, one data graph subtree call."
    proc.type = 'proc'
    proc.address = '.'.join(['static', 'flowchart', 'proc'])
    proc.basetype = 'proc'
    proc.ipars = ['']
    proc.itypes = ['flow']
    proc.otypes = ['flow']
    proc.name = 'proc'
    tree.put('static.flowchart', proc.get_repr(), get_key)
    address.insert(3, proc.address)
    flowaddr.insert(3, proc.address)

    dec = NodeConfig()
    dec.docstring = "Binary decision. Requires bool/int returning function or value."
    dec.type = 'dec'
    dec.address = '.'.join(['static', 'flowchart', 'dec'])
    dec.basetype = 'dec'
    # TODO: add ouput node "varname", we need "true" and "false" or similar here
    dec.ipars = ['']
    dec.itypes = ['flow']
    dec.otypes = ['flow', 'flow']
    dec.name = 'dec'
    tree.put('static.flowchart', dec.get_repr(), get_key)
    address.insert(4, dec.address)
    flowaddr.insert(4, dec.address)

    # fill out static datagraph branch
    obj = NodeConfig()
    obj.docstring = "object handle"
    obj.type = 'object'
    obj.address = '.'.join(['static', 'datagraph', 'object'])
    obj.basetype = 'object'
    obj.ipars = ['']
    obj.itypes = ['']
    obj.otypes = ['']
    obj.name = 'object'
    tree.put('static.datagraph', obj.get_repr(), get_key)
    address.append(obj.address)
    dgaddr.append(obj.address)

    literal = NodeConfig()
    literal.docstring = "input value handle"
    literal.type = 'literal'
    literal.address = '.'.join(['static', 'datagraph', 'literal'])
    literal.basetype = 'object_literal'
    literal.ipars = ['']
    literal.itypes = ['']
    literal.otypes = ['']
    literal.name = 'literal'
    tree.put('static.datagraph', literal.get_repr(), get_key)
    address.append(literal.address)
    dgaddr.append(literal.address)

    return flowaddr, dgaddr


def gen_user_branch(tree, address):
    biaddr = []
    customaddr = []

    obj = NodeConfig()
    obj.docstring = "built-in bool"
    obj.type = 'bool'
    obj.address = 'user.builtin.bool'
    # TODO: how do we handle nodes of simple types?
    obj.basetype = 'object_typed'
    obj.ipars = ['']
    obj.itypes = ['']
    obj.otypes = ['']
    obj.name = 'bool'
    obj.label = 'bool'
    tree.put('user.builtin', obj.get_repr(), get_key)
    address.append(obj.address)
    biaddr.append(obj.address)

    # user built-in branch
    obj = NodeConfig()
    obj.docstring = "built-in int"
    obj.type = 'int'
    obj.address = 'user.builtin.int'
    obj.basetype = 'object_typed'
    obj.ipars = ['']
    obj.itypes = ['']
    obj.otypes = ['']
    obj.name = 'int'
    obj.label = 'int'
    tree.put('user.builtin', obj.get_repr(), get_key)
    address.append(obj.address)
    biaddr.append(obj.address)

    # user built-in branch
    obj = NodeConfig()
    obj.docstring = "built-in string"
    obj.type = 'string'
    obj.address = 'user.builtin.string'
    obj.basetype = 'object_typed'
    obj.ipars = ['']
    obj.itypes = ['']
    obj.otypes = ['']
    obj.name = 'string'
    obj.label = 'string'
    tree.put('user.builtin', obj.get_repr(), get_key)
    address.append(obj.address)
    biaddr.append(obj.address)

    return biaddr, customaddr

def create_typeschema_todb(dct):
    ts = TypeSchema()
    ts.data_str = json.dumps(dct)
    ts.version = "gentypes01"
    ts.save()
    print("saved typeschema to db with id=%s..." % str(ts.id))


class Command(BaseCommand):
    help = 'Generates node type configurations from a python module.'

    def handle(self, *args, **options):
        typetree = TreeJsonAddr()

        # add the (empty) graphdef
        graphdef = {}
        typetree.root['graphdef'] = graphdef

        # node types - using tree.put
        addresses = [] # tree location/address accumulation list (TODO: create a tree iterator instead of this clunkiness)
        fcaddr, dgaddr = gen_static_branch(typetree, addresses)
        biaddr, customaddr = gen_user_branch(typetree, addresses)
        typetree.root['addresses'] = addresses

        # non-node type data using standard json (node-containing branch becomes grapical menu)
        menus = {}
        menus['FLOWCHART'] = fcaddr
        menus['DATAGRAPH'] = dgaddr
        menus['BUILTIN'] = biaddr
        menus['CUSTOM'] = customaddr
        typetree.root['menus'] = menus

        create_typeschema_todb(typetree.root)

