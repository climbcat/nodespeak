from django.core.management.base import BaseCommand
import json

from ns.models import GraphSession, TypeSchema

import cogen as cg
from simplegraph import TreeJsonAddr


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
                # get the json object
                tree = json.loads(s.data_str)

                text = cg.cogen_typedefs_py(tree)
                print(text)

            except Exception as e:
                raise e

