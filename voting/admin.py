from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Person, Category, VotingCode, Vote, VoteStatistics


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['created_at']
        return self.readonly_fields


@admin.register(VotingCode)
class VotingCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'current_uses', 'max_uses', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_by', 'created_at']
    search_fields = ['code']
    readonly_fields = ['code', 'created_by', 'created_at']
    actions = ['generate_codes', 'deactivate_codes']
    
    def save_model(self, request, obj, form, change):
        if not change:  # creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def generate_codes(self, request, queryset):
        """Generate new voting codes"""
        count = 10  # Generate 10 codes at once
        codes = []
        for _ in range(count):
            code = VotingCode.generate_code(request.user)
            codes.append(code.code)
        
        codes_list = ', '.join(codes)
        self.message_user(request, f'{count} neue Voting-Codes wurden generiert: {codes_list}')
    generate_codes.short_description = "10 neue Codes generieren"
    
    def deactivate_codes(self, request, queryset):
        """Deactivate selected codes"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} Codes wurden deaktiviert.')
    deactivate_codes.short_description = "Ausgewählte Codes deaktivieren"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['person', 'category', 'voting_code', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['person__name', 'category__title', 'voting_code__code']
    readonly_fields = ['voting_code', 'category', 'person', 'ip_address', 'user_agent', 'created_at']
    
    def has_add_permission(self, request):
        return False  # Prevent manual vote creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent vote editing
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete votes


@admin.register(VoteStatistics)
class VoteStatisticsAdmin(admin.ModelAdmin):
    list_display = ['person', 'category', 'vote_count', 'percentage', 'last_updated']
    list_filter = ['category', 'last_updated']
    search_fields = ['person__name', 'category__title']
    readonly_fields = ['category', 'person', 'vote_count', 'percentage', 'last_updated']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Custom admin site configuration
admin.site.site_header = "Klassenabstimmung Admin"
admin.site.site_title = "Klassenabstimmung"
admin.site.index_title = "Verwaltung der Klassenabstimmung"

