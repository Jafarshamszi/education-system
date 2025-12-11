from django.db import models
from django.contrib.auth.models import AbstractUser


class DictionaryType(models.Model):
    """Dictionary type model"""
    id = models.BigAutoField(primary_key=True)
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

    def __str__(self):
        return self.name_en or self.name_az or self.code or str(self.id)


class Dictionary(models.Model):
    """Dictionary model for all lookup values"""
    id = models.BigAutoField(primary_key=True)
    type = models.ForeignKey(DictionaryType, on_delete=models.CASCADE, 
                           db_column='type_id', blank=True, null=True)
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

    def __str__(self):
        return self.name_en or self.name_az or self.code or str(self.id)


class Organization(models.Model):
    """Organization model"""
    id = models.BigAutoField(primary_key=True)
    type_id = models.BigIntegerField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    dictionary_name = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                       db_column='dictionary_name_id', blank=True, null=True,
                                       related_name='organizations_by_name')
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

    @property
    def name(self):
        if self.dictionary_name:
            return self.dictionary_name.name_en or self.dictionary_name.name_az or self.dictionary_name.name_ru or "Unknown"
        return "Unknown"

    def __str__(self):
        return self.name


class Person(models.Model):
    """Person model containing personal information"""
    id = models.BigAutoField(primary_key=True)
    firstname = models.TextField(blank=True, null=True)
    lastname = models.TextField(blank=True, null=True)
    patronymic = models.TextField(blank=True, null=True)
    gender = models.ForeignKey(Dictionary, on_delete=models.SET_NULL, 
                              db_column='gender_id', blank=True, null=True,
                              related_name='persons_by_gender')
    pincode = models.TextField(blank=True, null=True)
    birthdate = models.TextField(blank=True, null=True)
    photo_file_id = models.BigIntegerField(blank=True, null=True)
    citizenship = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                   db_column='citizenship_id', blank=True, null=True,
                                   related_name='persons_by_citizenship')
    social_id = models.BigIntegerField(blank=True, null=True)
    marital = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                               db_column='marital_id', blank=True, null=True,
                               related_name='persons_by_marital_status')
    orphan_id = models.BigIntegerField(blank=True, null=True)
    military_id = models.BigIntegerField(blank=True, null=True)
    nationality = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                   db_column='nationality_id', blank=True, null=True,
                                   related_name='persons_by_nationality')
    create_date = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_user_id = models.BigIntegerField(blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True)
    balance = models.TextField(blank=True, null=True)
    blood_type = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                  db_column='blood_type_id', blank=True, null=True,
                                  related_name='persons_by_blood_type')
    past_fevers = models.TextField(blank=True, null=True)
    hobbies = models.TextField(blank=True, null=True)
    sports = models.TextField(blank=True, null=True)
    family_information = models.TextField(blank=True, null=True)
    secondary_education_info = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'persons'

    def __str__(self):
        parts = [self.firstname, self.lastname]
        return ' '.join(filter(None, parts)) or str(self.id)

    @property
    def full_name(self):
        """Get full name"""
        parts = [self.firstname, self.lastname, self.patronymic]
        return ' '.join(filter(None, parts))


class Account(models.Model):
    """Account model for login credentials"""
    id = models.BigAutoField(primary_key=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                              db_column='person_id', blank=True, null=True)
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

    def __str__(self):
        return self.username or str(self.id)


class User(models.Model):
    """User model for system access"""
    id = models.BigAutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE,
                               db_column='account_id', blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL,
                                    db_column='organization_id', blank=True, null=True)
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
    session_duration = models.SmallIntegerField(blank=True, null=True, default=60)
    access_ip_list = models.TextField(blank=True, null=True)
    favorite_tab = models.TextField(blank=True, null=True)
    level_id = models.BigIntegerField(blank=True, null=True, default=241217432406292880)
    subscription_end_date = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        if self.account and self.account.username:
            return self.account.username
        return str(self.id)

    @property
    def is_active(self):
        """Check if user is active"""
        return self.active == 1

    @property
    def is_blocked_user(self):
        """Check if user is blocked"""
        return self.is_blocked == 1


class Teacher(models.Model):
    """Teacher model linking person, user, and professional information"""
    id = models.BigAutoField(primary_key=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                              db_column='person_id', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            db_column='user_id', blank=True, null=True)
    in_action_id = models.BigIntegerField(blank=True, null=True)
    in_action_date = models.TextField(blank=True, null=True)
    out_action_id = models.BigIntegerField(blank=True, null=True)
    out_action_date = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL,
                                    db_column='organization_id', blank=True, null=True)
    staff_type = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                  db_column='staff_type_id', blank=True, null=True,
                                  related_name='teachers_by_staff_type')
    position = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                db_column='position_id', blank=True, null=True,
                                related_name='teachers_by_position')
    contract_type = models.ForeignKey(Dictionary, on_delete=models.SET_NULL,
                                     db_column='contract_type_id', blank=True, null=True,
                                     related_name='teachers_by_contract_type')
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

    def __str__(self):
        if self.person:
            return self.person.full_name
        return str(self.id)

    @property
    def is_active(self):
        """Check if teacher is active"""
        return self.active == 1

    @property
    def is_teaching(self):
        """Check if teacher is currently teaching"""
        return self.teaching == 1

    @property
    def full_name(self):
        """Get teacher's full name"""
        if self.person:
            return self.person.full_name
        return ""

    @property
    def email(self):
        """Get teacher's email"""
        if self.user and self.user.account:
            return self.user.account.email
        return None

    @property
    def username(self):
        """Get teacher's username"""
        if self.user and self.user.account:
            return self.user.account.username
        return None
