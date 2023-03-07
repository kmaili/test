# Generated by Django 3.1.12 on 2023-02-06 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('driver_id', models.CharField(max_length=256)),
                ('driver_name', models.CharField(max_length=256)),
                ('class_name', models.CharField(max_length=256)),
                ('import_package', models.CharField(max_length=256)),
            ],
        ),
        migrations.AlterField(
            model_name='accountauthentification',
            name='media',
            field=models.CharField(choices=[('twitter', 1), ('instagram', 2), ('facebook', 3), ('quora', 4)], default='twitter', max_length=128),
        ),
    ]
