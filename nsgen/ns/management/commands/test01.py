from django.core.management.base import BaseCommand
import json
import traceback

from cogen import cogen
from ns.models import GraphSession, TypeSchema


class Command(BaseCommand):
    help = 'Test all available flow charts/graph sessions by loading them and running cogen.'

    def handle(self, *args, **options):
        sessions = GraphSession.objects.all()
        for s in sessions:
            obj = json.loads(s.data_str)
            try:
                text = cogen(obj["graphdef"], obj, DB_logging=False)
            except Exception as e:
                text = traceback.format_exc()

            print()
            print()
            print("session #%d:" % s.id)
            print()
            print(text)

