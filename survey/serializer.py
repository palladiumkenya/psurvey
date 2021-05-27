from .models import *
from rest_framework import serializers, status
from rest_framework.response import Response as Res


class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = '__all__'



class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class QuestionResponseSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    class Meta:
        model = Answer
        fields = '__all__'


class StartQuestionnaireSerializer (serializers.ModelSerializer):
    class Meta:
        model = Started_Questionnaire
        fields = ('id')


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = '__all__'

    def validate(self, value):
        question = value['question']
        answer = value['answer']
        session = value['session']
        if End_Questionnaire.objects.filter(session=session).count() > 0:
            raise serializers.ValidationError({
                "success": False,
                "error": "Session already Ended"
            })

        if answer.question_id != question.id:
            serializer = QuestionSerializer(question)
            queryset = Answer.objects.filter(question=question)
            ans_ser = AnswerSerializer(queryset, many=True)
            raise serializers.ValidationError({
                "success": False,
                "error": "Response Provided not associated with Question",
                "Question": serializer.data,
                "Ans": ans_ser.data,
                "session_id": value['session'].id
            })
        else:
            return value


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'
