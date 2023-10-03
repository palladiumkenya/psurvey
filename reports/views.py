from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response as Res
from datetime import date
from django.shortcuts import render
from django.db.models import Count, Q
from django.db import connection
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from reports.serializer import *
from survey.models import *
# from authApp.models import Partner

import json


@login_required
def index(request, q_id):
    user = request.user
    question = Question.objects.get(id=q_id)
    respo = Response.objects.filter(question_id=q_id).order_by('-id')
    page = request.GET.get('page', 1)
    paginator = Paginator(respo, 20)
    try:
        resp = paginator.page(page)
    except PageNotAnInteger:
        resp = paginator.page(1)
    except EmptyPage:
        resp = paginator.page(paginator.num_pages)

    labels = []
    data = []

    queryset = Response.objects.filter(question_id=q_id).values(
        'answer__option').annotate(count=Count('answer'))

    for city in queryset:
        labels.append(city['answer__option'])
        data.append(city['count'])

    context = {
        'u': user,
        'items': paginator.count,
        'quest': question,
        'resp': resp,
        'labels': labels,
        'data': data,
    }
    return render(request, 'reports/response_report.html', context)


@login_required
def questionnaire_report(request, q_id):
    user = request.user
    question = Questionnaire.objects.get(id=q_id)
    respo = Response.objects.filter(
        question__questionnaire_id=q_id).order_by('-id')
    page = request.GET.get('page', 1)
    paginator = Paginator(respo, 20)
    try:
        resp = paginator.page(page)
    except PageNotAnInteger:
        resp = paginator.page(1)
    except EmptyPage:
        resp = paginator.page(paginator.num_pages)

    labels = []
    data = []
    etl_data = []

    etl_data = populate_etl_table(q_id)
    survey_count = 0 if etl_data is None else len(etl_data['data'])

    queryset = Response.objects.filter(question__questionnaire_id=q_id).values(
        'answer__option').annotate(count=Count('answer'))

    for city in queryset:
        labels.append(city['answer__option'])
        data.append(city['count'])

    context = {
        'u': user,
        'items': paginator.count,
        'quest': question,
        'resp': resp,
        'labels': labels,
        'data': data,
        'etl_data': json.dumps(etl_data),
        # 'survey_count': 0,
        'survey_count': survey_count,
    }

    # return HttpResponse(json.dumps(etl_data))
    return render(request, 'reports/questionnaire_report.html', context)


def populate_etl_table(q_id):
    try:
        etl_data = []

        # get the questions for this survey
        str_etl_query = ""
        str_max = "SELECT u.survey_id,TO_CHAR(u.submit_date,'DD/MM/YYYY') as submit_date,u.submitted_by,u.partner_name,u.county,u.sub_county,u.mfl_code,u.master_facility_name,"
        str_case = " FROM ( SELECT t.survey_id,t.submit_date,t.submitted_by,t.partner_name,t.county,t.sub_county,t.mfl_code,t.master_facility_name,"
        column_names = ['survey_id', 'submit_date', 'submitted_by', 'partner_name',
                        'county', 'sub_county', 'mfl_code', 'master_facility_name']

        questions = Question.objects.filter(
            questionnaire_id=q_id).order_by("question_order")

        for obj in questions:
            str_case += f"CASE WHEN t.question_order = {obj.question_order} THEN t.response ELSE NULL::character varying END AS {obj.response_col_name}, "
            str_max += f"max(u.{obj.response_col_name}::text) AS {obj.response_col_name}, "
            column_names.append(obj.response_col_name)
            # column_names += "{ title: '" + obj.response_col_name + "' }, "

        core_query = f" FROM ( SELECT DISTINCT z.id AS questionnaire_id,z.name AS questionnaire_name,b.id AS survey_id,p.name AS partner_name,w.mfl_code,w.name AS master_facility_name,w.county,w.sub_county,v.participant,b.ccc_number,e.question_order,e.question,CASE WHEN btrim(d.open_text::text) = ''::text THEN f.option ELSE d.open_text END AS response,y.id AS submitted_by_id,concat(y.f_name, ' ', y.l_name) AS submitted_by,d.created_at AS submit_date FROM  \"Questionnaires\" z JOIN  \"Started_Questionnaire\" b ON z.id = b.questionnaire_id JOIN  \"User\" y ON b.started_by_id = y.id JOIN  \"Facilities\" w ON y.facility_id = w.id JOIN  \"Responses\" d ON b.id = d.session_id JOIN  \"Answers\" f ON d.answer_id = f.id JOIN  \"Questions\" e ON f.question_id = e.id JOIN  \"End_Questionnaire\" h ON b.id = h.session_id JOIN  \"Questionnaire_Participants\" v ON b.questionnaire_participant_id = v.id LEFT JOIN  \"Partner_Facility\" x ON w.id = x.facility_id LEFT JOIN  \"Partner\" p ON x.partner_id = p.id WHERE z.id = {q_id} AND (y.id <> ALL (ARRAY[133, 136, 139, 138, 137, 142, 45, 155, 434])) ORDER BY b.id, e.question_order) t GROUP BY t.survey_id, t.submit_date,t.submitted_by, t.partner_name, t.county, t.sub_county, t.mfl_code, t.master_facility_name, t.question_order, t.response ORDER BY t.survey_id) u GROUP BY u.survey_id, u.submit_date,u.submitted_by, u.partner_name, u.county, u.sub_county, u.mfl_code, u.master_facility_name"

        str_etl_query = str_max[:-2] + str_case[:-2] + core_query
        # column_names = column_names[:-2] + "]"

        data = None
        with connection.cursor() as cursor:
            cursor.execute(str_etl_query)
            data = cursor.fetchall()
        return dict([('column_names', column_names), ('data', data)])

        # generate column names
        # generate raw data query for this questionnaire

        # get the completed surveys for this questionnaire
        survey_index = 0
        for survey in Started_Questionnaire.objects.filter(questionnaire_id=q_id):
            if End_Questionnaire.objects.filter(session=survey).exists():
                survey_index += 1
                survey_response = get_etl_table_row(q_id)
                submittor = Users.objects.get(id=survey.started_by_id)
                submittor_name = submittor.f_name + " " + submittor.l_name
                survey_response['survey_id'] = str(survey.id)
                survey_response['submit_date'] = str(survey.created_at)
                survey_response['submitted_by'] = submittor_name

                if submittor.facility_id:
                    faci = Facility.objects.get(id=submittor.facility_id)
                    partner_faci = Partner_Facility.objects.filter(
                        facility_id=submittor.facility_id).order_by("id").first()
                    partner = Partner.objects.get(id=partner_faci.partner_id)
                    survey_response['partner_name'] = partner.name
                    survey_response['county'] = faci.county
                    survey_response['sub_county'] = faci.sub_county
                    survey_response['mfl_code'] = str(faci.mfl_code)
                    survey_response['facility_name'] = faci.name

                # get all responses for this survey
                responses = Response.objects.filter(
                    session_id=survey.id).order_by("id")

                # generate ETL table data
                multi_select_responses = {}
                answer_value = ""

                # survey_len = len(responses)
                for obj in responses:

                    # get the question response column name for this response
                    ques = Question.objects.get(id=obj.question_id)
                    response_col_name = ques.response_col_name

                    # get the answer value for this response
                    if obj.open_text != '':
                        answer_value = obj.open_text
                    else:
                        answer_value = Answer.objects.get(
                            id=obj.answer_id).option

                    if ques.question_type != 3:
                        survey_response[response_col_name] = answer_value

                    else:
                        if not multi_select_responses.get(response_col_name):
                            multi_select_responses[response_col_name] = answer_value
                        else:
                            multi_select_responses[response_col_name] += "," + \
                                answer_value

                    for col_name, val_str in multi_select_responses.items():
                        survey_response[col_name] = val_str

                etl_data.append(survey_response)

        return etl_data

    except Exception as e:
        print("error", e)


def get_etl_table_row(q_id):
    table_row = dict(
        [('survey_id', ''), ('submit_date', ''), ('submitted_by', ''), ('partner_name', ''), ('county', ''), ('sub_county', ''), ('mfl_code', ''), ('facility_name', '')])

    questions = Question.objects.filter(
        questionnaire_id=q_id).order_by('question_order')

    for obj in questions:
        table_row[obj.response_col_name] = ''

    return table_row


def open_end(request, q_id):
    keywords = request.POST.get('keywords')
    print(keywords)
    words = keywords.replace(' ', '').split(',')

    labels = []
    data = []
    result = []
    for word in words:
        queryset = Response.objects.filter(
            question_id=q_id, open_text__icontains=word)
        result.append({'name': word, 'freq': queryset.count()})

    print(result)
    for re in result:
        labels.append(re['name'])
        data.append(re['freq'])

    context = {
        'labels': labels,
        'data': data,
    }

    return JsonResponse(context)


def pie_chart(request):
    labels = []
    data = []

    queryset = Response.objects.order_by('question')[:5]
    for city in queryset:
        labels.append(city.answer.option)
        data.append(city.id)

    return render(request, 'pie_chart.html', {
        'labels': labels,
        'data': data,
    })


def users_report(request):
    return render(request, 'reports/user_report.html', {'u': request.user})


def patients_report(request):
    return render(request, 'reports/patient_report.html', {'u': request.user})


class Current_user(viewsets.ModelViewSet):
    serializer_class = AllUserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.access_level.id == 2:
            return Users.objects.filter(facility_id__in=Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True), access_level_id=1)
        if user.access_level.id == 5:
            return Users.objects.filter(facility_id__in=Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True), access_level_id=1)
        if user.access_level.id == 3:
            return Users.objects.filter(access_level_id=1)
        if user.access_level.id == 4:
            return Users.objects.filter(facility=user.facility, access_level_id=1)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(Q(designation__name__icontains=search)
                           | Q(facility__name__icontains=search))

        return qs


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Patients(request):
    sq = Started_Questionnaire.objects.filter(
        started_by__facility=request.user.facility).order_by('ccc_number')
    print(sq)
    ser = PatientSer(sq, many=True)

    new_data = []
    not_found = True
    for item in ser.data:
        for month in new_data:
            not_found = True
            if item['ccc_number'] == month['ccc_number']:
                not_found = False
                month['responses'].append(
                    {'data': item['responses'], 'session': item['id']})

                break
        if not_found:
            new_data.append({'name': item['firstname'], 'ccc_number': item['ccc_number'],
                             'responses': [{'data': item['responses'], 'session': item['id']}]})

    print(new_data)
    data = {
        "recordsTotal": len(new_data),
        "recordsFiltered": len(new_data),
        "data": new_data,
    }

    return Res(data)


class RespViewSet(viewsets.ModelViewSet):
    serializer_class = RespSerializer

    def get_queryset(self):
        nome = self.kwargs['question_id']
        return Response.objects.filter(question_id=nome).order_by('-id')

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            for q in qs:
                if q.question.question_type == 1 or q.question.question_type == 4 or q.question.question_type == 5:
                    return qs.filter(open_text__icontains=search)
                else:
                    return qs.filter(answer__option__icontains=search)

        return qs


class QuestionnaireViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionnaireRespSerializer

    def get_queryset(self):
        name = self.kwargs['questionnaire_id']
        return Response.objects.filter(question__questionnaire_id=name).order_by('-id')

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            for q in qs:
                if q.question.question_type == 1 or q.question.question_type == 4 or q.question.question_type == 5:
                    return qs.filter(open_text__icontains=search)
                else:
                    return qs.filter(answer__option__icontains=search)

        return qs
