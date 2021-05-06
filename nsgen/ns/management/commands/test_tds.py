from django.core.management.base import BaseCommand
import json

from ns.models import GraphSession, TypeSchema

import cogen as cg
from cogen import *
from simplegraph import TreeJsonAddr


class UserType:
    def __init__(self, tpe, basetype, ipars, itypes, otypes, label):
        self.tpe = tpe
        self.basetype = basetype
        self.ipars = ipars
        self.itypes = itypes
        self.otypes = otypes
        self.label = label
        self.method = []

    def __str__(self):
        if self.basetype == "function_named":
            return "def %s(%s):\n    pass" % (self.tpe, ", ".join(self.ipars))

        elif self.basetype == "object_typed":
            # we should not do this when generating Python code
            return "# %s - typedefs not generated for Python" % self.tpe

        elif self.basetype == "constructor":
            if len(self.ipars) > 0:
                lst = []
                lst.append("class %s(%s):" % (self.tpe, ", ".join(self.ipars)))
                lst.append("    def __init__(self, %s):" % (", ".join(self.ipars)))
                lst.append("        pass")

                return "\n".join(lst)
            else:
                return "class %s:\n    pass" % self.tpe

        elif self.basetype == "method":
            if len(self.ipars) > 0:
                lst = []
                lst.append("    def %s(self, %s):" % (self.tpe, ", ".join(self.ipars)))
                lst.append("        pass")

                return "\n".join(lst)
            else:
                return "    def %s(self):\n        pass" % self.tpe

        else:
            return self.basetype + " - " + self.tpe

def load_typetree(s):
    # get the json object
    obj = json.loads(s.data_str)
    
    # load user types subtree
    tree = TreeJsonAddr(obj["user"]["branch"]["custom"]["branch"])
    user_addr = list(obj["user"]["branch"]["custom"]["branch"].keys()) 

    user_tpes = []
    user_methods = {}
    for addr in user_addr:
        localobj = tree.retrieve(addr)

        user_tpe = UserType(
            tpe = localobj["type"],
            basetype = localobj["basetype"],
            ipars = localobj["ipars"],
            itypes = localobj["itypes"],
            otypes = localobj["otypes"],
            label = localobj["label"])

        user_tpes.append(user_tpe)

        # get the methods from this branch
        if user_tpe.basetype == "constructor":

            branch = obj["user"]["branch"]["custom"]["branch"][user_tpe.tpe]["branch"]
            user_methods[user_tpe.tpe] = []
            for a in branch.keys():

                method_obj = tree.retrieve(addr + "." + a)

                user_mthod = UserType(
                    tpe = method_obj["type"],
                    basetype = method_obj["basetype"],
                    ipars = method_obj["ipars"],
                    itypes = method_obj["itypes"],
                    otypes = method_obj["otypes"],
                    label = method_obj["label"])

                user_methods[user_tpe.tpe].append(user_mthod)


    # print typedefs (should not be in pythonic cogen?)
    for user_tpe in user_tpes:
        if user_tpe.basetype != "object_typed":
            continue
        print(user_tpe)
        print()

    # print classes
    for user_tpe in user_tpes:
        if user_tpe.basetype != "constructor":
            continue
        print(user_tpe)

        # print its methods
        for method_tpe in user_methods[user_tpe.tpe]:
            print(method_tpe)

    # print function_named
    for user_tpe in user_tpes:
        if user_tpe.basetype != "function_named":
            continue
        print()
        print(user_tpe)

    return None


class Command(BaseCommand):
    help = 'Test typetree load and code generation, which supplements the fc/dg code generation.'
    def add_arguments(self, parser):
        parser.add_argument('sessionid', nargs='?', type=str, help='specify session to test')

    def handle(self, *args, **options):

        # session filter
        sessions = None
        if options["sessionid"]:
            sid = int(options["sessionid"])
            sessions = [GraphSession.objects.get(id=sid)]
        else:
            sessions = GraphSession.objects.all()

        # test and print
        for s in sessions:
            try:
                info = load_typetree(s)
            except Exception as e:
                raise e
                ## empty graphdef case
                #print("\n\n## session #%d: empty graphdef \n" % s.id)
                #continue

