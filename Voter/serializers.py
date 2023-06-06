from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Candidate, Nomination, Material, Voter


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Добавьте свои собственные поля
        token['phone'] = str(user.phone)
        token['user_id'] = user.id

        return token


class VoterCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter
        fields = ['journalist_certificate']


class NominationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomination
        fields = '__all__'


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class CandidateSerializer(serializers.ModelSerializer):
    nominations = NominationSerializer(many=True, read_only=True)
    materials = MaterialSerializer(many=True, read_only=True)

    class Meta:
        model = Candidate
        fields = ['id', 'full_name', 'photo', 'bio', 
                  'nominations', 'materials']


class VoterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Voter
        fields = ['id', 'full_name', 'phone', 'position', 'votes', 'password']
        read_only_fields = ['votes']

    def create(self, validated_data):
        voter = Voter.objects.create_user(**validated_data)
        voter.save()
        return voter

class VoteSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField()
    nomination = serializers.CharField(max_length=3)