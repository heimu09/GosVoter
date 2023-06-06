from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import CustomTokenObtainPairView, UploadJournalistCertificateView, CandidateViewSet, NominationViewSet, MaterialViewSet, VoteViewSet, VoterCreateView

router = DefaultRouter()
router.register(r'materials', MaterialViewSet)
router.register(r'nominations', NominationViewSet)
router.register(r'candidates', CandidateViewSet)
router.register(r'votes', VoteViewSet, basename='vote')


urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # path('voter/', VoterCreateView.as_view()),
    path('upload-certificate/', UploadJournalistCertificateView.as_view(), name='upload-certificate'),
    path('', include(router.urls)),

]
