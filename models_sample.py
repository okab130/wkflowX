"""
業務ワークフローシステムのモデル定義
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """ユーザープロファイル拡張"""
    ROLE_CHOICES = [
        ('applicant', '申請者'),
        ('receiver', '受付担当'),
        ('approver', '承認者'),
        ('admin', '管理者'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('役割', max_length=20, choices=ROLE_CHOICES, default='applicant')
    department = models.CharField('部署', max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'ユーザープロファイル'
        verbose_name_plural = 'ユーザープロファイル'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Application(models.Model):
    """申請"""
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('submitted', '申請中'),
        ('received', '受付済'),
        ('approved', '承認済'),
        ('rejected', '却下'),
    ]
    
    APPLICATION_TYPE_CHOICES = [
        ('expense', '経費申請'),
        ('leave', '休暇申請'),
        ('purchase', '購買申請'),
        ('other', 'その他'),
    ]
    
    application_number = models.CharField('申請番号', max_length=20, unique=True, editable=False)
    application_type = models.CharField('申請種別', max_length=20, choices=APPLICATION_TYPE_CHOICES)
    title = models.CharField('タイトル', max_length=200)
    content = models.TextField('申請内容')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', verbose_name='申請者')
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # オプションフィールド
    amount = models.DecimalField('金額', max_digits=10, decimal_places=0, null=True, blank=True)
    desired_date = models.DateField('希望日', null=True, blank=True)
    
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    submitted_at = models.DateTimeField('申請日時', null=True, blank=True)
    
    class Meta:
        verbose_name = '申請'
        verbose_name_plural = '申請'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.application_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # 申請番号の自動生成（例: APP20240101001）
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
        
        super().save(*args, **kwargs)
    
    def submit(self):
        """申請を提出"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save()
            return True
        return False
    
    def can_edit(self, user):
        """編集可能か判定"""
        return self.applicant == user and self.status == 'draft'
    
    def can_receive(self, user):
        """受付可能か判定"""
        return (hasattr(user, 'profile') and 
                user.profile.role in ['receiver', 'admin'] and 
                self.status == 'submitted')
    
    def can_approve(self, user):
        """承認可能か判定"""
        return (hasattr(user, 'profile') and 
                user.profile.role in ['approver', 'admin'] and 
                self.status == 'received')


class WorkflowStep(models.Model):
    """ワークフローステップ"""
    STEP_TYPE_CHOICES = [
        ('submit', '申請'),
        ('receive', '受付'),
        ('approve', '承認'),
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
        super().save(*args, **kwargs)
