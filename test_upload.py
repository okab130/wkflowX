"""
ファイルアップロードのテストスクリプト
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from workflow.models import Application, Attachment
from django.contrib.auth.models import User

# 申請を確認
apps = Application.objects.all()
print(f"申請数: {apps.count()}")

for app in apps:
    print(f"\n申請番号: {app.application_number}")
    print(f"タイトル: {app.title}")
    print(f"添付ファイル数: {app.attachments.count()}")
    
    for attachment in app.attachments.all():
        print(f"  - {attachment.filename} ({attachment.file_size} bytes)")
        print(f"    ファイルパス: {attachment.file.path}")
        print(f"    存在する: {os.path.exists(attachment.file.path)}")
