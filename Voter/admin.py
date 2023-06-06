from django.contrib import admin
from .models import Voter, Candidate, Nomination, Material, Vote

admin.site.register([Voter, Candidate, Nomination, Material, Vote])
