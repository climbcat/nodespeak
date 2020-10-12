from django.core.management.base import BaseCommand
import json
import traceback

from ns.models import GraphSession, TypeSchema

import cogen as cg
from cogen import *
import simplegraph
from simplegraph import *


def get_ast_text(ast):
    lines = []
    cg.treePrintRec(ast, lines)
    astrepr = '\n'.join(lines)
    return astrepr

def load_ast(s):
    # see cogen
    obj = json.loads(s.data_str)
    typetree = obj
    graphdef = obj["graphdef"]
    graph = simplegraph.SimpleGraph(typetree, graphdef)
    term_Is = [n for n in list(graph.root.subnodes.values()) if type(n)==simplegraph.NodeTerm and n.child != None]
    if len(term_Is) != 1:
        raise Exception("flow control graph must have exactly one entry point")
    term_I = term_Is[0]
    ast, gotos, labels = cg.flowchartToSyntaxTree(term_I)
    return ast, gotos, labels

def diagnose(s):
    ast, gotos, labels = load_ast(s)

    # TODO: do the diagnostics test


    return get_ast_text(ast)

class Command(BaseCommand):
    help = 'Test all available flow charts/graph sessions by loading them and running cogen.'
    def add_arguments(self, parser):
        parser.add_argument('sessionid', nargs='?', type=str, help='specify session to test')

    def handle(self, *args, **options):
        # session filter
        sessions = None
        if options["sessionid"]:
            sid = int(options["sessionid"][0])
            sessions = [GraphSession.objects.get(id=sid)]
        else:
            sessions = GraphSession.objects.all()

        # test and print
        for s in sessions:
            text = diagnose(s)

            print()
            print("session #%d:" % s.id)
            print()
            print(text)
