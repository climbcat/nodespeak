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
    ''' json compatible node type config schema '''
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

