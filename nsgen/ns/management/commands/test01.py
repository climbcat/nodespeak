from django.core.management.base import BaseCommand
import json
import traceback

from cogen import cogen
from ns.models import GraphSession, TypeSchema

def test_session(s) -> str:
    obj = json.loads(s.data_str)
    try:
        text = cogen(obj["graphdef"], obj, DB_logging=False)
    except Exception as e:
        text = traceback.format_exc()
    return text

class Command(BaseCommand):
    help = 'Test all available flow charts/graph sessions by loading them and running cogen.'
    def add_arguments(self, parser):
        parser.add_argument('sessionid', nargs='?', type=str, help='specify session to test')
        parser.add_argument('--list', action='store_true', help='list sessions')

    def handle(self, *args, **options):
        # list sessions
        if options["list"]:
            sessions = GraphSession.objects.all()
            for s in sessions:
                print(s.id)
            quit()

        # session filter
        sessions = None
        if options["sessionid"]:
            sid = int(options["sessionid"][0])
            sessions = [GraphSession.objects.get(id=sid)]
        else:
            sessions = GraphSession.objects.all()

        # test and print
        for s in sessions:
            text = test_session(s)

            print()
            print()
            print("session #%d:" % s.id)
            print()
            print(text)
