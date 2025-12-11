from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from .models import Teacher, Organization, Dictionary
from .serializers import (
    TeacherListSerializer, TeacherDetailSerializer, TeacherStatsSerializer,
    FilterOptionsSerializer, OrganizationSerializer, DictionarySerializer
)


class TeacherPagination(PageNumberPagination):
    """Custom pagination for teachers"""
    page_size = 25
    page_size_query_param = 'per_page'
    max_page_size = 100


class TeacherListView(generics.ListAPIView):
    """List view for teachers with filtering and pagination"""
    serializer_class = TeacherListSerializer
    pagination_class = TeacherPagination
    permission_classes = [AllowAny]  # Remove for production

    def get_queryset(self):
        """Get filtered queryset"""
        queryset = Teacher.objects.select_related(
            'person', 'user__account', 'organization', 'position', 
            'staff_type', 'contract_type'
        ).all()

        # Apply filters
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(person__firstname__icontains=search) |
                Q(person__lastname__icontains=search) |
                Q(person__pincode__icontains=search)
            )

        organization_id = self.request.query_params.get('organization_id', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        position_id = self.request.query_params.get('position_id', None)
        if position_id:
            queryset = queryset.filter(position_id=position_id)

        teaching = self.request.query_params.get('teaching', None)
        if teaching is not None:
            teaching_value = 1 if teaching.lower() == 'true' else 0
            queryset = queryset.filter(teaching=teaching_value)

        active = self.request.query_params.get('active', None)
        if active is not None:
            active_value = 1 if active.lower() == 'true' else 0
            queryset = queryset.filter(user__active=active_value)

        return queryset.order_by('person__lastname', 'person__firstname')


class TeacherDetailView(generics.RetrieveAPIView):
    """Detail view for a specific teacher"""
    queryset = Teacher.objects.select_related(
        'person', 'user__account', 'organization', 'position', 
        'staff_type', 'contract_type'
    )
    serializer_class = TeacherDetailSerializer
    permission_classes = [AllowAny]  # Remove for production


@api_view(['GET'])
@permission_classes([AllowAny])  # Remove for production
def teacher_stats(request):
    """Get teacher statistics"""
    try:
        stats = {
            'total_teachers': Teacher.objects.count(),
            'active_teachers': Teacher.objects.filter(user__active=1).count(),
            'teaching_count': Teacher.objects.filter(teaching=1).count(),
            'organizations_count': Teacher.objects.values('organization_id').distinct().count()
        }
        
        serializer = TeacherStatsSerializer(stats)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {'detail': f'Failed to retrieve teacher statistics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])  # Remove for production
def filter_options(request):
    """Get available filter options for teachers"""
    try:
        # Get organizations that have teachers
        organizations = Organization.objects.filter(
            id__in=Teacher.objects.values_list('organization_id', flat=True)
        ).distinct().order_by('name')

        # Get positions from dictionaries that are used by teachers
        positions = Dictionary.objects.filter(
            id__in=Teacher.objects.values_list('position_id', flat=True)
        ).distinct().order_by('name_en')

        # Get staff types from dictionaries that are used by teachers
        staff_types = Dictionary.objects.filter(
            id__in=Teacher.objects.values_list('staff_type_id', flat=True)
        ).distinct().order_by('name_en')

        # Get contract types from dictionaries that are used by teachers
        contract_types = Dictionary.objects.filter(
            id__in=Teacher.objects.values_list('contract_type_id', flat=True)
        ).distinct().order_by('name_en')

        options = {
            'organizations': OrganizationSerializer(organizations, many=True).data,
            'positions': DictionarySerializer(positions, many=True).data,
            'staff_types': DictionarySerializer(staff_types, many=True).data,
            'contract_types': DictionarySerializer(contract_types, many=True).data,
        }
        
        serializer = FilterOptionsSerializer(options)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {'detail': f'Failed to retrieve filter options: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
