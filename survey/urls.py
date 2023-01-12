from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from . import views

urlpatterns = [
    #web urls
    path('web/dashboard/', views.index, name='dashboard'),
    path('dashmetrics/', views.dashmetrics, name='dashmetrics'),
    path('partner-chart/', views.partner_chart, name='partner-chart'),
    path('web/questionnaires/', views.questionnaire, name='questionnaires'),
    path('web/new-questionnaire/', views.new_questionnaire, name='new-questionnaires'),
    path('web/edit-questionnaire/<int:q_id>/', views.edit_questionnaire, name='edit-questionnaires'),
    path('web/add-question/<int:q_id>/', views.add_question, name='add-question'),
    path('web/edit-question/<int:q_id>/', views.edit_question, name='edit-question'),
    path('web/delete-question/<int:q_id>/', views.delete_question, name='delete-question'),
    path('web/question-list/<int:q_id>/', views.question_list, name='questions'),
    path('resp-chart/', views.resp_chart, name='all-resp-chart'),
    path('trend-chart/', views.trend_chart, name='trend-chart'),
    path('get/facilities/', views.get_fac),
    path('get/answers/<int:q_id>', views.answers_list),

    #Api urls
    path('api/questionnaire/all/', views.all_questionnaire_api, name='questionnaire_api'),
    path('api/questionnaire/active/', views.active_questionnaire_api, name='active_questionnaire_api'),
    path('api/questions/all/', views.all_question_api, name='all_question_api'),
    path('api/questions/list/', views.list_question_api, name='list_question_api'),
    path('api/questionnaire/start/', views.get_consent, name='provide_consent_api'),
    path('api/questions/answer/', views.answer_question, name='provide_response_api'),
    path('api/questions/answer/<int:q_id>/', views.start_questionnaire_new, name='provide_response_one_api'),
    path('api/initial/consent/', views.initial_consent, name='initial_consent_api'),

]
urlpatterns += staticfiles_urlpatterns()