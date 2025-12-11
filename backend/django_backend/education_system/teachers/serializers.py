from rest_framework import serializers
from .models import Teacher, Person, User, Account, Organization, Dictionary


class DictionarySerializer(serializers.ModelSerializer):
    """Serializer for dictionary entries"""
    name = serializers.SerializerMethodField()

    class Meta:
        model = Dictionary
        fields = ['id', 'name', 'code']

    def get_name(self, obj):
        """Get the appropriate name based on language preference"""
        return obj.name_en or obj.name_az or obj.name_ru or obj.code


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organizations"""
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'short_name']


class PersonSerializer(serializers.ModelSerializer):
    """Serializer for person information"""
    gender_name = serializers.CharField(source='gender.name_en', read_only=True)
    citizenship_name = serializers.CharField(source='citizenship.name_en', read_only=True)
    nationality_name = serializers.CharField(source='nationality.name_en', read_only=True)
    marital_status_name = serializers.CharField(source='marital.name_en', read_only=True)
    blood_type_name = serializers.CharField(source='blood_type.name_en', read_only=True)
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Person
        fields = [
            'id', 'firstname', 'lastname', 'patronymic', 'full_name',
            'pincode', 'birthdate', 'gender_id', 'gender_name',
            'citizenship_id', 'citizenship_name', 'nationality_id', 'nationality_name',
            'marital_id', 'marital_status_name', 'blood_type_id', 'blood_type_name',
            'balance', 'hobbies', 'sports', 'family_information',
            'secondary_education_info', 'past_fevers'
        ]


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for account information"""
    
    class Meta:
        model = Account
        fields = ['id', 'username', 'email']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information"""
    account = AccountSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    is_blocked_user = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'account', 'user_type', 'is_active', 'is_blocked_user',
            'last_action_date'
        ]


class TeacherListSerializer(serializers.ModelSerializer):
    """Serializer for teacher list view"""
    full_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_teaching = serializers.ReadOnlyField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    position_name = serializers.CharField(source='position.name_en', read_only=True)
    staff_type_name = serializers.CharField(source='staff_type.name_en', read_only=True)
    contract_type_name = serializers.CharField(source='contract_type.name_en', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'full_name', 'email', 'username', 'is_active', 'is_teaching',
            'organization_name', 'position_name', 'staff_type_name', 'contract_type_name',
            'card_number', 'create_date', 'update_date'
        ]


class TeacherDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed teacher view"""
    person = PersonSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    position = DictionarySerializer(read_only=True)
    staff_type = DictionarySerializer(read_only=True)
    contract_type = DictionarySerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_teaching = serializers.ReadOnlyField()

    class Meta:
        model = Teacher
        fields = [
            'id', 'person', 'user', 'organization', 'position', 'staff_type',
            'contract_type', 'full_name', 'email', 'username', 'is_active',
            'is_teaching', 'card_number', 'create_date', 'update_date',
            'in_action_date', 'out_action_date'
        ]


class TeacherStatsSerializer(serializers.Serializer):
    """Serializer for teacher statistics"""
    total_teachers = serializers.IntegerField()
    active_teachers = serializers.IntegerField()
    teaching_count = serializers.IntegerField()
    organizations_count = serializers.IntegerField()


class FilterOptionsSerializer(serializers.Serializer):
    """Serializer for filter options"""
    organizations = OrganizationSerializer(many=True)
    positions = DictionarySerializer(many=True)
    staff_types = DictionarySerializer(many=True)
    contract_types = DictionarySerializer(many=True)