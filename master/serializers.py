from rest_framework import serializers 
from .models import Report, Post, Scheme, PostLike, PostComment, Announcement, Poll, Choice, Survey, Question, Answer, Voter
from user.serializers import UserSerializer,ProfileSerializer
 
class ReportSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Report
        fields = "__all__"
        
    def get_count(self, obj):
        return obj.reports.count()
        
class ReportStatusSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Report
        fields = ['status', 'mla_response']
        
class PostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = "__all__"
                
class PostSerializer(serializers.ModelSerializer):
    comments = PostCommentSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    user_profile = ProfileSerializer(source='user.profile', read_only=True)
    tags = serializers.SerializerMethodField()
    

    class Meta:
        model = Post
        fields = "__all__"

        
    def get_tags(self, obj):
        return [user.username for user in obj.tags.all()]
        

class SchemeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Scheme
        fields = "__all__"
        
        
class postLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = "__all__"
        
class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = "__all__"
        

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'votes', 'voters']

class PollSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'question', 'choices', 'total_votes']
        
    def get_total_votes(self, obj):
        return obj.get_total_votes()  
          
    # def get_vote_counts(self, obj):
    #     return obj.get_choice_vote_counts()

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        poll = Poll.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(poll=poll, **choice_data)
        return poll
    
    def update(self, instance, validated_data):
        choices_data = validated_data.pop('choices')
        chioces = instance.choices.all()
        chioces = list(chioces)
        instance.question = validated_data.get('question', instance.question)
        instance.save()
        for choice_data in choices_data:
            chioce = chioces.pop(0)
            chioce.text = choice_data.get('text', chioce.text)
            chioce.votes = choice_data.get('votes', chioce.votes)
            chioce.save()
        return instance



class AnswerSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=100)
    class Meta:
        model = Answer
        fields = ['id', 'text']

class QuestionSerializer(serializers.Serializer):
    text = serializers.CharField()
    answers = AnswerSerializer(many=True)

class SurveySerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    questions = QuestionSerializer(many=True)
    
    class Meta:
        model = Survey
        fields = ['id', 'title', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        survey = Survey.objects.create(**validated_data)

        for question_data in questions_data:
            answers_data = question_data.pop('answers')
            question = Question.objects.create(survey=survey, text=question_data['text'])

            for answer_data in answers_data:
                Answer.objects.create(question=question, text=answer_data['text'])

        return survey



# class EventSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Event
#         fields = ['id', 'event_name', 'start_datetime', 'end_datetime', 'description']
        
        

class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter
        fields = '__all__'
        
    def update(self, instance, validated_data):
        instance.is_updated = True
        return super().update(instance, validated_data)