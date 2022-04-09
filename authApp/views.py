from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from psycopg2._psycopg import IntegrityError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, views
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response as Res
from rest_framework.views import APIView
from datetime import date

from .forms import LoginForm
from .serializer import *
from .models import *
from survey.models import *


# api
@api_view(['GET'])
def facilities(request):
    if request.method == "GET":
        queryset = Facility.objects.all()
        serializer = FacilitySerializer(queryset, many=True)
        return Res(data={"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def counties(request):
    if request.method == "GET":
        queryset = Facility.objects.all().distinct('county')
        serializer = FacilitySerializer(queryset, many=True)
        return Res(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def facility_single(request):
    if request.method == "POST":
        queryset = Facility.objects.get(id=request.data['id'])
        serializer = FacilitySerializer(queryset)
        return Res(data={"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def designation(request):
    if request.method == "GET":
        queryset = Designation.objects.all()
        serializer = DesignationSerializer(queryset, many=True)
        return Res({"data": serializer.data}, status=status.HTTP_200_OK)




# Web
def web_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            clean = form.cleaned_data
            user = authenticate(username=clean['msisdn'], password=clean['password'])
            print(user)
            if user is not None:
                if user.is_active:
                    if user.access_level.id != 1:
                        login(request, user)
                        return HttpResponse('/web/dashboard')
                    else:
                        return HttpResponse('Not an admin')
                else:
                    return HttpResponse('Account is Disabled')
            else:
                return HttpResponse("invalid credentials")
    else:
        form = LoginForm()
    return render(request, "authApp/login.html", {'form': form})


@login_required
def designation_list(request):
    user = request.user
    if request.user.access_level.id != 3:
        raise PermissionDenied
    designation = Designation.objects.all()
    context = {
        'u': user,
        'desig': designation
    }
    return render(request, 'authApp/desigantion_list.html', context)


@login_required
def facility_partner_list(request):
    user = request.user
    if user.access_level.id != 3:
        raise PermissionDenied
    partner = Partner.objects.all().order_by('-created_at')
    page = request.GET.get('page', 1)
    paginator = Paginator(partner, 10)
    try:
        partner = paginator.page(page)
    except PageNotAnInteger:
        partner = paginator.page(1)
    except EmptyPage:
        partner = paginator.page(paginator.num_pages)
    context = {
        'u': user,
        'partner': partner,
        'paginator': paginator,
    }
    return render(request, 'authApp/partner_facility_list.html', context)


@login_required
def facility_admin_list(request):
    user = request.user
    if user.access_level.id != 2:
        raise PermissionDenied
    partner = Users.objects.filter(access_level_id=4,
                                   facility_id__in=Partner_Facility.objects.filter(partner_id=Partner_User.objects.get(user=user).name).values_list('facility_id', flat=True)).order_by('-date_joined')
    print(partner)
    page = request.GET.get('page', 1)
    paginator = Paginator(partner, 10)
    try:
        partner = paginator.page(page)
    except PageNotAnInteger:
        partner = paginator.page(1)
    except EmptyPage:
        partner = paginator.page(paginator.num_pages)
    context = {
        'u': user,
        'partner': partner,
        'paginator': paginator,
    }
    return render(request, 'authApp/facility_admin_list.html', context)


@login_required
def facility_partner_link(request):
    user = request.user
    if user.access_level.id != 3:
        raise PermissionDenied
    par_fac = Partner_Facility.objects.all()
    facilities = Facility.objects.all().exclude(id__in=par_fac.values_list('facility_id', flat=True))

    if request.method == 'POST':
        fac = request.POST.getlist('facility')
        partner = request.POST.get('partner')

        trans_one = transaction.savepoint()
        try:
            create_part = Partner.objects.create(name=partner, created_by=user)
            create_part.save()
            for i in fac:
                p_user = Partner_Facility.objects.create(facility_id=i, partner_id=create_part.pk)
                p_user.save()
        except IntegrityError:
            transaction.savepoint_rollback(trans_one)
            return HttpResponse("error")
        except Exception:
            transaction.savepoint_rollback(trans_one)
            return HttpResponse("error")
            

    partner_users = Partner.objects.all()
    context = {
        'u': user,
        'fac': facilities,
        'p_users': partner_users,
    }
    return render(request, 'authApp/new_partner_link.html', context)


@login_required
def register_partner(request):
    u = request.user
    if request.user.access_level.id != 3:
        raise PermissionDenied
    if request.user.access_level.id == 3:
        facilities = Facility.objects.filter().order_by('county', 'sub_county', 'name')
    else:
        facilities = Facility.objects.exclude(id__in=Partner_Facility.objects.values_list('facility_id', flat=True)).order_by('county', 'sub_county', 'name')
    if request.method == 'POST':
        trans_one = transaction.savepoint()
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        email = request.POST.get('email')
        msisdn = request.POST.get('msisdn')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')
        partner = request.POST.get('partner-user')
        if password != re_password:
            return HttpResponse("Password error")
        user = Users.objects.create_user(msisdn=msisdn, password=password, email=email)
        user.f_name = f_name
        user.l_name = l_name
        user.access_level_id = 2
        user.save()
        try:
            if user.pk:
                admin = Partner_User.objects.create(name_id=partner, user=user, created_by=u)
                admin.save()
        except IntegrityError:
            transaction.savepoint_rollback(trans_one)
            return HttpResponse("error")

    partner_users = Partner.objects.all()
    for p in partner_users:
        print(p)
    context = {
        'u': u,
        'fac': facilities,
        'p_users': partner_users,
    }
    return render(request, 'authApp/new_partner_link.html', context)


@login_required
# @permission_required('survey.add_users')
def register_partner_user(request):
    u = request.user
    if u.access_level.id == 5:
        if not request.user.has_perm('survey.view_users'):
            raise PermissionDenied
    elif u.access_level.id != 2:
        raise PermissionDenied
    if request.method == 'POST':
        trans_one = transaction.savepoint()
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        email = request.POST.get('email')
        msisdn = request.POST.get('msisdn')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')
        partner = request.POST.getlist('partner-user')
        if password != re_password:
            return HttpResponse("Password error")
        print(partner)
        user = Users.objects.create_user(msisdn=msisdn, password=password, email=email)
        user.f_name = f_name
        user.l_name = l_name
        user.access_level_id = 5
        print(user.id)
        user.save()
        try:
            admin = Partner_User.objects.create(name=Partner_User.objects.get(user=u).name, user=user, created_by=u)
            admin.save()
            for par in partner:
                user.user_permissions.add(Permission.objects.get(id=par))
                user.user_permissions.all()
        except IntegrityError:
            transaction.savepoint_rollback(trans_one)
            return HttpResponse("error")

    partner_users = Partner_User.objects.filter(name=Partner_User.objects.get(user=u).name, user__access_level__id=5)
    perm = Permission.objects.filter(Q(name__contains='Can add questionnaire') |
                                     Q(name__contains='Can change questionnaire') |
                                     Q(name__contains='Can delete questionnaire') |
                                     Q(name__contains='Can view questionnaire') |
                                     Q(name__exact='Can add partner') |
                                     Q(name__exact='Can change partner') |
                                     Q(name__exact='Can delete partner') |
                                     Q(name__exact='Can view partner') )
                                     # | Q(name__contains=''))

    context = {
        'u': u,
        'perm': perm,
        'p_users': partner_users,
    }
    return render(request, 'authApp/new_partner_user.html', context)


@login_required
def register_fac_admin(request):
    u = request.user
    if request.user.access_level.id != 2:
        raise PermissionDenied
    facilities = Facility.objects.filter(id__in=Partner_Facility.objects.filter(
        partner=Partner_User.objects.get(user=u).name).values_list('facility_id', flat=True)).order_by('name')
    if request.method == 'POST':
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        email = request.POST.get('email')
        msisdn = request.POST.get('msisdn')
        facility = request.POST.get('facility')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')
        if password != re_password:
            return HttpResponse("Password error")
        user = Users.objects.create_user(msisdn=msisdn, password=password, email=email)
        user.f_name = f_name
        user.l_name = l_name
        user.access_level_id = 4
        user.facility_id=facility
        print(user.id)
        user.save()

    context = {
        'u': u,
        'fac': facilities,
    }
    return render(request, 'authApp/new_fac_admin.html', context)


@login_required
def edit_partner(request, p_id):
    user = request.user
    if user.access_level.id == 2:
        raise PermissionDenied
    part = Partner.objects.get(id=p_id)
    par_fac = Partner_Facility.objects.all()
    facilities = Facility.objects.all().exclude(id__in=par_fac.values_list('facility_id', flat=True))
    selected = Facility.objects.filter(
        id__in=Partner_Facility.objects.filter(partner=part).values_list('facility_id', flat=True))

    if request.method == 'POST':
        fac = request.POST.getlist('facility')
        partner = request.POST.get('partner')

        trans_one = transaction.savepoint()
        try:
            part.name = partner
            part.save()
            fac_init = Partner_Facility.objects.filter(partner=part)
            fac_init.delete()
            for i in fac:
                p_user = Partner_Facility.objects.create(facility_id=i, created_by=user, partner_id=part.pk)
                p_user.save()
        except IntegrityError:
            transaction.savepoint_rollback(trans_one)
            return HttpResponse("error")

    context = {
        'u': user,
        'selected': selected,
        'fac': facilities,
        'pa': part,
        'p_id': p_id,

    }
    return render(request, 'authApp/edit_partner_link.html', context)


@login_required
def profile(request):
    u = request.user
    if u.access_level.id == 2:
        partner = Partner.objects.get(id=Partner_User.objects.get(user=u).name_id)
    else:
        partner = 1
    if request.method == "POST":
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        email = request.POST.get('email')
        msisdn = request.POST.get('msisdn')
        try:
            user = Users.objects.get(id=u.id)
            user.f_name = f_name
            user.l_name = l_name
            user.email = email
            user.msisdn = msisdn
            user.save()
        except IntegrityError:
            return 'error'

    context = {
        'u': u,
        'p': partner,
    }
    return render(request, 'authApp/profile.html', context)


def logout_request(request):
    logout(request)
    messages.info(request, "User is logged out", fail_silently=True)
    return redirect('web-login')
