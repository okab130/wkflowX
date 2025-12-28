"""
業務ワークフローシステムのフォーム（製造業・建設業向け）
"""
from django import forms
from .models import Application, Comment, Attachment


class ApplicationForm(forms.ModelForm):
    """申請フォーム"""
    
    class Meta:
        model = Application
        fields = [
            'application_type', 'title', 'content',
            'work_location', 'work_start_date', 'work_end_date', 'worker_count',
            'tool_list', 'restricted_area', 'entry_purpose', 'entry_members',
            'contractor_name'
        ]
        widgets = {
            'application_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '申請タイトルを入力'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '申請内容を詳しく記入してください'
            }),
            'work_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: A棟3階'}),
            'work_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'work_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'worker_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'tool_list': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '持込工具を1行ずつ入力\n例:\n電動ドライバー\nハンマー\n測定器'
            }),
            'restricted_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: クリーンルームA'}),
            'entry_purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '立入目的を記入してください'
            }),
            'entry_members': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '立入者を1行ずつ入力\n例:\n山田太郎 (ABC株式会社)\n佐藤花子 (ABC株式会社)'
            }),
            'contractor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '施工業者名'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 申請種別に応じて必須フィールドを動的に設定
        self.fields['work_location'].required = False
        self.fields['work_start_date'].required = False
        self.fields['work_end_date'].required = False
        self.fields['worker_count'].required = False
        self.fields['tool_list'].required = False
        self.fields['restricted_area'].required = False
        self.fields['entry_purpose'].required = False
        self.fields['entry_members'].required = False
        self.fields['contractor_name'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        application_type = cleaned_data.get('application_type')
        
        # 作業申請
        if application_type == 'work':
            if not cleaned_data.get('work_location'):
                self.add_error('work_location', '作業申請の場合、作業場所は必須です。')
            if not cleaned_data.get('work_start_date'):
                self.add_error('work_start_date', '作業申請の場合、作業開始予定日は必須です。')
            if not cleaned_data.get('worker_count'):
                self.add_error('worker_count', '作業申請の場合、作業人数は必須です。')
        
        # 工事申請
        elif application_type == 'construction':
            if not cleaned_data.get('work_location'):
                self.add_error('work_location', '工事申請の場合、工事場所は必須です。')
            if not cleaned_data.get('work_start_date'):
                self.add_error('work_start_date', '工事申請の場合、工事開始予定日は必須です。')
            if not cleaned_data.get('work_end_date'):
                self.add_error('work_end_date', '工事申請の場合、工事終了予定日は必須です。')
            if not cleaned_data.get('contractor_name'):
                self.add_error('contractor_name', '工事申請の場合、施工業者名は必須です。')
            if not cleaned_data.get('worker_count'):
                self.add_error('worker_count', '工事申請の場合、工事人数は必須です。')
        
        # 工具持込申請
        elif application_type == 'tool_bringin':
            if not cleaned_data.get('tool_list'):
                self.add_error('tool_list', '工具持込申請の場合、持込工具リストは必須です。')
            if not cleaned_data.get('work_start_date'):
                self.add_error('work_start_date', '工具持込申請の場合、使用開始予定日は必須です。')
            if not cleaned_data.get('work_end_date'):
                self.add_error('work_end_date', '工具持込申請の場合、返却予定日は必須です。')
        
        # 制限エリア立入申請
        elif application_type == 'restricted_entry':
            if not cleaned_data.get('restricted_area'):
                self.add_error('restricted_area', '制限エリア立入申請の場合、エリア名は必須です。')
            if not cleaned_data.get('entry_purpose'):
                self.add_error('entry_purpose', '制限エリア立入申請の場合、立入目的は必須です。')
            if not cleaned_data.get('entry_members'):
                self.add_error('entry_members', '制限エリア立入申請の場合、立入者リストは必須です。')
            if not cleaned_data.get('work_start_date'):
                self.add_error('work_start_date', '制限エリア立入申請の場合、立入予定日は必須です。')
        
        # 制限エリア工具持込申請
        elif application_type == 'restricted_tool':
            if not cleaned_data.get('restricted_area'):
                self.add_error('restricted_area', '制限エリア工具持込申請の場合、エリア名は必須です。')
            if not cleaned_data.get('tool_list'):
                self.add_error('tool_list', '制限エリア工具持込申請の場合、持込工具リストは必須です。')
            if not cleaned_data.get('entry_members'):
                self.add_error('entry_members', '制限エリア工具持込申請の場合、立入者リストは必須です。')
            if not cleaned_data.get('work_start_date'):
                self.add_error('work_start_date', '制限エリア工具持込申請の場合、使用開始予定日は必須です。')
        
        # 日付の妥当性チェック
        work_start_date = cleaned_data.get('work_start_date')
        work_end_date = cleaned_data.get('work_end_date')
        if work_start_date and work_end_date:
            if work_end_date < work_start_date:
                self.add_error('work_end_date', '終了日は開始日より後の日付を指定してください。')
        
        return cleaned_data


class CommentForm(forms.ModelForm):
    """コメントフォーム"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'コメントを入力してください'
            }),
        }


class AttachmentForm(forms.ModelForm):
    """添付ファイルフォーム"""
    
    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # ファイルサイズチェック（10MB制限）
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('ファイルサイズは10MB以下にしてください。')
            
            # ファイル拡張子チェック
            allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.zip']
            file_ext = file.name.lower()[file.name.rfind('.'):]
            if file_ext not in allowed_extensions:
                raise forms.ValidationError(f'許可されていないファイル形式です。許可形式: {", ".join(allowed_extensions)}')
        
        return file
