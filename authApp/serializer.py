from .models import *
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = '__all__'


class MyUserSerializer(UserSerializer):
    designation = DesignationSerializer(read_only=True)
    facility = FacilitySerializer(read_only=True)
    class Meta:
        model=Users
        fields = ['id', 'msisdn', 'email', 'f_name', 'l_name', 'designation', 'facility']


class MyUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Users
        fields = ['id', 'msisdn', 'password', 'email', 'f_name', 'l_name', 'designation', 'facility', 'access_level']
