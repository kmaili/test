# Generated by Django 3.2.15 on 2024-06-06 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_accountauthentification_consumption_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountauthentification',
            name='media',
            field=models.CharField(choices=[('twitter', 1), ('instagram', 2), ('facebook', 3), ('quora', 4), ('adoasis', 5), ('tumblr', 6), ('facebook_scraper', 7), ('youtube', 8), ('threads', 9)], default='twitter', max_length=128),
        ),
    ]
