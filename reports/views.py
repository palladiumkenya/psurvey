from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response as Res
from datetime import date
from django.shortcuts import render
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from reports.serializer import *
from survey.models import *


@login_required
def index (request, q_id):
    user =  request.user
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

    queryset = Response.objects.filter(question_id=q_id).values('answer__option').annotate(count=Count('answer'))

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


def open_end (request, q_id):
    keywords = request.POST.get('keywords')
    print(keywords)
    words = keywords.replace(' ', '').split(',')

    labels = []
    data = []
    result = []
    for word in words:
        queryset = Response.objects.filter(question_id=q_id, open_text__icontains=word)
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


def pie_chart (request):
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


def users_report (request):
    return render(request, 'reports/user_report.html', {'u': request.user})


def patients_report (request):
    return render(request, 'reports/patient_report.html', {'u': request.user})


class Current_user(viewsets.ModelViewSet):
    serializer_class = AllUserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.access_level.id == 2:
            return Users.objects.filter(facility_id__in=Partner_Facility.objects.filter(
                partner__in=Partner_User.objects.filter(user=user).values_list('name', flat=True)).values_list('facility_id', flat=True), access_level_id=1)
        if user.access_level.id == 3:
            return Users.objects.filter(access_level_id=1)
        if user.access_level.id == 4:
            return Users.objects.filter(facility=user.facility, access_level_id=1)


    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(Q(designation__name__icontains=search) | Q(facility__name__icontains=search))

        return qs


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Patients (request):
    sq = Started_Questionnaire.objects.filter(started_by__facility=request.user.facility).order_by('ccc_number')
    print(sq)
    ser = PatientSer(sq, many=True)

    new_data = []
    not_found = True
    for item in ser.data:
        for month in new_data:
            not_found = True
            if item['ccc_number'] == month['ccc_number']:
                not_found = False
                month['responses'].append({'data': item['responses'], 'session': item['id']})

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
                if q.question.question_type == 1:
                    return qs.filter(open_text__icontains=search)
                else:
                    return qs.filter(answer__option__icontains=search)

        return qs

