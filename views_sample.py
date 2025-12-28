"""
業務ワークフローシステムのビュー
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import Application, WorkflowStep, Comment, Attachment
from .forms import ApplicationForm, CommentForm


class DashboardView(LoginRequiredMixin, ListView):
    """ダッシュボード - ユーザー種別に応じた申請一覧"""
    model = Application
    template_name = 'workflow/dashboard.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.select_related('applicant').all()
        
        # ユーザー種別でフィルタリング
        if hasattr(user, 'profile'):
            if user.profile.role == 'applicant':
                # 申請者: 自分の申請のみ
                queryset = queryset.filter(applicant=user)
            elif user.profile.role == 'receiver':
                # 受付担当: 申請中のもの
                queryset = queryset.filter(status='submitted')
            elif user.profile.role == 'approver':
                # 承認者: 受付済のもの
                queryset = queryset.filter(status='received')
        
        return queryset


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    """申請作成"""
    model = Application
    form_class = ApplicationForm
    template_name = 'workflow/application_form.html'
    success_url = reverse_lazy('workflow:dashboard')
    
    def form_valid(self, form):
        form.instance.applicant = self.request.user
        
        # 下書き保存か申請提出かを判定
        if 'submit' in self.request.POST:
            form.instance.status = 'submitted'
            form.instance.submitted_at = timezone.now()
            messages.success(self.request, '申請を提出しました。')
        else:
            form.instance.status = 'draft'
            messages.success(self.request, '下書きとして保存しました。')
        
        return super().form_valid(form)


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    """申請詳細"""
    model = Application
    template_name = 'workflow/application_detail.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        return Application.objects.select_related('applicant').prefetch_related(
            'workflow_steps__processor',
            'comments__user',
            'attachments'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        
        # アクション権限の判定
        application = self.object
        user = self.request.user
        
        context['can_edit'] = application.can_edit(user)
        context['can_receive'] = application.can_receive(user)
        context['can_approve'] = application.can_approve(user)
        
        return context


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    """申請編集"""
    model = Application
    form_class = ApplicationForm
    template_name = 'workflow/application_form.html'
    
    def get_queryset(self):
        # 自分の下書きのみ編集可能
        return Application.objects.filter(applicant=self.request.user, status='draft')
    
    def get_success_url(self):
        return reverse_lazy('workflow:detail', kwargs={'pk': self.object.pk})


@login_required
@transaction.atomic
def submit_application(request, pk):
    """申請を提出"""
    application = get_object_or_404(Application, pk=pk, applicant=request.user, status='draft')
    
    if request.method == 'POST':
        application.submit()
        
        # ワークフローステップを作成
        WorkflowStep.objects.create(
            application=application,
            step_type='submit',
            processor=request.user,
            status='completed',
            processed_at=timezone.now()
        )
        
        messages.success(request, '申請を提出しました。')
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
            application.status = 'received'
            step_status = 'completed'
            msg = '申請を受付しました。'
        else:
            application.status = 'rejected'
            step_status = 'rejected'
            msg = '申請を差し戻しました。'
        
        application.save()
        
        # ワークフローステップを作成
        WorkflowStep.objects.create(
            application=application,
            step_type='receive',
            processor=request.user,
            status=step_status,
            comment=comment,
            processed_at=timezone.now()
        )
        
        messages.success(request, msg)
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
            application.status = 'approved'
            step_status = 'completed'
            msg = '申請を承認しました。'
        else:
            application.status = 'rejected'
            step_status = 'rejected'
            msg = '申請を却下しました。'
        
        application.save()
        
        # ワークフローステップを作成
        WorkflowStep.objects.create(
            application=application,
            step_type='approve',
            processor=request.user,
            status=step_status,
            comment=comment,
            processed_at=timezone.now()
        )
        
        messages.success(request, msg)
        return redirect('workflow:detail', pk=pk)
    
    return render(request, 'workflow/confirm_approve.html', {'application': application})


@login_required
def add_comment(request, pk):
    """コメントを追加"""
    application = get_object_or_404(Application, pk=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.application = application
            comment.user = request.user
            comment.save()
            messages.success(request, 'コメントを追加しました。')
    
    return redirect('workflow:detail', pk=pk)


class MyApplicationsView(LoginRequiredMixin, ListView):
    """自分の申請一覧"""
    model = Application
    template_name = 'workflow/my_applications.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).order_by('-created_at')


class PendingReceiveView(LoginRequiredMixin, ListView):
    """受付待ち一覧"""
    model = Application
    template_name = 'workflow/pending_receive.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        return Application.objects.filter(status='submitted').order_by('submitted_at')


class PendingApproveView(LoginRequiredMixin, ListView):
    """承認待ち一覧"""
    model = Application
    template_name = 'workflow/pending_approve.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        return Application.objects.filter(status='received').order_by('updated_at')
