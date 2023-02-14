# from pyexpat import model
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountAuthentification(models.Model):

    MEDIA_CHOICES = (
        ('twitter', 1),
        ('instagram', 2),
        ('facebook', 3),
        ('quora', 4),
        ('adoasis', 5)
    )
    login = models.EmailField(max_length=256)
    password = models.CharField(max_length=250)
    user_id = models.CharField(max_length=250)
    media = models.CharField(max_length=128, choices=MEDIA_CHOICES, default='twitter', null=False, blank=False)
    active = models.BooleanField(default=True)
    ip = models.CharField(max_length=128)
    cookie = models.TextField(null=True)
    cookie_valid = models.BooleanField(default=False)
    cookie_start = models.DateTimeField(null=True, blank=True)
    cookie_expected_end = models.DateTimeField(null=True, blank=True)
    cookie_real_end = models.DateTimeField(null=True, blank=True)
    account_active = models.BooleanField(default=False)
    account_valid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['user_id', 'media'], name="user_id_media_unique")
            ]
    def __str__(self):
        return f"[AccountsAuthentification={str(self.user_id)}]"



class AirflowDAGRUN(models.Model):

    dag_run_id = models.CharField(max_length=256)
    session = models.ForeignKey("AccountAuthentification", on_delete=models.CASCADE)
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[AirflowDAGRUN={str(self.dag_run_id)}]"


class Driver(models.Model):

    driver_id = models.CharField(max_length=256)
    driver_name = models.CharField(max_length=256)
    class_name = models.CharField(max_length=256)
    import_package = models.CharField(max_length=256)
    strategy = models.CharField(max_length=256,default="strategy1")

    def __str__(self):
        return f"[Driver={str(self.driver_id)}]"