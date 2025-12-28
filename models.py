"""
業務ワークフローシステムのモデル定義（製造業・建設業向け）
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache


class WorkflowRole(models.Model):
    """ワークフローロール（受付・承認の役割）"""
    ROLE_TYPE_CHOICES = [
        ('receiver', '受付'),
        ('approver', '承認'),
    ]
    
    name = models.CharField('ロール名', max_length=100, unique=True)
    role_type = models.CharField('ロール種別', max_length=20, choices=ROLE_TYPE_CHOICES)
    description = models.TextField('説明', blank=True)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = 'ワークフローロール'
        verbose_name_plural = 'ワークフローロール'
        ordering = ['role_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_role_type_display()})"
    
    def get_members_count(self):
        """メンバー数を取得"""
        return self.members.count()


class RoleMember(models.Model):
    """ロールメンバー（ロールとユーザーの多対多関係）"""
    role = models.ForeignKey(WorkflowRole, on_delete=models.CASCADE, related_name='members', verbose_name='ロール')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflow_roles', verbose_name='ユーザー')
    assigned_at = models.DateTimeField('割当日時', auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='role_assignments_made',
        verbose_name='割当者'
    )
    
    class Meta:
        verbose_name = 'ロールメンバー'
        verbose_name_plural = 'ロールメンバー'
        unique_together = ['role', 'user']
        ordering = ['role', 'assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # キャッシュをクリア
        cache.delete(f'user_receivable_types_{self.user.id}')
        cache.delete(f'user_approvable_types_{self.user.id}')
    
    def delete(self, *args, **kwargs):
        user_id = self.user.id
        super().delete(*args, **kwargs)
        # キャッシュをクリア
        cache.delete(f'user_receivable_types_{user_id}')
        cache.delete(f'user_approvable_types_{user_id}')


class ApplicationTypeConfig(models.Model):
    """申請種別設定（申請種別ごとの受付・承認ロール設定）"""
    application_type = models.CharField('申請種別', max_length=30, unique=True)
    receiver_role = models.ForeignKey(
        WorkflowRole,
        on_delete=models.PROTECT,
        related_name='receiver_for_types',
        verbose_name='受付ロール',
        limit_choices_to={'role_type': 'receiver', 'is_active': True}
    )
    approver_role = models.ForeignKey(
        WorkflowRole,
        on_delete=models.PROTECT,
        related_name='approver_for_types',
        verbose_name='承認ロール',
        limit_choices_to={'role_type': 'approver', 'is_active': True}
    )
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = '申請種別設定'
        verbose_name_plural = '申請種別設定'
        ordering = ['application_type']
    
    def __str__(self):
        return f"{self.application_type} - 受付:{self.receiver_role.name} / 承認:{self.approver_role.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 関連するキャッシュをクリア
        cache.delete(f'application_type_config_{self.application_type}')


class UserProfile(models.Model):
    """ユーザープロファイル拡張"""
    ROLE_CHOICES = [
        ('vendor', '取引先'),
        ('receiver', '受付担当'),
        ('approver', '承認者'),
        ('admin', '管理者'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('役割', max_length=20, choices=ROLE_CHOICES, default='vendor')
    company_name = models.CharField('企業名', max_length=200)
    department = models.CharField('部署', max_length=100, blank=True)
    phone_number = models.CharField('電話番号', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'ユーザープロファイル'
        verbose_name_plural = 'ユーザープロファイル'
    
    def __str__(self):
        return f"{self.user.username} - {self.company_name} ({self.get_role_display()})"


class Application(models.Model):
    """申請"""
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('submitted', '申請中'),
        ('received', '受付済'),
        ('approved', '承認済'),
        ('rejected', '却下'),
        ('returned', '差し戻し'),
    ]
    
    APPLICATION_TYPE_CHOICES = [
        ('work', '作業申請'),
        ('construction', '工事申請'),
        ('tool_bringin', '工具持込申請'),
        ('restricted_entry', '制限エリア立入申請'),
        ('restricted_tool', '制限エリア工具持込申請'),
    ]
    
    # 基本情報
    application_number = models.CharField('申請番号', max_length=20, unique=True, editable=False)
    application_type = models.CharField('申請種別', max_length=30, choices=APPLICATION_TYPE_CHOICES)
    title = models.CharField('タイトル', max_length=200)
    content = models.TextField('申請内容詳細')
    
    # 申請者情報
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', verbose_name='申請者')
    company_name = models.CharField('申請企業名', max_length=200)
    
    # 作業情報
    work_location = models.CharField('作業場所', max_length=200, blank=True)
    work_start_date = models.DateField('作業開始予定日', null=True, blank=True)
    work_end_date = models.DateField('作業終了予定日', null=True, blank=True)
    worker_count = models.PositiveIntegerField('作業人数', null=True, blank=True)
    
    # 工具・設備情報（工具持込申請用）
    tool_list = models.TextField('持込工具リスト', blank=True, help_text='改行区切りで入力')
    
    # 制限エリア情報
    restricted_area = models.CharField('制限エリア名', max_length=200, blank=True)
    entry_purpose = models.TextField('立入目的', blank=True)
    entry_members = models.TextField('立入者リスト', blank=True, help_text='氏名、所属を改行区切りで入力')
    
    # 工事情報
    contractor_name = models.CharField('施工業者名', max_length=200, blank=True)
    
    # ステータス
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # 日時情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    submitted_at = models.DateTimeField('申請日時', null=True, blank=True)
    received_at = models.DateTimeField('受付日時', null=True, blank=True)
    approved_at = models.DateTimeField('承認日時', null=True, blank=True)
    
    class Meta:
        verbose_name = '申請'
        verbose_name_plural = '申請'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['application_number']),
            models.Index(fields=['applicant', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # 申請番号の自動生成（例: APP20241227001）
            today = timezone.now().strftime('%Y%m%d')
            last_app = Application.objects.filter(
                application_number__startswith=f'APP{today}'
            ).order_by('-application_number').first()
            
            if last_app:
                last_num = int(last_app.application_number[-3:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.application_number = f'APP{today}{new_num:03d}'
        
        # 申請者の企業名を自動設定
        if not self.company_name and hasattr(self.applicant, 'profile'):
            self.company_name = self.applicant.profile.company_name
        
        super().save(*args, **kwargs)
    
    def submit(self):
        """申請を提出"""
        if self.status == 'draft' or self.status == 'returned':
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save()
            
            # メール通知: 受付担当へ
            self.send_notification_to_receivers()
            return True
        return False
    
    def receive(self, receiver):
        """申請を受付"""
        if self.status == 'submitted':
            self.status = 'received'
            self.received_at = timezone.now()
            self.save()
            
            # メール通知: 承認者と申請者へ
            self.send_notification_to_approvers()
            self.send_notification_to_applicant('受付完了', '申請が受付されました。')
            return True
        return False
    
    def approve(self, approver):
        """申請を承認"""
        if self.status == 'received':
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.save()
            
            # メール通知: 申請者へ
            self.send_notification_to_applicant('承認完了', '申請が承認されました。')
            return True
        return False
    
    def reject(self, processor, reason):
        """申請を却下"""
        if self.status in ['submitted', 'received']:
            self.status = 'rejected'
            self.save()
            
            # メール通知: 申請者へ
            self.send_notification_to_applicant('却下通知', f'申請が却下されました。\n理由: {reason}')
            return True
        return False
    
    def return_to_applicant(self, receiver, reason):
        """申請を差し戻し"""
        if self.status == 'submitted':
            self.status = 'returned'
            self.save()
            
            # メール通知: 申請者へ
            self.send_notification_to_applicant('差し戻し通知', f'申請が差し戻されました。修正後、再度提出してください。\n理由: {reason}')
            return True
        return False
    
    def send_notification_to_receivers(self):
        """申請種別に設定された受付ロールのメンバーへメール通知"""
        try:
            # 申請種別設定を取得（キャッシュ使用）
            cache_key = f'application_type_config_{self.application_type}'
            type_config = cache.get(cache_key)
            
            if not type_config:
                type_config = ApplicationTypeConfig.objects.select_related('receiver_role').get(
                    application_type=self.application_type,
                    is_active=True
                )
                cache.set(cache_key, type_config, 3600)
            
            # 受付ロールのメンバーを取得
            receivers = type_config.receiver_role.members.filter(
                user__is_active=True
            ).select_related('user')
            
            recipient_list = [member.user.email for member in receivers if member.user.email]
            
        except ApplicationTypeConfig.DoesNotExist:
            # 設定がない場合はフォールバック（既存ロジック）
            receivers = User.objects.filter(profile__role='receiver', is_active=True)
            recipient_list = [user.email for user in receivers if user.email]
        
        if not recipient_list:
            return
        
        subject = f'【新規申請】{self.application_number} - {self.get_application_type_display()}'
        message = f'''
新しい申請が提出されました。

申請番号: {self.application_number}
申請種別: {self.get_application_type_display()}
タイトル: {self.title}
申請企業: {self.company_name}
申請者: {self.applicant.get_full_name() or self.applicant.username}
申請日時: {self.submitted_at.strftime('%Y/%m/%d %H:%M')}

詳細は以下のURLからご確認ください。
{settings.SITE_URL}/workflow/{self.pk}/
'''
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)
    
    def send_notification_to_approvers(self):
        """申請種別に設定された承認ロールのメンバーへメール通知"""
        try:
            # 申請種別設定を取得（キャッシュ使用）
            cache_key = f'application_type_config_{self.application_type}'
            type_config = cache.get(cache_key)
            
            if not type_config:
                type_config = ApplicationTypeConfig.objects.select_related('approver_role').get(
                    application_type=self.application_type,
                    is_active=True
                )
                cache.set(cache_key, type_config, 3600)
            
            # 承認ロールのメンバーを取得
            approvers = type_config.approver_role.members.filter(
                user__is_active=True
            ).select_related('user')
            
            recipient_list = [member.user.email for member in approvers if member.user.email]
            
        except ApplicationTypeConfig.DoesNotExist:
            # 設定がない場合はフォールバック（既存ロジック）
            approvers = User.objects.filter(profile__role='approver', is_active=True)
            recipient_list = [user.email for user in approvers if user.email]
        
        if not recipient_list:
            return
        
        subject = f'【承認依頼】{self.application_number} - {self.get_application_type_display()}'
        message = f'''
受付完了した申請の承認をお願いします。

申請番号: {self.application_number}
申請種別: {self.get_application_type_display()}
タイトル: {self.title}
申請企業: {self.company_name}
受付日時: {self.received_at.strftime('%Y/%m/%d %H:%M')}

詳細は以下のURLからご確認ください。
{settings.SITE_URL}/workflow/{self.pk}/
'''
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)
    
    def send_notification_to_applicant(self, subject_prefix, body_message):
        """申請者へメール通知"""
        if self.applicant.email:
            subject = f'【{subject_prefix}】{self.application_number} - {self.get_application_type_display()}'
            message = f'''
{body_message}

申請番号: {self.application_number}
申請種別: {self.get_application_type_display()}
タイトル: {self.title}

詳細は以下のURLからご確認ください。
{settings.SITE_URL}/workflow/{self.pk}/
'''
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.applicant.email], fail_silently=True)
    
    def can_edit(self, user):
        """編集可能か判定"""
        return self.applicant == user and self.status in ['draft', 'returned']
    
    def can_submit(self, user):
        """提出可能か判定"""
        return self.applicant == user and self.status in ['draft', 'returned']
    
    def can_receive(self, user):
        """受付可能か判定（ロールベース権限チェック）"""
        if not hasattr(user, 'profile'):
            return False
        
        # 管理者は常に可能
        if user.profile.role == 'admin':
            return True
        
        # ステータスチェック
        if self.status != 'submitted':
            return False
        
        # 申請種別の受付ロールに所属しているかチェック
        try:
            cache_key = f'application_type_config_{self.application_type}'
            type_config = cache.get(cache_key)
            
            if not type_config:
                type_config = ApplicationTypeConfig.objects.select_related('receiver_role').get(
                    application_type=self.application_type,
                    is_active=True
                )
                cache.set(cache_key, type_config, 3600)
            
            return type_config.receiver_role.members.filter(user=user).exists()
            
        except ApplicationTypeConfig.DoesNotExist:
            # 設定がない場合はフォールバック（既存ロール判定）
            return user.profile.role == 'receiver'
    
    def can_approve(self, user):
        """承認可能か判定（ロールベース権限チェック）"""
        if not hasattr(user, 'profile'):
            return False
        
        # 管理者は常に可能
        if user.profile.role == 'admin':
            return True
        
        # ステータスチェック
        if self.status != 'received':
            return False
        
        # 申請種別の承認ロールに所属しているかチェック
        try:
            cache_key = f'application_type_config_{self.application_type}'
            type_config = cache.get(cache_key)
            
            if not type_config:
                type_config = ApplicationTypeConfig.objects.select_related('approver_role').get(
                    application_type=self.application_type,
                    is_active=True
                )
                cache.set(cache_key, type_config, 3600)
            
            return type_config.approver_role.members.filter(user=user).exists()
            
        except ApplicationTypeConfig.DoesNotExist:
            # 設定がない場合はフォールバック（既存ロール判定）
            return user.profile.role == 'approver'
    
    def can_return(self, user):
        """差し戻し可能か判定"""
        return (hasattr(user, 'profile') and 
                user.profile.role in ['receiver', 'admin'] and 
                self.status == 'submitted')


class WorkflowStep(models.Model):
    """ワークフローステップ（履歴記録）"""
    STEP_TYPE_CHOICES = [
        ('submit', '申請'),
        ('receive', '受付'),
        ('approve', '承認'),
        ('reject', '却下'),
        ('return', '差し戻し'),
    ]
    
    STEP_STATUS_CHOICES = [
        ('pending', '未処理'),
        ('processing', '処理中'),
        ('completed', '完了'),
        ('rejected', '却下'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='workflow_steps', verbose_name='申請')
    step_type = models.CharField('ステップ種別', max_length=20, choices=STEP_TYPE_CHOICES)
    processor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_steps', verbose_name='処理者')
    status = models.CharField('ステータス', max_length=20, choices=STEP_STATUS_CHOICES, default='pending')
    comment = models.TextField('コメント', blank=True)
    processed_at = models.DateTimeField('処理日時', null=True, blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    
    class Meta:
        verbose_name = 'ワークフローステップ'
        verbose_name_plural = 'ワークフローステップ'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.application.application_number} - {self.get_step_type_display()}"


class Comment(models.Model):
    """コメント"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='comments', verbose_name='申請')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='コメント者')
    content = models.TextField('コメント内容')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    
    class Meta:
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y/%m/%d %H:%M')}"


class Attachment(models.Model):
    """添付ファイル"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='attachments', verbose_name='申請')
    file = models.FileField('ファイル', upload_to='workflow/attachments/%Y/%m/%d/')
    filename = models.CharField('ファイル名', max_length=255)
    file_size = models.PositiveIntegerField('ファイルサイズ(bytes)', default=0)
    uploaded_at = models.DateTimeField('アップロード日時', auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='アップロード者')
    
    class Meta:
        verbose_name = '添付ファイル'
        verbose_name_plural = '添付ファイル'
        ordering = ['uploaded_at']
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """ファイルサイズを人間が読みやすい形式で返す"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def file_name(self):
        """ファイル名を返す（filenameがない場合はfileから取得）"""
        return self.filename if self.filename else (self.file.name.split('/')[-1] if self.file else '')
