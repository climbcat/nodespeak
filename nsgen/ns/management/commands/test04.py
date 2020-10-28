from django.core.management.base import BaseCommand
import json
import traceback

from ns.models import GraphSession, TypeSchema

import cogen as cg
from cogen import *
import simplegraph
from simplegraph import *

def load_ast(s):
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
    term_I = term_Is[0]
    ast, gotos, labels = cg.flowchartToSyntaxTree(term_I)

    allnodes = graph.root.subnodes
    return ast, gotos, labels, term_I, allnodes

class Command(BaseCommand):
    help = 'Test all available flow charts/graph sessions by loading them and running cogen.'
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
                ast, gotos, lbls, term_I, allnodes = load_ast(s)
            except:
                # empty graphdef case
                print("\n\n## session #%d: empty graphdef \n" % s.id)
                continue

            text_pseudocode = cg.get_pseudocode(term_I, allnodes)
            cg.elimination_alg(gotos, lbls, ast)
            text_ast = cg.get_ast_text(ast)
            text_pycode = cg.get_pycode(ast, allnodes)

            print()
            print()
            print("## session #%d:" % s.id)
            print()
            print(text_pseudocode)
            print()
            print(text_ast)
            print()
            print(text_pycode)

