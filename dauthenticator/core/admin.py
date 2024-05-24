from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import AccountAuthentification, AirflowDAGRUN, Driver


@admin.register(AccountAuthentification)
class AccountAuthentificationAdmin(ImportExportModelAdmin):
    list_display = ('id',
                    'client_name',
                    'login',
                    'password',
                    'ip',
                    'user_id',
                    'media',
                    'cookie',
                    'issue',
                    'cookie_valid',
                    'cookie_start',
                    'cookie_expected_end',
                    'cookie_real_end',
                    'consumption_time',
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


@admin.register(Driver)
class DriverAdmin(ImportExportModelAdmin):
    list_display = ("id", "driver_id", "driver_name", "import_package", "class_name","strategy")

    def save_model(self, request, obj, form, change):
        obj.save()

    # readonly_fields = ("dag_run_id", "start", "end", "session")
