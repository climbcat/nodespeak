from django.core.management.base import BaseCommand

from ns.models import GraphSession, TypeSchema


class Command(BaseCommand):
    help = 'Test all available flow charts/graph sessions by loading them and running cogen.'
    def add_arguments(self, parser): pass
        #parser.add_argument('sessionid', nargs='?', type=str, help='specify session to test')
        #parser.add_argument('--list', action='store_true', help='list sessions')

    def handle(self, *args, **options):
        # list sessions
        sessions = GraphSession.objects.all()
        for s in sessions:
            print(s.id, s.title, s.description)
        quit()
