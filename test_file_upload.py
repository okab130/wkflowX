"""
ファイルアップロードのテスト
"""
import os
import sys
import django

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from workflow.models import Application
import io

# テストクライアント
client = Client()

# ユーザーを取得（存在する場合）
try:
    user = User.objects.first()
    if not user:
        print("エラー: ユーザーが存在しません")
        sys.exit(1)
    
    print(f"テストユーザー: {user.username}")
    
    # ログイン
    client.force_login(user)
    
    # テストファイルを作成
    test_file = SimpleUploadedFile(
        "test.txt",
        b"test file content",
        content_type="text/plain"
    )
    
    # POSTデータ
    data = {
        'application_type': 'work',
        'title': 'テスト申請',
        'content': 'テスト内容',
        'work_location': 'テスト場所',
        'work_start_date': '2025-12-28',
        'worker_count': 5,
        'submit': 'true',
    }
    
    # ファイルデータ
    files = {
        'attachments': test_file
    }
    
    print("\n=== POSTリクエスト送信 ===")
    response = client.post('/workflow/create/', data=data, files=files, follow=True)
    
    print(f"ステータスコード: {response.status_code}")
    print(f"リダイレクト先: {response.redirect_chain}")
    
    # エラーメッセージを確認
    if hasattr(response, 'context') and response.context:
        if 'form' in response.context:
            form = response.context['form']
            if form.errors:
                print(f"\nフォームエラー: {form.errors}")
    
    # 最新の申請を確認
    latest_app = Application.objects.order_by('-created_at').first()
    if latest_app:
        print(f"\n最新申請: {latest_app.application_number}")
        print(f"添付ファイル数: {latest_app.attachments.count()}")
        for att in latest_app.attachments.all():
            print(f"  - {att.filename}")
    
except Exception as e:
    print(f"エラー: {str(e)}")
    import traceback
    traceback.print_exc()
