from django.core.management.base import BaseCommand
import json
import traceback

from ns.models import GraphSession, TypeSchema

import cogen as cg
from cogen import *
import simplegraph
from simplegraph import *
from ast import AST_root


class AstDataObjects:
    def __init__(self):
        self.ast = None
        self.gotos = None
        self.labels = None
        self.term_start = None
        self.allnodes = None

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

    info_obj = AstDataObjects()
    info_obj.term_start = term_Is[0]
    info_obj.ast, info_obj.gotos, info_obj.labels = cg.AST_from_flowchart(info_obj.term_start)
    info_obj.allnodes = graph.root.subnodes
    return info_obj

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
                info = load_ast(s)
            except:
                # empty graphdef case
                print("\n\n## session #%d: empty graphdef \n" % s.id)
                continue

            print()
            print()
            print("## session #%d:" % s.id)

            # pseudocode
            #text_pseudocode = cg.pseudocode_from_simplegraph(info.term_start, info.allnodes)

            log_evolution = cg.goto_elimination_alg(info.gotos, info.labels, info.ast, info.allnodes)

            msg, ast_next = log_evolution.next()
            while ast_next is not None:
                if type(ast_next) is not AST_root:
                    raise Exception("not root")

                print(msg)

                AST_make_expressions(ast_next, info.allnodes)

                text_pycode = cg.AST_write_pycode(ast_next)
                print()
                print(text_pycode)
                print()
                print()

                #text_ast = cg.AST_to_text(ast_next)
                #print()
                #print(text_ast)

                msg, ast_next = log_evolution.next()

