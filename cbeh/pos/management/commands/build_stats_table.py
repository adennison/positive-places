# from django.core.management.base import BaseCommand
from django.core.management.base import NoArgsCommand
from pos.models import *
from pos.statistics.build_stats import areaPosStats
from pos.statistics.pos_statistics import regionPosStats

class Command(NoArgsCommand):
    help = "Rebuilds the area pop stats table"

    def handle_noargs(self, **options):
        areaPosStats()

# class Command(NoArgsCommand):
#     help = "For testing. Rebuilds the area pop stats table only for City of Cockburn."

#     def handle_noargs(self, **options):
#         regionPosStats(8)
