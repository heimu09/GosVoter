from rest_framework import permissions, status, exceptions, generics, response, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import VoterSerializer, CustomTokenObtainPairSerializer, VoterCertificateSerializer, MaterialSerializer, CandidateSerializer, NominationSerializer, VoteSerializer
from .models import Candidate, Nomination, Material, Vote, Voter


def cast_vote(request, candidate_id, nomination):
    voter = request.user

    if not voter:
        return Response({"error": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if voter.votes < 1:
        return Response({"error": "У вас нет голосов для голосования"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        return Response({"error": "Голосуемый не найден"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        nomination = Nomination.objects.get(nomination=nomination, candidate=candidate)
    except Nomination.DoesNotExist:
        return Response({"error": "Номинация не найдена"}, status=status.HTTP_404_NOT_FOUND)
    
    if Vote.objects.filter(voter=voter, nomination__nomination=nomination.nomination).exists():
        return Response({"error": "Вы уже проголосовали в данной номинации"}, status=status.HTTP_400_BAD_REQUEST)

    vote = Vote(voter=voter, candidate=candidate, nomination=nomination)
    voter.votes -= 1
    nomination.votes += 1
    vote.save()
    voter.save()
    nomination.save()

    return Response({"message": "Голос успешно принят"}, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @swagger_auto_schema(
        operation_description="A custom login view with JWT authentication.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'journalist_certificate': openapi.Schema(type=openapi.TYPE_FILE, description='Journalist certificate'),
            },
        ),
        responses={200: VoterSerializer()},
    )
    def validate(self, attrs):
        data = super().validate(attrs)

        # authenticate the user
        voter = authenticate(self.context['request'], phone=attrs['phone'], password=attrs['password'])
        journalist_certificate = self.context['request'].data.get('journalist_certificate')
        print(journalist_certificate)
        if not voter:
            raise exceptions.AuthenticationFailed('Invalid login credentials')

        refresh = self.get_token(voter)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        return data


class UploadJournalistCertificateView(generics.UpdateAPIView):
    serializer_class = VoterCertificateSerializer
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_description="Upload journalist certificate.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'journalist_certificate': openapi.Schema(type=openapi.TYPE_FILE, description='Journalist certificate'),
            },
        ),
        responses={200: VoterCertificateSerializer()},
    )
    def patch(self, request, *args, **kwargs):
        if not self.request.user.journalist_certificate:
            return self.partial_update(request, *args, **kwargs)

        return response.Response({"message": "Удостоверение уже имеется"}, status=status.HTTP_400_BAD_REQUEST)


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [permissions.IsAuthenticated]


class NominationViewSet(viewsets.ModelViewSet):
    queryset = Nomination.objects.all()
    serializer_class = NominationSerializer
    permission_classes = [permissions.IsAuthenticated]


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated]


class VoteViewSet(viewsets.ViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a vote.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'voter_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the voter'),
                'nomination': openapi.Schema(type=openapi.TYPE_STRING, description='Nomination'),
            },
            required=['voter_id', 'nomination'],
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                },
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                },
            ),
        },
    )
    def create(self, request):
        serializer = VoteSerializer(data=request.data)

        if serializer.is_valid():
            candidate_id = serializer.validated_data['candidate_id']
            nomination = serializer.validated_data['nomination']

            result = cast_vote(request, candidate_id, nomination)

            return result

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VoterCreateView(generics.CreateAPIView):
    queryset = Voter.objects.all()
    serializer_class = VoterSerializer
    permission_classes = (permissions.AllowAny,)
