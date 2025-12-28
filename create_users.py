"""
スーパーユーザーとテストユーザーを作成するスクリプト
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from workflow.models import UserProfile

# スーパーユーザー作成
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin',
        first_name='管理者',
        last_name='システム'
    )
    UserProfile.objects.create(
        user=admin,
        role='admin',
        company_name='XYZ製作所',
        department='システム管理部',
        phone_number='03-1234-5678'
    )
    print('✅ スーパーユーザー (admin/admin) を作成しました')
else:
    print('⚠️  スーパーユーザー admin は既に存在します')

# テストユーザー1: 取引先
if not User.objects.filter(username='vendor1').exists():
    vendor = User.objects.create_user(
        username='vendor1',
        email='vendor1@abc-corp.com',
        password='vendor1',
        first_name='太郎',
        last_name='山田'
    )
    UserProfile.objects.create(
        user=vendor,
        role='vendor',
        company_name='ABC株式会社',
        department='施工部',
        phone_number='03-2222-3333'
    )
    print('✅ 取引先ユーザー (vendor1/vendor1) を作成しました')
else:
    print('⚠️  取引先ユーザー vendor1 は既に存在します')

# テストユーザー2: 受付担当
if not User.objects.filter(username='receiver1').exists():
    receiver = User.objects.create_user(
        username='receiver1',
        email='receiver1@xyz-mfg.com',
        password='receiver1',
        first_name='花子',
        last_name='佐藤'
    )
    UserProfile.objects.create(
        user=receiver,
        role='receiver',
        company_name='XYZ製作所',
        department='総務部',
        phone_number='03-1234-5679'
    )
    print('✅ 受付担当ユーザー (receiver1/receiver1) を作成しました')
else:
    print('⚠️  受付担当ユーザー receiver1 は既に存在します')

# テストユーザー3: 承認者
if not User.objects.filter(username='approver1').exists():
    approver = User.objects.create_user(
        username='approver1',
        email='approver1@xyz-mfg.com',
        password='approver1',
        first_name='次郎',
        last_name='鈴木'
    )
    UserProfile.objects.create(
        user=approver,
        role='approver',
        company_name='XYZ製作所',
        department='管理部',
        phone_number='03-1234-5680'
    )
    print('✅ 承認者ユーザー (approver1/approver1) を作成しました')
else:
    print('⚠️  承認者ユーザー approver1 は既に存在します')

print('\n🎉 セットアップ完了！')
print('\n📋 作成されたユーザー:')
print('   管理者:     admin/admin')
print('   取引先:     vendor1/vendor1    (ABC株式会社)')
print('   受付担当:   receiver1/receiver1 (XYZ製作所)')
print('   承認者:     approver1/approver1 (XYZ製作所)')
print('\n🚀 次のコマンドでサーバーを起動してください:')
print('   python manage.py runserver')
print('\n🌐 アクセス先:')
print('   ログイン:       http://localhost:8000/accounts/login/')
print('   ダッシュボード: http://localhost:8000/workflow/')
print('   管理画面:       http://localhost:8000/admin/')
