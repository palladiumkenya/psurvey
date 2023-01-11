from itertools import filterfalse, islice
import json
from datetime import date
from itertools import chain

# from dateutil.relativedelta import relativedelta
import requests
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.serializers import serialize
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.db.models.functions import Cast, TruncMonth
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from docutils.nodes import status
from rest_framework import status
from rest_framework.response import Response as Res
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from survey.bulk_manager import BulkCreateManager


from .models import *
from .serializer import *
from authApp.serializer import *


# api
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_questionnaire_api(request):
    if request.user.access_level.id == 1:
            q = Facility_Questionnaire.objects.filter(facility_id=request.user.facility.id).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
    elif request.user.access_level.id == 2:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True))
        q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                    ).values_list('questionnaire_id').distinct()
        quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
    elif request.user.access_level.id == 3:
        quest = Questionnaire.objects.filter().order_by('-created_at')
    elif request.user.access_level.id == 4:
            q = Facility_Questionnaire.objects.filter(facility_id=request.user.facility.id).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
    elif request.user.access_level.id == 5:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True))
        q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                    ).values_list('questionnaire_id').distinct()
        quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
        
    serializer = QuestionnaireSerializer(quest, many=True)
    
    return Res({"data": serializer.data}, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_questionnaire_api(request):
    if request.user.access_level.id == 1:
        quest = Facility_Questionnaire.objects.filter(facility_id=request.user.facility.id)

        queryset = Questionnaire.objects.filter(id__in=quest.values_list('questionnaire_id', flat=True), is_active=True,
                                            active_till__gte=date.today())
    elif request.user.access_level.id == 2:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True))
        q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                    ).values_list('questionnaire_id').distinct()
        quest = Questionnaire.objects.filter(id__in=q, is_active=True,
                                            active_till__gte=date.today()).order_by('-created_at')
    elif request.user.access_level.id == 3:
        quest = Questionnaire.objects.filter(is_active=True, active_till__gte=date.today()).order_by('-created_at')
    elif request.user.access_level.id == 4:
            q = Facility_Questionnaire.objects.filter(facility_id=request.user.facility.id).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q, is_active=True, active_till__gte=date.today()).order_by('-created_at')
    elif request.user.access_level.id == 5:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True))
        q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                    ).values_list('questionnaire_id').distinct()
        quest = Questionnaire.objects.filter(id__in=q, is_active=True, active_till__gte=date.today()).order_by('-created_at')
    
    serializer = QuestionnaireSerializer(queryset, many=True)
    return Res({"data": serializer.data}, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def all_question_api(request):
    quest = Question.objects.filter(questionnaire_id=request.data['questionnaire_id']).order_by('question_order')
    serializer = QuestionSerializer(quest, many=True)

    return Res({"data": serializer.data}, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_question_api(request):
    quest = Answer.objects.filter(question_id=request.data['question_id'])
    serializer = QuestionResponseSerializer(quest, many=True)

    return Res({"data": serializer.data}, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_consent(request):
    quest = Question.objects.filter(questionnaire_id=request.data['questionnaire_id']).order_by('question_order')[:1]
    a_id = 0
    for q in quest:
        a_id =q.id

    consent = Patient_Consent.objects.create(questionnaire_id=request.data['questionnaire_id'],
                                             ccc_number=request.data['ccc_number'])
    consent.save()
    session = Started_Questionnaire.objects.create(questionnaire_id=request.data['questionnaire_id'],
                                                   started_by=request.user,
                                                   ccc_number=request.data['ccc_number'],
                                                   firstname=request.data['first_name'])
    session.save()
    return JsonResponse({
        'link': 'https://psurvey-api.mhealthkenya.co.ke/api/questions/answer/{}'.format(a_id),
        'session': session.pk
    })
    # return Res({"Question": serializer.data, "Ans": ser.data, "session_id": session.pk}, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initial_consent(request):
    check = check_ccc(request.data['ccc_number'])
    if not check:
        return Res({'error': False, 'message': 'ccc number doesnt exist'}, status=status.HTTP_200_OK)
    if check['f_name'].upper() != request.data['first_name'].upper():
        return Res({'error': False, 'message': 'client verification failed'}, status=status.HTTP_200_OK)
    return Res({'success': True, 'message': "You can now start questionnaire"}, status=status.HTTP_200_OK)


def check_ccc(value):
    user = {
        "ccc_number": value
    }

    url = "http://ushaurinode.mhealthkenya.org/api/mlab/get/one/client"
    headers = {
        'content-type': "application/json",
        'Accept': 'application/json'
    }
    response = requests.post(url, data=user, json=headers)
    try:
        return response.json()["clients"][0]
    except IndexError:
        return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def start_questionnaire_new(request, q_id):
    quest = Question.objects.get(id=q_id)
    serializer = QuestionSerializer(quest)
    queryset = Answer.objects.filter(question_id=quest)
    ser = AnswerSerializer(queryset, many=True)

    return Res({"Question": serializer.data, "Ans": ser.data}, status.HTTP_200_OK)


@api_view(['POST'])
def answer_question(request):
    q = Question.objects.get(id=request.data['question'])

    if q.question_type == 3:
        a = request.data.copy()
        trans_one = transaction.savepoint()
        b = a['answer'].split(',')

        for i in b:

            a.update({'answer': i})
            serializer = ResponseSerializer(data=a)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            else:
                transaction.savepoint_rollback(trans_one)
                return Res({'success': False, 'error': 'Unknown error, try again'}, status=status.HTTP_400_BAD_REQUEST)

        q = Question.objects.get(id=serializer.data['question'])
        quest = Questionnaire.objects.get(id=q.questionnaire_id)
        questions = Question.objects.filter(questionnaire=quest)

        foo = q
        previous = next_ = None
        l = len(questions)
        for index, obj in enumerate(questions):
            if obj == foo:
                if index > 0:
                    previous = questions[index - 1]
                if index < (l - 1):
                    next_ = questions[index + 1]
                    return JsonResponse({
                        'link': 'https://psurvey-api.mhealthkenya.co.ke/api/questions/answer/{}'.format(next_.id),
                        "session_id": serializer.data['session']
                    })

                elif next_ == None:
                    end = End_Questionnaire.objects.create(questionnaire=quest, session_id=serializer.data['session'])
                    end.save()
                    return Res({
                        "success": True,
                        "Message": "Questionnaire complete, Thank You👌!"
                    }, status.HTTP_200_OK)
        return Res({'success': False, 'error': 'Unknown error, try again'}, status=status.HTTP_400_BAD_REQUEST)

    else:
        serializer = ResponseSerializer(data=request.data)
        print(serializer.is_valid(raise_exception=True))
        try:
            if serializer.is_valid():
                data = check_answer_algo(serializer)
            else:
                return Res({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("error", e)
            return Res(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return data


def check_answer_algo(ser):
    ser.save()
    q = Question.objects.get(id=ser.data['question'])
    quest = Questionnaire.objects.get(id=q.questionnaire_id)
    question_depends_on = QuestionDependance.objects.filter(
            question__in=Question.objects.filter(questionnaire=quest).order_by("question_order")
        ).exclude(
            answer_id__in=Response.objects.filter(session_id=ser.data['session']).values_list('answer_id', flat=True)
        )
    
    if question_depends_on.exists():
        questions = Question.objects.filter(questionnaire=quest).order_by("question_order").exclude(id__in=question_depends_on.values_list('question_id', flat=True))
    else:
        questions = Question.objects.filter(questionnaire=quest).order_by("question_order")

    foo = q
    previous = next_ = None
    l = len(questions)
    for index, obj in enumerate(questions):
        if obj == foo:
            if index > 0:
                previous = questions[index - 1]
            if index < (l - 1):
                next_ = questions[index + 1]
                serializer = QuestionSerializer(next_)
                queryset = Answer.objects.filter(question=next_)
                ans_ser = AnswerSerializer(queryset, many=True)
                return JsonResponse({
                    'link': 'https://psurvey-api.mhealthkenya.co.ke/api/questions/answer/{}'.format(next_.id),
                    "session_id": ser.data['session']
                })

            elif next_ == None:
                end = End_Questionnaire.objects.create(questionnaire=quest, session_id=ser.data['session'])
                end.save()
                return Res({
                    "success": True,
                    "Message": "Questionnaire complete, Thank You👌!"
                }, status.HTTP_200_OK)
    return Res({'success': False, 'error': 'Unknown error, try again'}, status=status.HTTP_400_BAD_REQUEST)


# web
def get_fac(request):
    if request.method == "POST":
        if request.user.access_level.id == 3:
            county_list = request.POST.getlist('county_list[]')
            print(request.POST)
            fac = Facility.objects.filter(county__in=county_list)

            serialized = serialize('json', fac)
            obj_list = json.loads(serialized)
        elif request.user.access_level.id == 2:
            county_list = request.POST.getlist('county_list[]')
            fac = Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True))
            fac = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True), county__in=county_list)

            serialized = serialize('json', fac)
            obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


@login_required
def index(request):
    user = request.user
    is_active = request.POST.get('active')

    if user.access_level.id == 3:
        fac = Facility.objects.all().order_by('county', 'sub_county', 'name')
        quest = Questionnaire.objects.filter(is_active=True).order_by('name')
        if is_active == 'active':
            quest = Questionnaire.objects.filter(is_active=True).values_list('id', flat=True)
        elif is_active == 'inactive':
            quest = Questionnaire.objects.filter(is_active=False).values_list('id', flat=True)
        aq = Questionnaire.objects.filter(is_active=True, active_till__gte=date.today())
        resp = End_Questionnaire.objects.filter()
        queryset = Facility.objects.all().distinct('county')
        org = Partner.objects.all().order_by('name')
        context = {
            'u': user,
            'fac': fac,
            'quest': quest,
            'aq': aq,
            'resp': resp,
            'county': queryset,
            'org': org
        }
        return render(request, 'survey/dashboard.html', context)
    elif user.access_level.id == 2:
        fac = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')

        fac_quest = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True)
                                                ).values_list('questionnaire').distinct()
        quest = Questionnaire.objects.filter(is_active=True,id__in=fac_quest)
        aq = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                    questionnaire__is_active=True,
                                                    questionnaire__active_till__gte=date.today()
                                                ).values_list('questionnaire').distinct()

        resp = End_Questionnaire.objects.filter(questionnaire__in=quest)
        context = {
            'u': user,
            'fac': fac,
            'quest': quest,
            'aq': aq,
            'resp': resp,
        }
        return render(request, 'survey/dashboard.html', context)
    elif user.access_level.id == 4:
        que = Facility_Questionnaire.objects.filter(facility_id=user.facility.id).values_list('questionnaire_id').distinct()
        fac = Facility.objects.all().order_by('county', 'sub_county', 'name')
        quest = Questionnaire.objects.filter(id__in=que, is_active=True)
        aq = Questionnaire.objects.filter(is_active=True, active_till__gte=date.today(), id__in=que)
        resp = End_Questionnaire.objects.filter(session__started_by__facility=user.facility)
        pat = Started_Questionnaire.objects.filter(started_by__facility=user.facility).distinct('ccc_number').count()

        context = {
            'u': user,
            'fac': pat,
            'quest': quest,
            'aq': aq,
            'resp': resp,
        }
        return render(request, 'survey/dashboard.html', context)
    elif user.access_level.id == 5:
        fac = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')

        fac_quest = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True)
                                                    ).values_list('questionnaire').distinct()
        quest = Questionnaire.objects.filter(is_active=True, id__in=fac_quest)
        aq = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                questionnaire__is_active=True,
                                                questionnaire__active_till__gte=date.today()
                                            ).values_list('questionnaire').distinct()

        resp = End_Questionnaire.objects.filter(questionnaire__in=quest)
        context = {
            'u': user,
            'fac': fac,
            'quest': quest,
            'aq': aq,
            'resp': resp,
        }
        return render(request, 'survey/dashboard.html', context)


def dashmetrics(request):
    user = request.user
    is_active = request.POST.get('active')
    qs = request.POST.getlist('questionnaire[]', [])
    org = request.POST.getlist('org[]', [])

    if user.access_level.id == 3:
        fac = Facility.objects.all().order_by('county', 'sub_county', 'name')
        if len(qs) > 0 and len(org) > 0:
            part_fac = Partner_Facility.objects.filter(partner_id__in=org)
            quest_org = Facility_Questionnaire.objects.filter(questionnaire__in=qs, facility_id__in=part_fac.values_list('facility', flat=True))
            quest = Questionnaire.objects.filter(id__in=quest_org.values_list('questionnaire', flat=True))
            fac = Facility.objects.filter(id__in=part_fac.values_list('facility', flat=True))
        elif len(qs) > 0:
            quest = Questionnaire.objects.filter(id__in=qs)
        elif len(org) > 0:
            part_fac = Partner_Facility.objects.filter(partner_id__in=org)
            quest_org = Facility_Questionnaire.objects.filter(facility_id__in=part_fac.values_list('facility', flat=True))
            quest = Questionnaire.objects.filter(id__in=quest_org.values_list('questionnaire', flat=True))
            fac = Facility.objects.filter(id__in=part_fac.values_list('facility', flat=True))
        else:
            quest = Questionnaire.objects.all()

        # quest = Questionnaire.objects.filter(id__in=questionnaire).values_list('id', flat=True)

        # if is_active == 'active':
        #     quest = Questionnaire.objects.filter(id__in=questionnaire, is_active=True).values_list('id', flat=True)
        # elif is_active == 'inactive':
        #     quest = Questionnaire.objects.filter(id__in=questionnaire, is_active=False).values_list('id', flat=True)
        aq = Questionnaire.objects.filter(is_active=True, active_till__gte=date.today())
        st = Started_Questionnaire.objects.filter(started_by__facility__in=fac, questionnaire__in=quest)
        resp = End_Questionnaire.objects.filter(session__in=st, questionnaire__in=quest)
        

    elif user.access_level.id == 2:
        fac = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')

        if len(qs) > 0:
            questionnaire = Facility_Questionnaire.objects.filter(questionnaire_id__in=qs, facility_id__in=fac.values_list('id', flat=True)
                                                    ).values_list('questionnaire').distinct()
        else:
            questionnaire = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True)
                                                    ).values_list('questionnaire').distinct()
        quest = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                        questionnaire__in=questionnaire
                                                    ).values_list('questionnaire').distinct()

        if is_active == 'active':
            quest = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                        questionnaire__in=questionnaire,
                                                        questionnaire__is_active=True
                                                    ).values_list('questionnaire').distinct()
        elif is_active == 'inactive':
            quest = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True), 
                                                        questionnaire__in=questionnaire,
                                                        questionnaire__is_active=False
                                                    ).values_list('questionnaire').distinct()
        aq = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                questionnaire__is_active=True,
                                                questionnaire__active_till__gte=date.today()
                                            ).values_list('questionnaire').distinct()

        resp = End_Questionnaire.objects.filter(questionnaire__in=quest)

    elif user.access_level.id == 4:
        # fac = Facility.objects.all().order_by('county', 'sub_county', 'name')

        if len(qs) > 0:
            que = Facility_Questionnaire.objects.filter(questionnaire_id__in=qs, facility_id=user.facility.id).values_list('questionnaire_id').distinct()
            questionnaire = Questionnaire.objects.filter(id__in=que)
        else:
            que = Facility_Questionnaire.objects.filter(facility_id=user.facility.id).values_list('questionnaire_id').distinct()
            questionnaire = Questionnaire.objects.filter(id__in=que)
        quest = Questionnaire.objects.filter(id__in=que).values_list('id', flat=True)

        if is_active == 'active':
            quest = Questionnaire.objects.filter(id__in=que, is_active=True).values_list('id', flat=True)
        elif is_active == 'inactive':
            quest = Questionnaire.objects.filter(id__in=que, is_active=False).values_list('id', flat=True)
        aq = Questionnaire.objects.filter(is_active=True, active_till__gte=date.today(), id__in=que)
        resp = End_Questionnaire.objects.filter(session__started_by__facility=user.facility)
        fac = Started_Questionnaire.objects.filter(started_by__facility=user.facility).distinct('ccc_number')

    elif user.access_level.id == 5:
        fac = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')

        if len(qs) > 0:
            questionnaire = Facility_Questionnaire.objects.filter(questionnaire_id__in=qs,
                                                    facility_id__in=fac.values_list('id', flat=True)
                                                ).values_list('questionnaire').distinct()
        else:
            questionnaire = Facility_Questionnaire.objects.filter(
                                                facility_id__in=fac.values_list('id', flat=True)
                                            ).values_list('questionnaire').distinct()
        quest = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                    questionnaire__in=questionnaire
                                                ).values_list('questionnaire').distinct()
        
        if is_active == 'active':
            quest = Facility_Questionnaire.objects.filter(questionnaire__in=questionnaire,
                                                          facility_id__in=fac.values_list('id', flat=True), 
                                                          questionnaire__is_active=True
                                                          ).values_list('questionnaire').distinct()
        elif is_active == 'inactive':
            quest = Facility_Questionnaire.objects.filter(questionnaire__in=questionnaire,
                                                          facility_id__in=fac.values_list('id', flat=True), 
                                                          questionnaire__is_active=False
                                                          ).values_list('questionnaire').distinct()
        aq = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('id', flat=True),
                                                   questionnaire__is_active=True,
                                                   questionnaire__active_till__gte=date.today()
                                                   ).values_list('questionnaire').distinct()

        resp = End_Questionnaire.objects.filter(questionnaire__in=quest)

    return JsonResponse(data={
        'fac': fac.count(),
        'quest': quest.count(),
        'aq': aq.count(),
        'resp': resp.count(),
    })


def resp_chart(request):
    start = request.POST.get('start_date')
    end = request.POST.get('end_date')
    facilities = request.POST.getlist('fac[]', '')
    qs = request.POST.getlist('questionnaire[]', [])
    is_active = request.POST.get('active')
    org = request.POST.getlist('org[]', [])

    labels = []
    data = []
    if request.user.access_level.id == 3:
        if facilities == '':
            facilities = Facility.objects.values_list('id', flat=True)

        if len(qs) > 0 and len(org) > 0:
            part_fac = Partner_Facility.objects.filter(partner_id__in=org)
            quest_org = Facility_Questionnaire.objects.filter(questionnaire__in=qs, facility_id__in=part_fac.values_list('facility', flat=True))
            questionnaire = Questionnaire.objects.filter(id__in=quest_org.values_list('questionnaire', flat=True))
            facilities = Facility.objects.filter(id__in=part_fac.values_list('facility', flat=True))
        elif len(qs) > 0:
            questionnaire = Questionnaire.objects.filter(id__in=qs)
        elif len(org) > 0:
            part_fac = Partner_Facility.objects.filter(partner_id__in=org)
            quest_org = Facility_Questionnaire.objects.filter(facility_id__in=part_fac.values_list('facility', flat=True))
            questionnaire = Questionnaire.objects.filter(id__in=quest_org.values_list('questionnaire', flat=True))
            facilities = Facility.objects.filter(id__in=part_fac.values_list('facility', flat=True))
        else:
            questionnaire = Questionnaire.objects.filter().values_list('id', flat=True)

        # if is_active == 'active':
        #     questionnaire = Questionnaire.objects.filter(id__in=quest, is_active=True).values_list('id', flat=True)
        # elif is_active == 'inactive':
        #     questionnaire = Questionnaire.objects.filter(id__in=quest, is_active=False).values_list('id', flat=True)

        st = Started_Questionnaire.objects.filter(started_by__facility_id__in=facilities, questionnaire__in=questionnaire)
        queryset = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session__in=st
        ).values('created_at').annotate(count=Count('created_at')).order_by('created_at')

    if request.user.access_level.id == 2:
        if facilities == '':
            facilities = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True)).values_list(
                'facility_id', flat=True))
        if len(qs) > 0:
            quest = Questionnaire.objects.filter(id__in=qs).values_list('id', flat=True)
        else:
            quest = Questionnaire.objects.filter().values_list('id', flat=True)

        questionnaire = Questionnaire.objects.filter(id__in=quest).values_list('id', flat=True)
        if is_active == 'active':
            questionnaire = Questionnaire.objects.filter(id__in=quest, is_active=True).values_list('id', flat=True)
        elif is_active == 'inactive':
            questionnaire = Questionnaire.objects.filter(id__in=quest, is_active=False).values_list('id', flat=True)
        st = Started_Questionnaire.objects.filter(started_by__facility_id__in=facilities, questionnaire__in=questionnaire)

        queryset = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session__in=st
        ).values('created_at').annotate(count=Count('created_at')).order_by('created_at')

    if request.user.access_level.id == 4:
        facilities =  request.user.facility.id
        if len(qs) > 0:
            quest = Questionnaire.objects.filter(id__in=qs).values_list('id', flat=True)
        else:
            quest = Questionnaire.objects.filter().values_list('id', flat=True)

        questionnaire = Questionnaire.objects.filter(id__in=quest).values_list('id', flat=True)
        if is_active == 'active':
            questionnaire = Questionnaire.objects.filter(id__in=quest, is_active=True).values_list('id', flat=True)
        elif is_active == 'inactive':
            questionnaire = Questionnaire.objects.filter(id__in=quest, is_active=False).values_list('id', flat=True)
        st = Started_Questionnaire.objects.filter(started_by__facility_id=facilities, questionnaire__in=questionnaire)

        queryset = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session__in=st
        ).values('created_at').annotate(count=Count('created_at')).order_by('created_at')

    for entry in queryset:
        labels.append(entry['created_at'])
        data.append(entry['count'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })


def trend_chart(request):
    start = request.POST.get('start_date')
    end = request.POST.get('end_date')
    facilities = request.POST.getlist('fac[]', '')
    qs = request.POST.getlist('questionnaire[]', [])
    is_active = request.POST.get('active')
    org = request.POST.getlist('org[]', [])

    labels = []
    data = []
    data1 = []
    if request.user.access_level.id == 3:
        if facilities == '':
            facilities = Facility.objects.values_list('id', flat=True)

        if len(qs) > 0 and len(org) > 0:
            part_fac = Partner_Facility.objects.filter(partner_id__in=org)
            quest_org = Facility_Questionnaire.objects.filter(questionnaire__in=qs, facility_id__in=part_fac.values_list('facility', flat=True))
            questionnaire = Questionnaire.objects.filter(id__in=quest_org.values_list('questionnaire', flat=True))
            facilities = Facility.objects.filter(id__in=part_fac.values_list('facility', flat=True))
        elif len(qs) > 0:
            questionnaire = Questionnaire.objects.filter(id__in=qs)
        elif len(org) > 0:
            part_fac = Partner_Facility.objects.filter(partner_id__in=org)
            quest_org = Facility_Questionnaire.objects.filter(facility_id__in=part_fac.values_list('facility', flat=True))
            questionnaire = Questionnaire.objects.filter(id__in=quest_org.values_list('questionnaire', flat=True))
            facilities = Facility.objects.filter(id__in=part_fac.values_list('facility', flat=True))
        else:
            questionnaire = Questionnaire.objects.filter()

        # if is_active == 'active':
        #     questionnaire = Questionnaire.objects.filter(id__in=qs, is_active=True).values_list('id', flat=True)
        # elif is_active == 'inactive':
        #     questionnaire = Questionnaire.objects.filter(id__in=qs, is_active=False).values_list('id', flat=True)

        st = Started_Questionnaire.objects.filter(started_by__facility_id__in=facilities, questionnaire__in=questionnaire)
        end_q = End_Questionnaire.objects.filter(session__in=st, questionnaire__in=questionnaire)
        st_q = Started_Questionnaire.objects.filter(id__in=st.values_list('id', flat=True)).exclude(id__in=end_q.values_list('session', flat=True))

        re = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session__in=st_q
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(
            c=Count('session', distinct=True)).values('month', 'c').order_by('month')

        complete = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session_id__in=end_q.values_list('session', flat=True)
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(
            d=Count('session', distinct=True)).values('month', 'd').order_by('month')
        model_combination = list(chain(complete, re))

    if request.user.access_level.id == 2:
        if facilities == '':
            facilities = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=request.user).values_list('name', flat=True)).values_list(
                'facility_id', flat=True))
        if len(qs) > 0:
            questionnaire = Questionnaire.objects.filter(id__in=qs).values_list('id', flat=True)
        else:
            questionnaire = Questionnaire.objects.filter().values_list('id', flat=True)
        if is_active == 'active':
            questionnaire = Questionnaire.objects.filter(id__in=qs, is_active=True).values_list('id', flat=True)
        elif is_active == 'inactive':
            questionnaire = Questionnaire.objects.filter(id__in=qs, is_active=False).values_list('id', flat=True)
            
        st = Started_Questionnaire.objects.filter(started_by__facility_id__in=facilities, questionnaire__in=questionnaire)
        end_q = End_Questionnaire.objects.filter(session__in=st, questionnaire__in=questionnaire)
        st_q = Started_Questionnaire.objects.filter(id__in=st.values_list('id', flat=True)).exclude(id__in=end_q.values_list('session', flat=True))

        re = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session__in=st_q
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(
            c=Count('session', distinct=True)).values('month', 'c').order_by('month')

        complete = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session_id__in=end_q.values_list('session', flat=True)
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(
            d=Count('session', distinct=True)).values('month', 'd').order_by('month')
        model_combination = list(chain(complete, re))

    if request.user.access_level.id == 4:
        facilities = request.user.facility.id
        if len(qs) > 0:
            questionnaire = Questionnaire.objects.filter(id__in=qs).values_list('id', flat=True)
        else:
            questionnaire = Questionnaire.objects.filter().values_list('id', flat=True)
        if is_active == 'active':
            questionnaire = Questionnaire.objects.filter(id__in=qs, is_active=True).values_list('id', flat=True)
        elif is_active == 'inactive':
            questionnaire = Questionnaire.objects.filter(id__in=qs, is_active=False).values_list('id', flat=True)
            
        st = Started_Questionnaire.objects.filter(started_by__facility_id=facilities, questionnaire__in=questionnaire)
        end_q = End_Questionnaire.objects.filter(session__in=st, questionnaire__in=questionnaire)
        st_q = Started_Questionnaire.objects.filter(id__in=st.values_list('id', flat=True)).exclude(id__in=end_q.values_list('session', flat=True))

        re = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session__in=st_q
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(
            c=Count('session', distinct=True)).values('month', 'c').order_by('month')

        complete = Response.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            session_id__in=end_q.values_list('session', flat=True)
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(
            d=Count('session', distinct=True)).values('month', 'd').order_by('month')
        model_combination = list(chain(complete, re))

    out = {}
    for d in model_combination:
        out[d["month"]] = {**out.get(d["month"], {}), **d}

    out = list(out.values())
    for entry in out:
        labels.append(entry['month'].strftime('%B') + '-' + entry['month'].strftime('%y'))
        data.append(entry['c'])
        data1.append(entry['d'])

    return JsonResponse(data={
        'labels': labels,
        'data': [data, data1],
    })


@login_required
def new_questionnaire(request):
    user = request.user
    u = user
    if request.method == 'POST':
        name = request.POST.get('title')
        facility = request.POST.getlist('facility')
        desc = request.POST.get('description')
        dateTill = request.POST.get('date-till')
        isActive = request.POST.get('isActive')
        num_questions = request.POST.get('num_questions')
        target_app = request.POST.get('target_app')

        if isActive == "inactive":
            isActive = False
        else:
            isActive = True
        trans_one = transaction.savepoint()
        create_quest = Questionnaire.objects.create(name=name, is_active=isActive, description=desc, active_till=dateTill, created_by=request.user, number_of_questions=num_questions, target_app=target_app)
        create_quest.save()
        q_id = create_quest.pk

        if q_id:
            try:
                batch_size = 500
                objs = (Facility_Questionnaire(facility_id=f, questionnaire_id=q_id) for f in facility)
                # while True:
                #     batch = list(islice(objs, batch_size))
                #     if not batch:
                #         break
                #     Facility_Questionnaire.objects.bulk_create(batch, batch_size)
                bulk_mgr = BulkCreateManager(chunk_size=2000)
                for f in facility:
                    bulk_mgr.add(Facility_Questionnaire(facility_id=f, questionnaire_id=q_id))
                bulk_mgr.done()
                # for f in facility:
                #     fac_save = Facility_Questionnaire.objects.create(facility_id=f, questionnaire_id=q_id)
                #     fac_save.save()
            except IntegrityError:
                transaction.savepoint_rollback(trans_one)
                return HttpResponse("error")

    if user.access_level.id == 3:
        facilities = Facility.objects.all().order_by('county', 'sub_county', 'name')
        queryset = Facility.objects.all().distinct('county')
        context = {
            'u': u,
            'county': queryset,
            'fac': facilities,
        }
        return render(request, 'survey/new_questionnaire.html', context)
    elif user.access_level.id == 2:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
        facilities = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')
        queryset = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True)).distinct('county')
        context = {
            'u': u,
            'fac': facilities,
            'county': queryset,
        }
        return render(request, 'survey/new_questionnaire.html', context)
    elif user.access_level.id == 5:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
        facilities = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')
        queryset = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True)).distinct('county')
        context = {
            'u': u,
            'fac': facilities,
            'county': queryset,
        }
        return render(request, 'survey/new_questionnaire.html', context)
    elif user.access_level.id == 4:
        raise PermissionDenied


@login_required
def edit_questionnaire(request, q_id):
    user = request.user
    u = user
    if request.method == 'POST':
        name = request.POST.get('title')
        facility = request.POST.getlist('facility')
        desc = request.POST.get('description')
        dateTill = request.POST.get('date-till')
        isActive = request.POST.get('isActive')
        num_questions = request.POST.get('num_questions')
        target_app = request.POST.get('target_app')

        if isActive == "inactive":
            isActive = False
        else:
            isActive = True

        trans_one = transaction.savepoint()

        create_quest = Questionnaire.objects.get(id=q_id)
        create_quest.name = name
        create_quest.is_active = isActive
        create_quest.description = desc
        create_quest.active_till = dateTill
        create_quest.number_of_questions = num_questions
        create_quest.target_app = target_app

        create_quest.save()

        if q_id:
            try:
                fac = Facility_Questionnaire.objects.filter(questionnaire_id=q_id)
                fac_list = []
                for fi in fac:
                    fac_list.append(str(fi.facility_id))
                print(facility)
                for f in fac_list:
                    fac_rem = Facility_Questionnaire.objects.filter(facility_id=f, questionnaire_id=q_id)
                    fac_rem.delete()

                bulk_mgr = BulkCreateManager(chunk_size=2000)
                for f in facility:
                    bulk_mgr.add(Facility_Questionnaire(facility_id=f, questionnaire_id=q_id))
                bulk_mgr.done()
                    # fac_save = Facility_Questionnaire.objects.create(facility_id=f, questionnaire_id=q_id)
                    # fac_save.save()
            except IntegrityError:
                transaction.savepoint_rollback(trans_one)
                return HttpResponse("error")

    if user.access_level.id == 3:
        question = Questionnaire.objects.get(id=q_id)
        selected = Facility_Questionnaire.objects.filter(questionnaire_id=q_id)
        facilities = Facility.objects.all().exclude(id__in=selected.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')
        s = Facility.objects.all().filter(id__in=selected.values_list('facility_id', flat=True))

        context = {
            'u': u,
            'fac': facilities,
            'q': question,
            'fac_sel': s,
        }
        return render(request, 'survey/edit_questionnaire.html', context)
    if user.access_level.id == 2:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
        selected = Facility_Questionnaire.objects.filter(questionnaire_id=q_id)
        try:
            question = Questionnaire.objects.get(id=q_id)
        except Questionnaire.DoesNotExist:
            raise Http404('Questionnaire Does not exist')

        if question.created_by.access_level.id == 3:
            raise PermissionDenied
        facilities = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True)
                                             ).exclude(id__in=selected.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')
        s = Facility.objects.all().filter(id__in=selected.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')

        context = {
            'u': u,
            'fac': facilities,
            'q': question,
            'fac_sel': s,
        }
        return render(request, 'survey/edit_questionnaire.html', context)
    if user.access_level.id == 5:
        fac = Partner_Facility.objects.filter(
            partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
        selected = Facility_Questionnaire.objects.filter(questionnaire_id=q_id)
        try:
            question = Questionnaire.objects.get(id=q_id)
        except Questionnaire.DoesNotExist:
            raise Http404('Questionnaire Does not exist')

        if question.created_by.access_level.id == 3:
            raise PermissionDenied
        facilities = Facility.objects.filter(id__in=fac.values_list('facility_id', flat=True)
                                             ).exclude(id__in=selected.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')
        s = Facility.objects.all().filter(id__in=selected.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')

        context = {
            'u': u,
            'fac': facilities,
            'q': question,
            'fac_sel': s,
        }
        return render(request, 'survey/edit_questionnaire.html', context)
    if user.access_level.id == 4:
        raise PermissionDenied


@login_required
def questionnaire(request):
    user = request.user
    u = user
    if request.method == "POST":
        print(request.POST)
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        if user.access_level.id == 3:
            quest = Questionnaire.objects.filter(created_at__gte=start, created_at__lte=end).order_by('-created_at')
            count = Questionnaire.objects.filter(created_at__gte=start, created_at__lte=end).count()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)
            context = {
                'u': u,
                'quest': quest,
                'count': count,
            }

            return render(request, 'survey/questionnaires.html', context)

        elif user.access_level.id == 4:
            q = Facility_Questionnaire.objects.filter(facility_id=user.facility.id).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(created_at__gte=start, created_at__lte=end, id__in=q).order_by('-created_at')
            count = Questionnaire.objects.filter(created_at__gte=start, created_at__lte=end, id__in=q).count()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)
            context = {
                'u': u,
                'quest': quest,
                'count': count,
            }

            return render(request, 'survey/questionnaires.html', context)

        elif user.access_level.id == 2:
            fac = Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
            q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                      ).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q, created_at__gte=start, created_at__lte=end).order_by('-created_at')
            count = quest.count()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)

            context = {
                'u': u,
                'quest': quest,
                'fac': fac,
                'count': count,
            }
            return render(request, 'survey/questionnaires.html', context)
        elif user.access_level.id == 5:
            fac = Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
            q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                      ).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q, created_at__gte=start, created_at__lte=end).order_by('-created_at')
            count = quest.count()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)

            context = {
                'u': u,
                'quest': quest,
                'fac': fac,
                'count': count,
            }
            return render(request, 'survey/questionnaires.html', context)
    elif request.method == "GET":
        if user.access_level.id == 3:
            quest = Questionnaire.objects.all().order_by('-created_at')
            count = Questionnaire.objects.all().count()
            fac = Facility.objects.all()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)
            context = {
                'u': u,
                'quest': quest,
                'fac': fac,
                'count': count,
            }
            return render(request, 'survey/questionnaires.html', context)
        if user.access_level.id == 4:
            q = Facility_Questionnaire.objects.filter(facility_id=user.facility.id).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
            count = Questionnaire.objects.filter(id__in=q).count()
            fac = Facility.objects.all()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)
            context = {
                'u': u,
                'quest': quest,
                'fac': fac,
                'count': count,
            }
            return render(request, 'survey/questionnaires.html', context)
        elif user.access_level.id == 2:
            fac = Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
            q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                      ).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
            count = quest.count()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)

            context = {
                'u': u,
                'quest': quest,
                'fac': fac,
                'count': count,
            }
            return render(request, 'survey/questionnaires.html', context)
        elif user.access_level.id == 5:
            fac = Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True))
            q = Facility_Questionnaire.objects.filter(facility_id__in=fac.values_list('facility_id', flat=True)
                                                      ).values_list('questionnaire_id').distinct()
            quest = Questionnaire.objects.filter(id__in=q).order_by('-created_at')
            count = quest.count()

            page = request.GET.get('page', 1)
            paginator = Paginator(quest, 20)
            try:
                quest = paginator.page(page)
            except PageNotAnInteger:
                quest = paginator.page(1)
            except EmptyPage:
                quest = paginator.page(paginator.num_pages)

            context = {
                'u': u,
                'quest': quest,
                'fac': fac,
                'count': count,
            }
            return render(request, 'survey/questionnaires.html', context)


@login_required
def add_question(request, q_id):
    user = request.user
    u = user
    if request.method == 'POST':
        question = request.POST.get('question')
        q_type = request.POST.get('q_type')  # For q_type 1 is opened ended 2 Radio 3 is Checkbox 4 is Numeric and 5 is Date
        answers = request.POST.get('answers')
        question_order = request.POST.get('question_order')
        q_is_required = request.POST.get('q_is_required')
        q_date_validation = request.POST.get('date_validation')
        q_is_repeatable = request.POST.get('q_is_repeatable')
        
        parent_response = request.POST.get('parent_response')
        parent_question = request.POST.get('parent_question')

               
        if q_type == '1':
            answers = "Open Text"
        elif q_type == '4':
            answers = "Numeric"
        elif q_type == '5':
            answers = "Date"

        if q_date_validation == '':
            q_date_validation = None

        answers_list = answers.split(',')
        print(question, q_type, answers_list)
        
        trans_one = transaction.savepoint()
        q_save = Question.objects.create(question=question, question_type=q_type, created_by=user,
                                            questionnaire_id=q_id, question_order=question_order,is_required=q_is_required,
                                            date_validation = q_date_validation,
                                            is_repeatable = q_is_repeatable)
        
        question_id = q_save.pk

        if question_id:
            try:
                if parent_question and parent_response:
                    dep_question = QuestionDependance.objects.create(question_id=question_id, answer_id=parent_response)
                    dep_question.save()
                for f in answers_list:
                    fac_save = Answer.objects.create(question_id=question_id, created_by=user, option=f)
                    fac_save.save()
            except IntegrityError:
                transaction.savepoint_rollback(trans_one)
                return HttpResponse("error")
    if user.access_level.id == 2 and user.access_level.id != Questionnaire.objects.get(
            id=q_id).created_by.access_level.id:
        raise PermissionDenied
    if user.access_level.id == 5 and user.access_level.id != Questionnaire.objects.get(
            id=q_id).created_by.access_level.id:
        raise PermissionDenied
    if user.access_level.id == 4:
        raise PermissionDenied
    try:
        Questionnaire.objects.get(id=q_id)
    except Questionnaire.DoesNotExist:
        raise Http404('Questionnaire does not exist')
    questionnaire = Questionnaire.objects.get(id=q_id)
    question_number = []
    for i in range(1, questionnaire.number_of_questions + 1):
        question_number.append(i)
    question_order = Question.objects.filter(questionnaire_id=q_id).values_list('question_order', flat=True).order_by('question_order')
    questions = Question.objects.filter(questionnaire_id=q_id, question_type__in=[2, 3]).order_by('question_order')
    
    context = {
        'u': u,
        'questionnaire': q_id,
        'question_order': list(filterfalse(list(question_order).__contains__, question_number)),
        'questions': questions,
        
    }
    return render(request, 'survey/new_questions.html', context)


@login_required
def edit_question(request, q_id):
    user = request.user
    try:
        q = Question.objects.get(id=q_id)
        quest_id = Questionnaire.objects.get(id=q.questionnaire_id).id
        ans = Answer.objects.filter(question=q).values_list('option', flat=True)
        a = ','.join([str(elem) for elem in ans])
        print(a)
    except Question.DoesNotExist:
        raise Http404('Question does not exist')
    except Questionnaire.DoesNotExist:
        raise Http404('Questionnaire does not exist')
    if user.access_level.id == 2:
        if Questionnaire.objects.get(id=q.questionnaire_id).created_by.access_level.id == 3:
            raise PermissionDenied
    if user.access_level.id == 5:
        if Questionnaire.objects.get(id=q.questionnaire_id).created_by.access_level.id == 3:
            raise PermissionDenied
    if user.access_level.id == 4:
        raise PermissionDenied
    if request.method == 'POST':
        question = request.POST.get('question')
        q_type = request.POST.get('q_type')  # For q_type 1 is opened ended 2 Radio 3 is Checkbox
        answers = request.POST.get('answers')
        question_order = request.POST.get('question_order')
        q_is_required = request.POST.get('q_is_required')
        q_date_validation = request.POST.get('date_validation')
        q_is_repeatable = request.POST.get('q_is_repeatable')

        if q_date_validation == '':
            q_date_validation = None
        
        parent_response = request.POST.get('parent_response')
        parent_question = request.POST.get('parent_question')
        if q_type == '1':
            answers = "Open Text"
        elif q_type == '4':
            answers = "Numeric"
        elif q_type == '5':
            answers = "Date"
        answers_list = answers.split(',')

        print(question, q_type, answers_list)
        trans_one = transaction.savepoint()

        q.question = question
        q.question_type = q_type
        q.question_order = question_order
        q.is_required = q_is_required
        q.date_validation = q_date_validation
        q.is_repeatable = q_is_repeatable

        q.save()

        try:
            dep_question = QuestionDependance.objects.filter(question=q).delete()
            if parent_question and parent_response:
                dep_question = QuestionDependance.objects.create(question=q, answer_id=parent_response)
                dep_question.save()
            Answer.objects.filter(question=q).delete()
            for f in answers_list:
                fac_save = Answer.objects.create(question=q, created_by=user, option=f)
                fac_save.save()
        except IntegrityError:
            transaction.savepoint_rollback(trans_one)
            return HttpResponse("error")
    
    question_number = []
    questionnaire = Questionnaire.objects.get(id=quest_id)
    for i in range(1, questionnaire.number_of_questions + 1):
        question_number.append(i)
    question_dependance = QuestionDependance.objects.filter(question_id=q_id)
    # question_order = Question.objects.filter(questionnaire_id=q_id).values_list('question_order', flat=True).order_by('question_order')
    questions = Question.objects.filter(questionnaire_id=quest_id, question_type__in=[2, 3]).order_by('question_order')
    

    context = {
        'u': user,
        'q': q,
        'questionnaire': quest_id,
        'question_order': question_number,
        'question_dependance': question_dependance,
        'question_dependance_exists': question_dependance.exists(),
        'ans': a,
        'questions': questions,
    }
    return render(request, 'survey/edit_questions.html', context)

@login_required
def delete_question(request, q_id):
    user = request.user
    try:
        q = Question.objects.get(id=q_id)
        quest_id = Questionnaire.objects.get(id=q.questionnaire_id).id
        ans = Answer.objects.filter(question=q).values_list('option', flat=True)
        a = ','.join([str(elem) for elem in ans])
        print(a)
    except Question.DoesNotExist:
        raise Http404('Question does not exist')
    except Questionnaire.DoesNotExist:
        raise Http404('Questionnaire does not exist')
    if user.access_level.id == 2:
        if Questionnaire.objects.get(id=q.questionnaire_id).created_by.access_level.id == 3:
            raise PermissionDenied
    if user.access_level.id == 5:
        if Questionnaire.objects.get(id=q.questionnaire_id).created_by.access_level.id == 3:
            raise PermissionDenied
    if user.access_level.id == 4:
        raise PermissionDenied
    if request.method == 'POST':
        Response.objects.filter(question=q).delete()
        QuestionDependance.objects.filter(question=q).delete()
        Answer.objects.filter(question=q).delete()
        Question.objects.filter(question=q).delete()    

    context = {
        'u': user,
        'q': None,
        'questionnaire': quest_id,
    }
    return render(request, 'survey/question_list.html', context)

@login_required
def question_list(request, q_id):
    user = request.user
    u = user
    if user.access_level.id == 3:
        quest = Question.objects.filter(questionnaire_id=q_id).order_by('question_order')
        context = {
            'u': u,
            'quest': quest,
            'questionnaire': q_id,
        }
        print(quest)
        return render(request, 'survey/question_list.html', context)
    elif user.access_level.id == 2:
        try:
            quest = Question.objects.filter(questionnaire=Questionnaire.objects.get(id=q_id)).order_by('question_order')
        except Questionnaire.DoesNotExist:
            raise Http404("Questionnaire Does not exist")
        if Questionnaire.objects.get(id=q_id).created_by.access_level.id == 3:
            raise PermissionDenied

        context = {
            'u': u,
            'quest': quest,
            'questionnaire': q_id,
        }
        return render(request, 'survey/question_list.html', context)
    elif user.access_level.id == 5:
        try:
            quest = Question.objects.filter(questionnaire=Questionnaire.objects.get(id=q_id)).order_by('question_order')
        except Questionnaire.DoesNotExist:
            raise Http404("Questionnaire Does not exist")
        if Questionnaire.objects.get(id=q_id).created_by.access_level.id == 3:
            raise PermissionDenied

        context = {
            'u': u,
            'quest': quest,
            'questionnaire': q_id,
        }
        return render(request, 'survey/question_list.html', context)


@api_view(['GET'])
def answers_list(request, q_id):
    quest = Question.objects.get(id=q_id)
    queryset = Answer.objects.filter(question_id=quest)
    ser = AnswerSerializer(queryset, many=True)

    return Res(ser.data, status.HTTP_200_OK)
