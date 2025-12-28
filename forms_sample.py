"""
業務ワークフローシステムのフォーム
"""
from django import forms
from .models import Application, Comment


class ApplicationForm(forms.ModelForm):
    """申請フォーム"""
    
    class Meta:
        model = Application
        fields = ['application_type', 'title', 'content', 'amount', 'desired_date']
        widgets = {
            'application_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '申請タイトルを入力'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '申請内容を詳しく記入してください'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '金額（円）'}),
            'desired_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean_amount(self):
        """金額のバリデーション"""
        amount = self.cleaned_data.get('amount')
        application_type = self.cleaned_data.get('application_type')
        
        if application_type == 'expense' and not amount:
            raise forms.ValidationError('経費申請の場合、金額は必須です。')
        
        if amount and amount < 0:
            raise forms.ValidationError('金額は0以上で入力してください。')
        
        return amount


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
