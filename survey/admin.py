from django.contrib import admin
from import_export import resources
from .models import Questionnaire_Data
import json

# Register your models here.

class QuestionnaireDataResource(resources.ModelResource):

    class Meta:
        model = Questionnaire_Data
        # fields = ('questionnaire_id', 'mfl_code', 'ccc_number',)
        # exclude = ('id', )
        import_id_fields = ["questionnaire_id","mfl_code", "ccc_number"]
        # exclude = ('id',)
        skip_unchanged = True
        use_bulk = True



# admin.site.register(QuestionnaireDataResource)
