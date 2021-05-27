from datetime import date
from survey.models import Questionnaire
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, *args, **options):
        queryset = Questionnaire.objects.filter(active_till__lt=date.today(), is_active=True)
        for q in queryset:
            try:
                qu = Questionnaire.objects.get(id=q.id)
                qu.is_active = False
                qu.save()
                print(qu)
            except Questionnaire.DoesNotExist:
                raise CommandError('Questionnaire "%s" does not exist' % q.id)
    # Another trick
