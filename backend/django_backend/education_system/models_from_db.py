# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Teachers(models.Model):
    id = models.BigIntegerField(primary_key=True)
    person_id = models.BigIntegerField(blank=True, null=True)
    user_id = models.BigIntegerField(blank=True, null=True)
    in_action_id = models.BigIntegerField(blank=True, null=True)
    in_action_date = models.TextField(blank=True, null=True)
    out_action_id = models.BigIntegerField(blank=True, null=True)
    out_action_date = models.TextField(blank=True, null=True)
    organization_id = models.BigIntegerField(blank=True, null=True)
    staff_type_id = models.BigIntegerField(blank=True, null=True)
    position_id = models.BigIntegerField(blank=True, null=True)
    contract_type_id = models.BigIntegerField(blank=True, null=True)
    teaching = models.SmallIntegerField(blank=True, null=True)
    card_number = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'teachers'


class Persons(models.Model):
    id = models.BigIntegerField(primary_key=True)
    firstname = models.TextField(blank=True, null=True)
    lastname = models.TextField(blank=True, null=True)
    patronymic = models.TextField(blank=True, null=True)
    gender_id = models.BigIntegerField(blank=True, null=True)
    pincode = models.TextField(blank=True, null=True)
    birthdate = models.TextField(blank=True, null=True)
    photo_file_id = models.BigIntegerField(blank=True, null=True)
    citizenship_id = models.BigIntegerField(blank=True, null=True)
    social_id = models.BigIntegerField(blank=True, null=True)
    marital_id = models.BigIntegerField(blank=True, null=True)
    orphan_id = models.BigIntegerField(blank=True, null=True)
    military_id = models.BigIntegerField(blank=True, null=True)
    nationality_id = models.BigIntegerField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)
    balance = models.TextField(blank=True, null=True)
    blood_type_id = models.BigIntegerField(blank=True, null=True)
    past_fevers = models.TextField(blank=True, null=True)
    hobbies = models.TextField(blank=True, null=True)
    sports = models.TextField(blank=True, null=True)
    family_information = models.TextField(blank=True, null=True)
    secondary_education_info = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'persons'


class Users(models.Model):
    id = models.BigIntegerField(primary_key=True)
    account_id = models.BigIntegerField(blank=True, null=True)
    organization_id = models.BigIntegerField(blank=True, null=True)
    is_blocked = models.SmallIntegerField(blank=True, null=True)
    user_type = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)
    group_id = models.BigIntegerField(blank=True, null=True)
    conversation_session = models.SmallIntegerField(blank=True, null=True)
    in_status = models.SmallIntegerField(blank=True, null=True)
    last_action_date = models.DateTimeField(blank=True, null=True)
    session_duration = models.SmallIntegerField(blank=True, null=True)
    access_ip_list = models.TextField(blank=True, null=True)
    favorite_tab = models.TextField(blank=True, null=True)
    level_id = models.BigIntegerField(blank=True, null=True)
    subscription_end_date = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'


class Accounts(models.Model):
    id = models.BigIntegerField(primary_key=True)
    person_id = models.BigIntegerField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    lang_id = models.BigIntegerField(blank=True, null=True)
    default_user_id = models.BigIntegerField(blank=True, null=True)
    in_system = models.SmallIntegerField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    other_username = models.TextField(blank=True, null=True)
    auth_type = models.SmallIntegerField(blank=True, null=True)
    fail_login_count = models.SmallIntegerField(blank=True, null=True)
    other_password = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'accounts'


class Organizations(models.Model):
    id = models.BigIntegerField(primary_key=True)
    type_id = models.BigIntegerField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    dictionary_name_id = models.BigIntegerField(blank=True, null=True)
    nod_level = models.IntegerField(blank=True, null=True)
    logo_name = models.IntegerField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organizations'


class Dictionaries(models.Model):
    id = models.BigIntegerField(primary_key=True)
    type_id = models.BigIntegerField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    order_by = models.IntegerField(blank=True, null=True)
    name_az = models.TextField(blank=True, null=True)
    name_en = models.TextField(blank=True, null=True)
    name_ru = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)
    icon = models.TextField(blank=True, null=True)
    short_name_az = models.TextField(blank=True, null=True)
    short_name_en = models.TextField(blank=True, null=True)
    short_name_ru = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dictionaries'


class DictionaryTypes(models.Model):
    id = models.BigIntegerField(primary_key=True)
    code = models.TextField(blank=True, null=True)
    name_az = models.TextField(blank=True, null=True)
    name_en = models.TextField(blank=True, null=True)
    name_ru = models.TextField(blank=True, null=True)
    hidden_status = models.IntegerField(blank=True, null=True)
    show_user_type = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dictionary_types'
