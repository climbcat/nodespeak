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

    subnodes = graph.root.subnodes
    return ast, gotos, labels, term_I, subnodes

def diagnose(gotos, lbls):
    print()
    print("# diagnostics:")

    for goto in gotos:
        lbl = lbls[goto]

        # test level, offset, indir, dir and sib
        glvl = cg.level(goto)
        llvl = cg.level(lbl)
        goff = cg.offset(goto)
        loff = cg.offset(lbl)
        irel = cg.indirectly_related(goto, lbl)
        drel = cg.directly_related(goto, lbl)
        sibs = cg.siblings(goto, lbl)
        
        # test inloop, inif
        ginloop = cg.is_in_loop(goto)
        ginif = cg.is_in_if(goto)
        linloop = cg.is_in_loop(lbl)
        linif = cg.is_in_if(lbl)
        sinstructure = ""
        if ginloop:
            sinstructure = sinstructure + ", goto in loop"
        elif ginif:
            sinstructure = sinstructure + ", goto in if"
        if linloop:
            sinstructure = sinstructure + ", lbl in loop"
        elif linif:
            sinstructure = sinstructure + ", lbl in if"
        
        print()
        print("%s -> %s%s" % (str(goto), str(lbl), sinstructure))
        print("goto level:  %s" % str(glvl))
        print("lbl level:   %s" % str(llvl))
        print("goto offset: %s" % str(goff))
        print("lbl offset:  %s" % str(loff))
        if irel:
            print("indirectly related")
        if drel:
            print("directly related")
        if sibs:
            print("siblings")


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
            ast, gotos, lbls, term_I, subnodes = load_ast(s)
            text_psc = cg.get_pseudocode(term_I, subnodes)
            text_ast = get_ast_text(ast)

            print()
            print("## session #%d:" % s.id)
            print()
            print(text_psc)
            print()
            print(text_ast)

            diagnose(gotos, lbls)

            # DEBUG
            cg.elimination_alg(gotos, lbls)

            print()
            print("## take two:")
            print()
            print(get_ast_text(ast))
            diagnose(gotos, lbls)

