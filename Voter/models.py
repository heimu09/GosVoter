from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from .constants import NOMINATIONS
from .utils import get_file_path
from cloudinary.models import CloudinaryField


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, full_name=None, position=None):
        if not phone:
            raise ValueError('Phone is required.')
        user = self.model(
            phone=phone, 
            full_name=full_name, 
            position=position,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password):
        superuser = self.create_user(phone=phone, password=password, full_name='Admin', position='Root')
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save(using=self._db)
        return superuser


class Voter(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=100)
    phone = PhoneNumberField(unique=True)
    position = models.CharField(max_length=255, null=True)
    votes = models.PositiveIntegerField(default=10, editable=False)
    journalist_certificate = CloudinaryField('image', null=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return f' {self.phone} {", " + self.full_name if self.full_name else ""}'

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Candidate(models.Model):
    full_name = models.CharField(max_length=100)
    photo = models.URLField()
    bio = models.TextField()

    def __str__(self) -> str:
        return f'{self.full_name}'

class Nomination(models.Model):
    candidate = models.ForeignKey(Candidate, related_name='nominations', on_delete=models.CASCADE)
    nomination = models.CharField(max_length=3, choices=NOMINATIONS)
    votes = models.PositiveIntegerField(default=0, null=False) 

    def __str__(self) -> str:
        return f'{self.nomination}: {self.candidate.full_name}'


class Material(models.Model):
    candidate = models.ForeignKey(Candidate, related_name='materials', on_delete=models.CASCADE)
    link = models.URLField(max_length=200)

    def __str__(self):
        return f'{self.link}: {self.candidate.full_name}'

    def save(self, *args, **kwargs):
        if self.candidate.materials.count() >= 5:
            raise ValidationError("У одного кандидата не может быть больше пяти материалов")
        super().save(*args, **kwargs)


class Vote(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    nomination = models.ForeignKey(Nomination, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('candidate', 'nomination')

    def __str__(self):
        return f'{self.voter.full_name} voted for {self.candidate.full_name}'
