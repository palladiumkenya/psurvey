from django_cron import CronJobBase, Schedule
from .models import *
from datetime import date

class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 180 # every 3 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'survey.my_cron_job'    # a unique code

    def do(self):
        queryset = Questionnaire.objects.filter(active_till__lt=date.today(), is_active=True)
        for q in queryset:
            qu = Questionnaire.objects.get(id=q.id)
            qu.is_active = False
            qu.save()
            print(qu)
        pass    # do your thing here