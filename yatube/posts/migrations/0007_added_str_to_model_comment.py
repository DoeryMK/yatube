# Generated by Django 2.2.16 on 2022-06-06 20:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_added_model_Comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created']},
        ),
    ]
