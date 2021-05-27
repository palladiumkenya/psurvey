from celery import task
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
# We can have either registered task
# @task(name='summary')
# def send_import_summary():
#     print('Registered')
#     return 'i am there'

# Magic happens here ...
# or
@shared_task
def send_notification():
    print('Here I\’m')
    return 'i am here'
    # Another trick
