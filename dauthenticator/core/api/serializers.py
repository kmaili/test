import re
from django.contrib.auth import get_user_model
from rest_framework import serializers
from dauthenticator.core.models import AccountAuthentification, Driver

User = get_user_model()


class AccountAuthSerializer(serializers.Serializer):
    media = serializers.CharField(max_length=128, required=True)
    nb_jobs = serializers.CharField(max_length=128, required=True)



class AccountAuthentificationSerializer(serializers.ModelSerializer):

    media = serializers.CharField(max_length=128, write_only=True)
    login = serializers.EmailField(max_length=256)
    password = serializers.CharField(max_length=250)
    user_id = serializers.CharField(max_length=250)
    ip = serializers.CharField(max_length=128)
    client_name = serializers.CharField(max_length=128)
    cookie = serializers.CharField(allow_null=True)
    cookie_valid = serializers.BooleanField(default=False)
    cookie_start = serializers.DateTimeField(allow_null=True)
    cookie_expected_end = serializers.DateTimeField(allow_null=True)
    cookie_real_end = serializers.DateTimeField(allow_null=True)
    account_active = serializers.BooleanField(default=False)
    account_valid = serializers.BooleanField(default=False)

    def validate(self, attrs):
        return attrs

    class Meta:
        model = AccountAuthentification
        fields = "__all__"


class RevokeAccountAuthentificationSerializer(serializers.ModelSerializer):

    media = serializers.CharField(max_length=128, write_only=True)
    login = serializers.EmailField(max_length=256)

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def check_format_email(self, email):
        return re.fullmatch(self.regex, email)

    def validate(self, attrs):
        if not self.check_format_email(attrs['login']):
            raise serializers.ValidationError("Not an available account, please give an email")
        return attrs

    class Meta:
        model = AccountAuthentification
        fields = ["id"]


class AccountAuthentificationChangeStatusSerializer(serializers.ModelSerializer):

    media = serializers.CharField(max_length=128, write_only=True)
    login = serializers.EmailField(max_length=256)
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def check_format_email(self, email):
        return re.fullmatch(self.regex, email)

    def validate(self, attrs):
        if not self.check_format_email(attrs['login']):
            raise serializers.ValidationError("Not an available account, please check the format for input email")
        return attrs

    class Meta:
        model = AccountAuthentification
        fields = ["id"]


class AccountChangeStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountAuthentification
        fields = "__all__"


class DriverSerializer(serializers.ModelSerializer):

    driver_id = serializers.CharField(max_length=128)
    driver_name = serializers.CharField(max_length=256)
    class_name = serializers.CharField(max_length=250)
    import_package = serializers.CharField(max_length=250)
    strategy = serializers.CharField(max_length=250)

    def validate(self, attrs):
        return attrs

    class Meta:
        model = Driver
        fields = "__all__"