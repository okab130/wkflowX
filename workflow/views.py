"""
業務ワークフローシステムのビュー（製造業・建設業向け）
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache

from .models import (
    Application, WorkflowStep, Comment, Attachment,
    ApplicationTypeConfig, RoleMember
)
from .forms import ApplicationForm, CommentForm, AttachmentForm


class RoleRequiredMixin(UserPassesTestMixin):
    """役割チェック用Mixin"""
    required_roles = []
    
    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.role in self.required_roles


class DashboardView(LoginRequiredMixin, ListView):
    """ダッシュボード - ユーザー種別に応じた申請一覧"""
    model = Application
    template_name = 'workflow/dashboard.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # 条件1: 自分が申請した伝票（全ステータス）
        my_applications = Application.objects.filter(applicant=user)
        
        # 条件2: 自分が受付する伝票（申請中のみ）
        receivable_applications = Application.objects.none()
        if hasattr(user, 'profile'):
            receivable_types = self._get_user_receivable_types(user)
            if receivable_types:
                receivable_applications = Application.objects.filter(
                    status='submitted',  # 申請中のみ
                    application_type__in=receivable_types
                ).exclude(
                    applicant=user  # 自分の申請は除外（条件1で含まれる）
                )
        
        # 条件3: 自分が承認する伝票（受付済のみ）
        approvable_applications = Application.objects.none()
        if hasattr(user, 'profile'):
            approvable_types = self._get_user_approvable_types(user)
            if approvable_types:
                approvable_applications = Application.objects.filter(
                    status='received',  # 受付済のみ
                    application_type__in=approvable_types
                ).exclude(
                    applicant=user  # 自分の申請は除外（条件1で含まれる）
                )
        
        # 3条件のOR結合
        queryset = (
            my_applications | 
            receivable_applications | 
            approvable_applications
        ).distinct()
        
        # 検索条件の適用
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(application_number__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )
        
        # ステータスフィルターの適用
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 申請種別フィルターの適用
        type_filter = self.request.GET.get('type', '')
        if type_filter:
            queryset = queryset.filter(application_type=type_filter)
        
        return queryset.select_related('applicant', 'applicant__profile').order_by('-created_at')
    
    def _get_user_receivable_types(self, user):
        """ユーザーが受付可能な申請種別のリストを取得（キャッシュ付き）"""
        cache_key = f'user_receivable_types_{user.id}'
        types = cache.get(cache_key)
        
        if types is None:
            # ユーザーが所属する受付ロールを取得
            user_roles = user.workflow_roles.filter(role__role_type='receiver', role__is_active=True)
            
            # それらのロールが担当する申請種別を取得
            configs = ApplicationTypeConfig.objects.filter(
                receiver_role__in=[rm.role for rm in user_roles],
                is_active=True
            )
            types = [config.application_type for config in configs]
            
            # フォールバック: 設定がない場合は全種別
            if not types:
                types = [choice[0] for choice in Application.APPLICATION_TYPE_CHOICES]
            
            cache.set(cache_key, types, 3600)  # 1時間キャッシュ
        
        return types
    
    def _get_user_approvable_types(self, user):
        """ユーザーが承認可能な申請種別のリストを取得（キャッシュ付き）"""
        cache_key = f'user_approvable_types_{user.id}'
        types = cache.get(cache_key)
        
        if types is None:
            # ユーザーが所属する承認ロールを取得
            user_roles = user.workflow_roles.filter(role__role_type='approver', role__is_active=True)
            
            # それらのロールが担当する申請種別を取得
            configs = ApplicationTypeConfig.objects.filter(
                approver_role__in=[rm.role for rm in user_roles],
                is_active=True
            )
            types = [config.application_type for config in configs]
            
            # フォールバック: 設定がない場合は全種別
            if not types:
                types = [choice[0] for choice in Application.APPLICATION_TYPE_CHOICES]
            
            cache.set(cache_key, types, 3600)  # 1時間キャッシュ
        
        return types
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報（全ユーザー共通）
        user = self.request.user
        
        # 自分の申請の統計
        context['my_draft_count'] = Application.objects.filter(
            applicant=user, 
            status='draft'
        ).count()
        context['my_submitted_count'] = Application.objects.filter(
            applicant=user, 
            status='submitted'
        ).count()
        context['my_approved_count'] = Application.objects.filter(
            applicant=user, 
            status='approved'
        ).count()
        
        # 受付待ち（受付可能な申請種別）
        if hasattr(user, 'profile'):
            receivable_types = self._get_user_receivable_types(user)
            if receivable_types:
                context['pending_receive_count'] = Application.objects.filter(
                    status='submitted',
                    application_type__in=receivable_types
                ).exclude(applicant=user).count()
            else:
                context['pending_receive_count'] = 0
            
            # 承認待ち（承認可能な申請種別）
            approvable_types = self._get_user_approvable_types(user)
            if approvable_types:
                context['pending_approve_count'] = Application.objects.filter(
                    status='received',
                    application_type__in=approvable_types
                ).exclude(applicant=user).count()
            else:
                context['pending_approve_count'] = 0
        
        # フィルター用の選択肢
        context['status_choices'] = Application.STATUS_CHOICES
        context['type_choices'] = Application.APPLICATION_TYPE_CHOICES
        
        return context


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    """申請作成"""
    model = Application
    form_class = ApplicationForm
    template_name = 'workflow/application_form.html'
    success_url = reverse_lazy('workflow:dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        print(f"DEBUG: form_valid called")  # デバッグ
        print(f"DEBUG: request.FILES = {self.request.FILES}")  # デバッグ
        print(f"DEBUG: request.POST keys = {self.request.POST.keys()}")  # デバッグ
        
        form.instance.applicant = self.request.user
        
        # 下書き保存か申請提出かを判定
        if 'submit' in self.request.POST:
            form.instance.status = 'submitted'
            form.instance.submitted_at = timezone.now()
        else:
            form.instance.status = 'draft'
        
        # フォームを保存（self.objectが設定される）
        response = super().form_valid(form)
        
        print(f"DEBUG: Application saved, ID={self.object.id}")  # デバッグ
        
        # 添付ファイルの処理（self.object使用後）
        self._handle_attachments()
        
        # 申請提出の場合の処理
        if 'submit' in self.request.POST:
            # ワークフローステップを作成
            WorkflowStep.objects.create(
                application=self.object,
                step_type='submit',
                processor=self.request.user,
                status='completed',
                processed_at=timezone.now()
            )
            
            # メール通知
            self.object.send_notification_to_receivers()
            messages.success(self.request, f'申請を提出しました。申請番号: {self.object.application_number}')
        else:
            messages.success(self.request, '下書きとして保存しました。')
        
        return response
    
    def _handle_attachments(self):
        """添付ファイルの処理"""
        files = self.request.FILES.getlist('attachments')
        for file in files:
            # ファイルサイズチェック（10MB制限）
            if file.size > 10 * 1024 * 1024:
                messages.warning(self.request, f'{file.name} はサイズが大きすぎるためスキップされました（10MB以下）')
                continue
            
            # ファイル拡張子チェック
            allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.zip']
            file_ext = file.name.lower()[file.name.rfind('.'):]
            if file_ext not in allowed_extensions:
                messages.warning(self.request, f'{file.name} は許可されていないファイル形式です')
                continue
            
            Attachment.objects.create(
                application=self.object,
                file=file,
                uploaded_by=self.request.user
            )


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    """申請詳細"""
    model = Application
    template_name = 'workflow/application_detail.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        queryset = Application.objects.select_related('applicant', 'applicant__profile').prefetch_related(
            'workflow_steps__processor',
            'comments__user',
            'attachments__uploaded_by'
        )
        
        user = self.request.user
        
        # 管理者は全て閲覧可能
        if hasattr(user, 'profile') and user.profile.role == 'admin':
            return queryset
        
        # 以下の条件で閲覧可能（ダッシュボードと同じロジック）
        # 1. 自分が申請した伝票
        # 2. 自分が受付可能な申請種別の申請中伝票
        # 3. 自分が承認可能な申請種別の受付済伝票
        
        accessible_ids = []
        
        # 条件1: 自分が申請した伝票
        my_applications = Application.objects.filter(applicant=user).values_list('id', flat=True)
        accessible_ids.extend(my_applications)
        
        # 条件2: 受付可能な申請中の伝票
        if hasattr(user, 'profile'):
            receivable_types = self._get_user_receivable_types(user)
            if receivable_types:
                receivable_apps = Application.objects.filter(
                    status='submitted',
                    application_type__in=receivable_types
                ).values_list('id', flat=True)
                accessible_ids.extend(receivable_apps)
            
            # 条件3: 承認可能な受付済の伝票
            approvable_types = self._get_user_approvable_types(user)
            if approvable_types:
                approvable_apps = Application.objects.filter(
                    status='received',
                    application_type__in=approvable_types
                ).values_list('id', flat=True)
                accessible_ids.extend(approvable_apps)
        
        # アクセス可能なIDでフィルタリング
        return queryset.filter(id__in=accessible_ids)
    
    def _get_user_receivable_types(self, user):
        """ユーザーが受付可能な申請種別のリストを取得（キャッシュ付き）"""
        cache_key = f'user_receivable_types_{user.id}'
        types = cache.get(cache_key)
        
        if types is None:
            user_roles = user.workflow_roles.filter(role__role_type='receiver', role__is_active=True)
            configs = ApplicationTypeConfig.objects.filter(
                receiver_role__in=[rm.role for rm in user_roles],
                is_active=True
            )
            types = [config.application_type for config in configs]
            
            if not types:
                types = [choice[0] for choice in Application.APPLICATION_TYPE_CHOICES]
            
            cache.set(cache_key, types, 3600)
        
        return types
    
    def _get_user_approvable_types(self, user):
        """ユーザーが承認可能な申請種別のリストを取得（キャッシュ付き）"""
        cache_key = f'user_approvable_types_{user.id}'
        types = cache.get(cache_key)
        
        if types is None:
            user_roles = user.workflow_roles.filter(role__role_type='approver', role__is_active=True)
            configs = ApplicationTypeConfig.objects.filter(
                approver_role__in=[rm.role for rm in user_roles],
                is_active=True
            )
            types = [config.application_type for config in configs]
            
            if not types:
                types = [choice[0] for choice in Application.APPLICATION_TYPE_CHOICES]
            
            cache.set(cache_key, types, 3600)
        
        return types
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['attachment_form'] = AttachmentForm()
        
        # アクション権限の判定
        application = self.object
        user = self.request.user
        
        context['can_edit'] = application.can_edit(user)
        context['can_submit'] = application.can_submit(user)
        context['can_receive'] = application.can_receive(user)
        context['can_approve'] = application.can_approve(user)
        context['can_return'] = application.can_return(user)
        
        return context


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    """申請編集"""
    model = Application
    form_class = ApplicationForm
    template_name = 'workflow/application_form.html'
    
    def get_queryset(self):
        # 自分の下書きまたは差し戻しのみ編集可能
        return Application.objects.filter(applicant=self.request.user, status__in=['draft', 'returned'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('workflow:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # 再提出の場合
        if 'submit' in self.request.POST and self.object.status == 'returned':
            form.instance.status = 'submitted'
            form.instance.submitted_at = timezone.now()
        
        # フォームを保存
        response = super().form_valid(form)
        
        # 添付ファイルの処理（self.object使用後）
        self._handle_attachments()
        
        # 再提出の場合の処理
        if 'submit' in self.request.POST and self.object.status == 'submitted':
            # ワークフローステップを作成
            WorkflowStep.objects.create(
                application=self.object,
                step_type='submit',
                processor=self.request.user,
                status='completed',
                comment='再申請',
                processed_at=timezone.now()
            )
            
            # メール通知
            self.object.send_notification_to_receivers()
            messages.success(self.request, '申請を再提出しました。')
        else:
            messages.success(self.request, '申請を更新しました。')
        
        return response
    
    def _handle_attachments(self):
        """添付ファイルの処理"""
        files = self.request.FILES.getlist('attachments')
        for file in files:
            # ファイルサイズチェック（10MB制限）
            if file.size > 10 * 1024 * 1024:
                messages.warning(self.request, f'{file.name} はサイズが大きすぎるためスキップされました（10MB以下）')
                continue
            
            # ファイル拡張子チェック
            allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.zip']
            file_ext = file.name.lower()[file.name.rfind('.'):]
            if file_ext not in allowed_extensions:
                messages.warning(self.request, f'{file.name} は許可されていないファイル形式です')
                continue
            
            Attachment.objects.create(
                application=self.object,
                file=file,
                uploaded_by=self.request.user
            )


@login_required
@transaction.atomic
def submit_application(request, pk):
    """申請を提出"""
    application = get_object_or_404(Application, pk=pk, applicant=request.user)
    
    if not application.can_submit(request.user):
        messages.error(request, '提出できない状態です。')
        return redirect('workflow:detail', pk=pk)
    
    if request.method == 'POST':
        if application.submit():
            # ワークフローステップを作成
            WorkflowStep.objects.create(
                application=application,
                step_type='submit',
                processor=request.user,
                status='completed',
                processed_at=timezone.now()
            )
            messages.success(request, '申請を提出しました。')
        else:
            messages.error(request, '申請の提出に失敗しました。')
        
        return redirect('workflow:detail', pk=pk)
    
    return render(request, 'workflow/confirm_submit.html', {'application': application})


@login_required
@transaction.atomic
def receive_application(request, pk):
    """申請を受付"""
    application = get_object_or_404(Application, pk=pk, status='submitted')
    
    if not application.can_receive(request.user):
        messages.error(request, '受付する権限がありません。')
        return redirect('workflow:detail', pk=pk)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        action = request.POST.get('action')
        
        if action == 'receive':
            if application.receive(request.user):
                # ワークフローステップを作成
                WorkflowStep.objects.create(
                    application=application,
                    step_type='receive',
                    processor=request.user,
                    status='completed',
                    comment=comment,
                    processed_at=timezone.now()
                )
                messages.success(request, '申請を受付しました。')
            else:
                messages.error(request, '受付処理に失敗しました。')
        
        elif action == 'return':
            if application.return_to_applicant(request.user, comment):
                # ワークフローステップを作成
                WorkflowStep.objects.create(
                    application=application,
                    step_type='return',
                    processor=request.user,
                    status='completed',
                    comment=comment,
                    processed_at=timezone.now()
                )
                messages.success(request, '申請を差し戻しました。')
            else:
                messages.error(request, '差し戻し処理に失敗しました。')
        
        return redirect('workflow:detail', pk=pk)
    
    return render(request, 'workflow/confirm_receive.html', {'application': application})


@login_required
@transaction.atomic
def approve_application(request, pk):
    """申請を承認"""
    application = get_object_or_404(Application, pk=pk, status='received')
    
    if not application.can_approve(request.user):
        messages.error(request, '承認する権限がありません。')
        return redirect('workflow:detail', pk=pk)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        action = request.POST.get('action')
        
        if action == 'approve':
            if application.approve(request.user):
                # ワークフローステップを作成
                WorkflowStep.objects.create(
                    application=application,
                    step_type='approve',
                    processor=request.user,
                    status='completed',
                    comment=comment,
                    processed_at=timezone.now()
                )
                messages.success(request, '申請を承認しました。')
            else:
                messages.error(request, '承認処理に失敗しました。')
        
        elif action == 'reject':
            if application.reject(request.user, comment):
                # ワークフローステップを作成
                WorkflowStep.objects.create(
                    application=application,
                    step_type='reject',
                    processor=request.user,
                    status='rejected',
                    comment=comment,
                    processed_at=timezone.now()
                )
                messages.success(request, '申請を却下しました。')
            else:
                messages.error(request, '却下処理に失敗しました。')
        
        return redirect('workflow:detail', pk=pk)
    
    return render(request, 'workflow/confirm_approve.html', {'application': application})


@login_required
def add_comment(request, pk):
    """コメントを追加"""
    application = get_object_or_404(Application, pk=pk)
    
    # 取引先は自分の申請のみコメント可能
    user = request.user
    if hasattr(user, 'profile') and user.profile.role == 'vendor':
        if application.applicant != user:
            messages.error(request, 'コメントする権限がありません。')
            return redirect('workflow:detail', pk=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.application = application
            comment.user = request.user
            comment.save()
            messages.success(request, 'コメントを追加しました。')
    
    return redirect('workflow:detail', pk=pk)


@login_required
def upload_attachment(request, pk):
    """添付ファイルをアップロード"""
    application = get_object_or_404(Application, pk=pk)
    
    # 編集可能な場合のみアップロード可能
    if not application.can_edit(request.user):
        messages.error(request, 'ファイルをアップロードする権限がありません。')
        return redirect('workflow:detail', pk=pk)
    
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.application = application
            attachment.uploaded_by = request.user
            attachment.save()
            messages.success(request, 'ファイルをアップロードしました。')
        else:
            messages.error(request, 'ファイルのアップロードに失敗しました。')
    
    return redirect('workflow:detail', pk=pk)


@login_required
def delete_attachment(request, pk, attachment_id):
    """添付ファイルを削除"""
    application = get_object_or_404(Application, pk=pk)
    attachment = get_object_or_404(Attachment, pk=attachment_id, application=application)
    
    # 編集可能な場合のみ削除可能
    if not application.can_edit(request.user):
        messages.error(request, 'ファイルを削除する権限がありません。')
        return redirect('workflow:detail', pk=pk)
    
    if request.method == 'POST':
        attachment.file.delete()
        attachment.delete()
        messages.success(request, 'ファイルを削除しました。')
    
    return redirect('workflow:detail', pk=pk)


class MyApplicationsView(LoginRequiredMixin, ListView):
    """自分の申請一覧"""
    model = Application
    template_name = 'workflow/my_applications.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).order_by('-created_at')


class PendingReceiveView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """受付待ち一覧（ロールベース）"""
    model = Application
    template_name = 'workflow/pending_receive.html'
    context_object_name = 'applications'
    paginate_by = 20
    required_roles = ['receiver', 'admin']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.filter(status='submitted').order_by('submitted_at')
        
        # 管理者以外はロールベースでフィルタリング
        if hasattr(user, 'profile') and user.profile.role != 'admin':
            # ユーザーが受付可能な申請種別のみ表示
            receivable_types = self._get_user_receivable_types(user)
            queryset = queryset.filter(application_type__in=receivable_types)
        
        return queryset
    
    def _get_user_receivable_types(self, user):
        """ユーザーが受付可能な申請種別のリストを取得"""
        cache_key = f'user_receivable_types_{user.id}'
        types = cache.get(cache_key)
        
        if types is None:
            user_roles = user.workflow_roles.filter(role__role_type='receiver', role__is_active=True)
            configs = ApplicationTypeConfig.objects.filter(
                receiver_role__in=[rm.role for rm in user_roles],
                is_active=True
            )
            types = [config.application_type for config in configs]
            
            if not types:
                types = [choice[0] for choice in Application.APPLICATION_TYPE_CHOICES]
            
            cache.set(cache_key, types, 3600)
        
        return types


class PendingApproveView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """承認待ち一覧（ロールベース）"""
    model = Application
    template_name = 'workflow/pending_approve.html'
    context_object_name = 'applications'
    paginate_by = 20
    required_roles = ['approver', 'admin']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.filter(status='received').order_by('received_at')
        
        # 管理者以外はロールベースでフィルタリング
        if hasattr(user, 'profile') and user.profile.role != 'admin':
            # ユーザーが承認可能な申請種別のみ表示
            approvable_types = self._get_user_approvable_types(user)
            queryset = queryset.filter(application_type__in=approvable_types)
        
        return queryset
    
    def _get_user_approvable_types(self, user):
        """ユーザーが承認可能な申請種別のリストを取得"""
        cache_key = f'user_approvable_types_{user.id}'
        types = cache.get(cache_key)
        
        if types is None:
            user_roles = user.workflow_roles.filter(role__role_type='approver', role__is_active=True)
            configs = ApplicationTypeConfig.objects.filter(
                approver_role__in=[rm.role for rm in user_roles],
                is_active=True
            )
            types = [config.application_type for config in configs]
            
            if not types:
                types = [choice[0] for choice in Application.APPLICATION_TYPE_CHOICES]
            
            cache.set(cache_key, types, 3600)
        
        return types


@login_required
def user_manual(request):
    """利用者マニュアル"""
    return render(request, 'workflow/user_manual.html')


@login_required
def operation_manual(request):
    """運用マニュアル"""
    return render(request, 'workflow/operation_manual.html')
