# Generated by Django 4.0.3 on 2022-03-31 01:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('balance', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Symbol',
            fields=[
                ('sym', models.CharField(max_length=5, primary_key=True, serialize=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('position_id', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('amount', models.IntegerField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.account')),
                ('sym', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.symbol')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('amount', models.IntegerField()),
                ('limit', models.FloatField()),
                ('status', models.CharField(default='open', max_length=50)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.account')),
                ('sym', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.symbol')),
            ],
        ),
    ]
