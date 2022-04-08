from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework import routers

from . import views
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'albums/(?P<question_id>\d+)', views.RespViewSet, basename='Response')
router.register(r'questionnaire/(?P<questionnaire_id>\d+)', views.QuestionnaireViewSet, basename='QResponse')
router.register(r'reports/list', views.Current_user, basename='Users')
# router.register(r'patients/list', views.Patients, basename='Start_Questionnaire')

urlpatterns = [
    #web urls
    path('web/reports/response/<int:q_id>', views.index, name='response_report'),
    path('web/reports/questionnaire/<int:q_id>', views.questionnaire_report, name='q_response_report'),
    path('web/reports/open_resp/<int:q_id>', views.open_end, name='open_resp_report'),
    path('web/reports/users', views.users_report, name='users_report'),
    path('web/reports/patients', views.patients_report, name='patients_report'),
    path('web/patients/list', views.Patients, name='patients_list'),
    url('^api/', include(router.urls)),

]
urlpatterns += staticfiles_urlpatterns()