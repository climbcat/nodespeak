from django.core.management.base import BaseCommand
import json
from ns.models import GraphSession

import cogen as cg
from cogen import *
import simplegraph
from simplegraph import *
from ast import *

class AstDataObjects:
    def __init__(self):
        self.ast = None
        self.gotos = None
        self.labels = None
        self.term_start = None
        self.allnodes = None

def load_typetree(s):
    # see cogen
    obj = json.loads(s.data_str)
    typetree = obj
    graphdef = obj["graphdef"]
    graph = simplegraph.SimpleGraph(typetree, graphdef)

    # empty graphdef case
    if len(graph.root.subnodes.values()) == 0:
        raise Exception("empty graphdef case")

    term_Is = [n for n in list(graph.root.subnodes.values()) if type(n)==simplegraph.NodeTerm and n.child != None]
    if len(term_Is) != 1:
        raise Exception("flow control graph must have exactly one entry point")
    
    dbobj = AstDataObjects()
    dbobj.term_start = term_Is[0]
    dbobj.ast, dbobj.gotos, dbobj.labels = AST_from_flowchart(dbobj.term_start)
    dbobj.allnodes = graph.root.subnodes
    return dbobj

class Command(BaseCommand):
    help = ''
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
            print("\nTESTING AST_clone_tree on session #%s:" % s.id)

            info = load_typetree(s)            
            cloned_ast = AST_clone_tree(info.ast)

            # DB CHECK IT:
            print("\n[ORG]:")
            iter = AST_iterator(info.ast)
            node = iter.next()
            while node != None:
                print(node)
                node = iter.next()

            print("\n[CLN]:")
            iter = AST_iterator(cloned_ast)
            node = iter.next()
            while node != None:
                print(node)
                node = iter.next()

