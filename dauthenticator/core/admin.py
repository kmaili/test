from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import AccountAuthentification, AirflowDAGRUN


@admin.register(AccountAuthentification)
class AccountAuthentificationAdmin(ImportExportModelAdmin):
    list_display = ('id',
                    'login',
                    'password',
                    'ip',
                    'user_id',
                    'media',
                    'cookie',
                    'cookie_valid',
                    'cookie_start',
                    'cookie_expected_end',
                    'cookie_real_end',
                    'account_active',
                    'account_valid',
                    'created_at',
                    'modified_at')

    def save_model(self, request, obj, form, change):
        obj.save()

    readonly_fields = ('login', 'password', 'user_id')


@admin.register(AirflowDAGRUN)
class AirflowDAGRUNAdmin(ImportExportModelAdmin):
    list_display = ("id", "dag_run_id", "start", "end", "session")

    def save_model(self, request, obj, form, change):
        obj.save()

    readonly_fields = ("dag_run_id", "start", "end", "session")
