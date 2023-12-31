from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http.response import JsonResponse
from rest_framework.response import Response
from rest_framework.parsers import JSONParser 
from rest_framework import status, viewsets
from rest_framework.views import APIView
from .models import Report, Post, Scheme, PostLike, PostComment, Announcement, Poll, Choice,UserVote, Survey, Question, Answer, Voter
from .serializers import ReportSerializer,postLikeSerializer,SchemeSerializer,PostSerializer, PostCommentSerializer, AnnouncementSerializer, PollSerializer, ChoiceSerializer, SurveySerializer, QuestionSerializer, AnswerSerializer, ReportStatusSerializer,VoterSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from user.permissions import IsRegularUser, IsSuperuser
from user.models import Profile, CustomUser
import requests
from rest_framework import generics
import pandas as pd
from tablib import Dataset
from rest_framework.parsers import FileUploadParser,MultiPartParser
from openpyxl import Workbook
from django.http import HttpResponse, FileResponse
from api.models import PollingStation, Constituency
import xlwt


# Create your views here.

        
from import_export import resources

class VoterResource(resources.ModelResource):

    class Meta:
        model = Voter
        import_id_fields = ["booth_no", "voterId_no"]
        skip_unchanged = True
        use_bulk = True
        
        
class ReportListCreateView(generics.ListCreateAPIView):
    queryset = Report.objects.all().order_by('-id')
    serializer_class = ReportSerializer
    
    # def get_queryset(self):
    #     queryset = Report.objects.all()
    #     status = self.request.GET.get('status', None)
    #     count = queryset.count()
    #     self.count = count
    #     if status:
    #         return Report.objects.filter(status=status).order_by('-id')
    #     else:
    #         return Report.objects.all().order_by('-id')
    #     return queryset

    def list(self, request, *args, **kwargs):
        permission_classes = [IsAuthenticated]
        admin_constituency = request.user.constituency
        print(admin_constituency)
        admin_user = CustomUser.objects.filter(constituency=admin_constituency, roles='voter')
        print('############',admin_user)
        user_ids = admin_user.values_list('id', flat=True)
        print('user_ids', user_ids)
        user_reports = Report.objects.filter(user__id__in=user_ids)
        user_reports_serializer = ReportSerializer(user_reports, many=True)

        response_data = {
            'reports': user_reports_serializer.data,
        }
        return Response(response_data)
        
    def perform_create(self, serializer):
        permission_classes = [IsAuthenticated]
        serializer.save(user=self.request.user)
        
class ReportListCountView(APIView):
    
    def get(self, request):
        permission_classes = [IsAuthenticated]
        admin_constituency = request.user.constituency
        admin_user = CustomUser.objects.filter(constituency=admin_constituency, roles='voter')
        user_ids = admin_user.values_list('id', flat=True)
        user_reports = Report.objects.filter(user__id__in=user_ids)
        total_reports = user_reports.count()
        pending_reports = user_reports.filter(status='pending').count()
        solved_reports = user_reports.filter(status='solved').count()
        failed_reports = user_reports.filter(status='failed').count()
        response_data = {
            'total_reports':total_reports,
            'pending_reports':pending_reports,
            'solved_reports':solved_reports,
            'failed_reports':failed_reports
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
# def report_count(request):
#     count = Report.objects.count()
#     return Response({'count':count})
        
class ReportRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    # permission_classes = [IsAuthenticated]


@api_view(['PATCH', ])
@permission_classes([IsAuthenticated])
def report_status_update(request, id):
    try:
        report = Report.objects.get(id=id)
        report_user = report.user
        user_fcm = Profile.objects.get(user=report.user)
        print(user_fcm.fcm_token)
    except Report.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ReportStatusSerializer(report, data=request.data)
    if serializer.is_valid():
        new_status = serializer.validated_data.get('status')
        
        response_messages = {
            'solved': "Dear Sir/Madam, Your reported problem is solved.",
            'pending': "Dear Sir/Madam, Your reported problem is currently in progress.",
            'failed': "Dear Sir/Madam, Your reported problem is failed.",
        }

        serializer.validated_data['mla_response'] = response_messages.get(new_status, "")

        serializer.save()
        message = {"success": "Update Successful"}
        
        # Send a notification using FCM with your FCM authorization key
        fcm_api_key = 'AAAAg_vupFQ:APA91bGe8g4QJJhSLVidujCJxlhu5IXZNraltSq8Z5wPoEhWC2k5GWkm6YlBj-CagpBNp09i8phsFf96WxnkD3-d2M2Q8LuLfbNLAir5xU52WHh9GfDNHxjBIQSfqm0ezwaWDYwf1muX'
        fcm_endpoint = 'https://fcm.googleapis.com/fcm/send'
        
        headers = {
            'Authorization': f'key={fcm_api_key}',
            'Content-Type': 'application/json',
        }

        # Create a notification payload
        notification_payload = {
            'to': user_fcm.fcm_token,
            'notification': {
                'title': 'Report status',
                'body': serializer.data['mla_response'],
            },
            'data': {
            },
        }

        # Send the notification
        response = requests.post(fcm_endpoint, json=notification_payload, headers=headers)
        
        return Response({"message": message, "data": serializer.data}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserReportsView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]       
    
    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).order_by('-id')
    
    
class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-id')
    serializer_class = PostSerializer
    
    def perform_create(self, serializer):
        permission_classes = [IsAuthenticated]
        serializer.save(user=self.request.user)
        
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def getUserReports(request):
#     user = request.user
    
#     reports = Report.objects.filter(user=user)
#     serializer = ReportSerializer(reports)
#     return Response({"message": "User  added reports.", "data":serializer.data}, status=status.HTTP_201_CREATED)

class PostRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_update(self, serializer):
        if serializer.instance.user == self.request.user:
            serializer.save()
        else:
            raise PermissionDenied("You don't have permission to update this post.")

    def perform_destroy(self, instance):
        if instance.user == self.request.user:
            instance.delete()
            return Response({"message": "Post deleted successfully"}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied("You don't have permission to delete this post.")
    
class SchemaListCreateView(generics.ListCreateAPIView):
    queryset = Scheme.objects.all().order_by('-id')
    serializer_class = SchemeSerializer
    
    
    def perform_create(self, serializer):
        permission_classes = [IsAuthenticated]
        serializer.save(user=self.request.user)

class SchemaRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer
    permission_classes = [IsAuthenticated]
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except post.DoesNotExist:
        return Response({"message": "post not found."}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    existing_like = PostLike.objects.filter(user=user, post=post).first()
    
    if existing_like:
        existing_like.delete()
        message = "You have unliked the post."
    else:
        PostLike.objects.create(user=user, post=post)
        message = "You have liked the post."
   
    post.likes = PostLike.objects.filter(post=post, is_like=True).count()
    post.save()
    serializer = PostSerializer(post)
    return Response({"message": message, "data":serializer.data}, status=status.HTTP_201_CREATED)

from django.contrib.auth.decorators import login_required

class UserLikedPostsView(generics.ListAPIView):
    serializer_class = postLikeSerializer
    permission_classes = [IsAuthenticated]       
    
    def get_queryset(self):
        return PostLike.objects.filter(user=self.request.user).order_by('-id')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except post.DoesNotExist:
        return Response({"message": "post not found."}, status=status.HTTP_404_NOT_FOUND)

    content = request.data.get('content', None)
    if not content:
        return Response({"message": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)

    comment = PostComment.objects.create(user=request.user, post=post, content=content)
    serializer = PostCommentSerializer(comment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)



class AnnouncementListCreateView(generics.ListCreateAPIView):
    queryset = Announcement.objects.all().order_by('-id')
    serializer_class = AnnouncementSerializer
    
    
    def perform_create(self, serializer):
        permission_classes = [IsAuthenticated]
        serializer.save(user=self.request.user)

class AnnouncementRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    
    
class PollList(generics.ListCreateAPIView):
    queryset = Poll.objects.all().order_by('-id')
    serializer_class = PollSerializer

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data, many=isinstance(request.data, list))
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PollRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
  
    
class VoteView(generics.UpdateAPIView):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        choice = self.get_object()
        user = request.user

        if UserVote.objects.filter(user=user, choice=choice).exists():
            raise PermissionDenied("You have already voted for this choice.")
        
        if UserVote.objects.filter(user=user, choice__poll=choice.poll).exists():
            raise PermissionDenied("You can only vote for one choice in this poll.")
        # if user in choice.voters.all():
        #     raise PermissionDenied("You have already voted for this choice.")
        
        # if user.choices.filter(poll=choice.poll).exists():
        #     raise PermissionDenied("You can only vote for one choice in this poll.")

        choice.votes += 1
        choice.voters.add(user)
        choice.save()
        
        UserVote.objects.create(user=user, choice=choice)
        
        return Response({"message": "Vote recorded successfully"}, status=status.HTTP_200_OK)


class SurveyList(generics.ListCreateAPIView):
    queryset = Survey.objects.all().order_by('-id')
    serializer_class = SurveySerializer


class SurveyDetail(generics.RetrieveAPIView):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

class QuestionDetail(generics.RetrieveAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class AnswerDetail(generics.RetrieveAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    

    


class VoterUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request):
        uploaded_file = request.data.get('file')
        constituency = request.data.get('constituency')
        print(constituency)

        if not uploaded_file.name.endswith('.xlsx'):
            return Response({'message': 'Invalid file format. Please upload an Excel file.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            constituency_obj = Constituency.objects.get(id=constituency)

            # if constituency_obj.is_uploded:
            #     return Response({'message': f'Constituency "{constituency}" has already been updated.'}, status=status.HTTP_400_BAD_REQUEST)
            
            df = pd.read_excel(uploaded_file, engine='openpyxl')

            df = df.where(pd.notna(df), None)

            column_mapping = {"Booth No": "booth_no", "Sno": "sl_no","VoterName": "name","Surname": "surname","Address": "address","Village": "village","Voter Id Number": "voterId_no"}

            df.rename(columns=column_mapping, inplace=True)
            
            df['constituency'] = constituency
            df['is_uploded'] = True
            
            data_to_import = df.to_dict(orient='records')
            serializer = VoterSerializer(data=data_to_import, many=True)

            if serializer.is_valid():
                serializer.save()
                constituency_obj.is_uploded = True
                constituency_obj.save()
                return Response({'message': 'Data from Excel file imported successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Constituency.DoesNotExist:
            return Response({'message': f'Polling station "{constituency}" does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'message': f'Error processing Excel file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        

class VoterReUploadView(APIView):
    parser_classes = (MultiPartParser,)
    print('kalki')

    def post(self, request):
        uploaded_file = request.data.get('file')
        constituency = request.data.get('constituency')
        print(constituency)

        if not uploaded_file.name.endswith('.xlsx'):
            return Response({'message': 'Invalid file format. Please upload an Excel file.'}, status=status.HTTP_400_BAD_REQUEST)

        try:            
            df = pd.read_excel(uploaded_file, engine='openpyxl')

            column_mapping = {"Booth No": "booth_no", "Sno": "sl_no","VoterName": "name","Surname": "surname","Address": "address","Village": "village","Voter Id Number": "voterId_no"}

            df.rename(columns=column_mapping, inplace=True)
            
            df['constituency'] = constituency

            data_to_import = df.to_dict(orient='records')
            serializer = VoterSerializer(data=data_to_import, many=True)

            if serializer.is_valid():
                serializer.save()

                return Response({'message': 'Data from Excel file imported successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'message': f'Error processing Excel file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)  
   
# class VotersListDownloadView(APIView):
    
#     def get(self, request):
#         # polling_station = request.data.get('polling_station')
#         data = Voter.objects.filter(is_updated=True)
#         print(data)
#         wb = Workbook()
#         ws = wb.active

#         ws.append(['SL.No', 'Name', 'Surname', 'Gender', 'Age' 'Voter ID', 'Address'])

#         for voter in data:
#             ws.append([voter.sl_no, voter.name, voter.surname, voter.gender, voter.age, voter.voterId_no, voter.address])


#         response = HttpResponse(content_type='application/ms-excel')
#         response['Content-Disposition'] = 'attachment; filename="voters_list.xlsx"'
#         wb.save(response)
#         print(response)
#         return response

def VotersListDownloadView(request):
    
    # polling_station = get_object_or_404(PollingStation, id=polling_station)
    village = request.GET.get('village', None)
    print(village)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=voters_list.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Contractors Data')
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['SL.No', 'Booth No', 'Name', 'Surname', 'Gender', 'Age', 'Voter ID', 'Address', 'Village', 'Caste', 'Mobile No', 'Occupation', 'Resident', 'Party', 'Joint Family', 'Benificers', 'Remarks', 'PartNameEn', 'Image', 'Latitude', 'Longitude']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style) 

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = Voter.objects.filter(is_updated=True,village=village).values_list('sl_no', 'polling_station', 'name', 'surname', 'gender', 'age', 'voterId_no', 'address', 'village', 'caste', 'mobile', 'occupation', 'resident', 'party', 'joint_family', 'benificers', 'remarks', 'partNameEn', 'image', 'latitude','longitude')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    
    wb.save(response)

    return response
    
class VoterList(generics.ListAPIView):
    queryset = Voter.objects.all()
    serializer_class = VoterSerializer
    
    def get_queryset(self):
        village = self.request.GET.get('village')
        # polling_station = self.request.GET.get('polling_station')
        # print(polling_station)
        return Voter.objects.filter(is_updated=True,village=village)    
        
class VoterListCreate(generics.ListCreateAPIView):
    queryset = Voter.objects.all()
    serializer_class = VoterSerializer
    
    def get_queryset(self):
        queryset = Voter.objects.all()
        voterId = self.request.GET.get('voter_id', None)
        voterName = self.request.GET.get('name', None)
        if voterId:
            return Voter.objects.filter(voterId_no__icontains=voterId)
        elif voterName:
            return Voter.objects.filter(name__icontains=voterName)
        else:
            return Voter.objects.all()
        return queryset
    
class VoterRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Voter.objects.all()
    serializer_class = VoterSerializer
    # permission_classes = [IsAuthenticated]
    
class VillagesByConstituencyView(APIView):
    def get(self, request):
        try:
            constituency_id = self.request.GET.get('constituency_id', None)
            villages_list = list(set(Voter.objects.values_list('village', flat=True)))
            filtered_list = list(filter(lambda item: item is not None, villages_list))

            return Response({'villages':filtered_list}, status=status.HTTP_200_OK)
        except Voter.DoesNotExist:
            return Response({'message': 'Villages not found for the given constituency.'}, status=status.HTTP_404_NOT_FOUND)
        
        
class UniqueVoterListView(APIView):
    def get(self, request):
        try:
            constituency_id = self.request.GET.get('constituency_id', None)
            voter_by_constituency = Voter.objects.filter(constituency=constituency_id)
            voters_list = voter_by_constituency.values('village', 'booth_no').distinct()
            filtered_voters_data = [item for item in voters_list if item['village'] is not None]


            return Response(filtered_voters_data, status=status.HTTP_200_OK)
        except Voter.DoesNotExist:
            return Response({'message': 'No voters found.'}, status=status.HTTP_404_NOT_FOUND)