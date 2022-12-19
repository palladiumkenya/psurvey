from datetime import datetime

from django.db import models
from authApp.models import Facility, Users


class Questionnaire (models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=750)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    number_of_questions = models.IntegerField(default=1)
    active_till = models.DateField(default=datetime.now)
    target_app = models.CharField(max_length=45)

    class Meta:
        db_table = "Questionnaires"


class Question (models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    question =  models.CharField(max_length=500)
    allow_furure_date =  models.CharField(max_length=10, default="false")
    question_type = models.IntegerField()
    question_order = models.IntegerField(default=1)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE)


    class Meta:
        db_table = "Questions"

class Answer (models.Model):
    question= models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.CharField(max_length=455)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, default=1)

    class Meta:
        db_table = "Answers"


class QuestionDependance (models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='response_id')


    class Meta:
        db_table = "QuestionDependance"

class Questionnaire_Participants (models.Model):
    participant = models.CharField(max_length=100)
    require_ccc_number = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "Questionnaire_Participants"

class Started_Questionnaire (models.Model):
    ccc_number = models.CharField(max_length=15, null=True)
    firstname = models.CharField(max_length=300, null=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    questionnaire_participant = models.ForeignKey(Questionnaire_Participants, on_delete=models.CASCADE)
    started_by = models.ForeignKey(Users, on_delete=models.CASCADE, default=1)

    class Meta:
        db_table = "Started_Questionnaire"


class Response (models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True)
    open_text = models.CharField(max_length=150, blank=True, null=True)
    session = models.ForeignKey(Started_Questionnaire, on_delete=models.CASCADE, default=1)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "Responses"


class Patient_Consent(models.Model):
    ccc_number = models.CharField(max_length=15)
    informed_consent = models.BooleanField(default=True)
    privacy_policy = models.BooleanField(default=True)
    interviewer_statement = models.BooleanField(default=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

    class Meta:
        db_table = "PatientConsent"


class End_Questionnaire (models.Model):
    session = models.OneToOneField(Started_Questionnaire, on_delete=models.CASCADE, default=1)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, default=1)

    class Meta:
        db_table = "End_Questionnaire"


class Facility_Questionnaire (models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

    class Meta:
        db_table = "Facility_Questionnaire"


class Group (models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Groups"


class Group_Questionnaire (models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Group_Questionnaire"
