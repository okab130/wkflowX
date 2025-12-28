"""
業務ワークフローシステムの管理画面設定（製造業・建設業向け）
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Application, WorkflowStep, Comment, Attachment,
    WorkflowRole, RoleMember, ApplicationTypeConfig
)


@admin.register(WorkflowRole)
class WorkflowRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'role_type', 'is_active', 'member_count', 'created_at']
    list_filter = ['role_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['role_type', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'role_type', 'description')
        }),
        ('ステータス', {
            'fields': ('is_active',)
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        count = obj.get_members_count()
        return format_html('<strong>{}</strong> 人', count)
    member_count.short_description = 'メンバー数'


@admin.register(RoleMember)
class RoleMemberAdmin(admin.ModelAdmin):
    list_display = ['role', 'user', 'user_email', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__username', 'user__email', 'role__name']
    readonly_fields = ['assigned_at']
    date_hierarchy = 'assigned_at'
    autocomplete_fields = ['user', 'assigned_by']
    
    fieldsets = (
        ('ロール割当', {
            'fields': ('role', 'user')
        }),
        ('割当情報', {
            'fields': ('assigned_by', 'assigned_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email if obj.user.email else '-'
    user_email.short_description = 'メールアドレス'


@admin.register(ApplicationTypeConfig)
class ApplicationTypeConfigAdmin(admin.ModelAdmin):
    list_display = [
        'get_application_type_display',
        'receiver_role',
        'approver_role',
        'is_active',
        'updated_at'
    ]
    list_filter = ['is_active', 'receiver_role', 'approver_role']
    search_fields = ['application_type']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['application_type']
    
    fieldsets = (
        ('申請種別', {
            'fields': ('application_type',)
        }),
        ('ロール設定', {
            'fields': ('receiver_role', 'approver_role')
        }),
        ('ステータス', {
            'fields': ('is_active',)
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_application_type_display(self, obj):
        type_display_map = dict(Application.APPLICATION_TYPE_CHOICES)
        return type_display_map.get(obj.application_type, obj.application_type)
    get_application_type_display.short_description = '申請種別'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'company_name', 'department', 'phone_number']
    list_filter = ['role']
    search_fields = ['user__username', 'company_name', 'department']
    ordering = ['company_name', 'user__username']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_number',
        'get_application_type_display',
        'title',
        'company_name',
        'applicant',
        'status_badge',
        'submitted_at',
        'created_at'
    ]
    list_filter = ['status', 'application_type', 'created_at', 'submitted_at']
    search_fields = ['application_number', 'title', 'company_name', 'applicant__username']
    readonly_fields = [
        'application_number',
        'created_at',
        'updated_at',
        'submitted_at',
        'received_at',
        'approved_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本情報', {
            'fields': ('application_number', 'application_type', 'title', 'content')
        }),
        ('申請者情報', {
            'fields': ('applicant', 'company_name')
        }),
        ('作業情報', {
            'fields': ('work_location', 'work_start_date', 'work_end_date', 'worker_count')
        }),
        ('工具情報', {
            'fields': ('tool_list',),
            'classes': ('collapse',)
        }),
        ('制限エリア情報', {
            'fields': ('restricted_area', 'entry_purpose', 'entry_members'),
            'classes': ('collapse',)
        }),
        ('工事情報', {
            'fields': ('contractor_name',),
            'classes': ('collapse',)
        }),
        ('ステータス', {
            'fields': ('status',)
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'received_at', 'approved_at')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'submitted': '#0dcaf0',
            'received': '#ffc107',
            'approved': '#198754',
            'rejected': '#dc3545',
            'returned': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'ステータス'


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = [
        'application',
        'step_type',
        'processor',
        'status',
        'processed_at',
        'created_at'
    ]
    list_filter = ['step_type', 'status', 'processed_at']
    search_fields = ['application__application_number', 'processor__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'processed_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['application', 'user', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['application__application_number', 'user__username', 'content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'コメント内容'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'filename',
        'application',
        'file_size_display_admin',
        'uploaded_by',
        'uploaded_at'
    ]
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'application__application_number', 'uploaded_by__username']
    readonly_fields = ['file_size', 'uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    def file_size_display_admin(self, obj):
        return obj.get_file_size_display()
    file_size_display_admin.short_description = 'ファイルサイズ'


# 管理画面のカスタマイズ
admin.site.site_header = '業務ワークフローシステム 管理画面'
admin.site.site_title = 'ワークフロー管理'
admin.site.index_title = 'メニュー'
