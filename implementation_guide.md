# Django 業務ワークフローシステム 実装手順書（製造業・建設業向け）

## システム概要

### 対象業種
製造業・建設業における取引先企業の作業申請管理システム

### 申請種別
1. 作業申請
2. 工事申請
3. 工具持込申請
4. 制限エリア立入申請
5. 制限エリア工具持込申請

### ユーザー種別
- 取引先: 申請の作成・提出
- 受付担当: 申請内容の確認・受理・差し戻し
- 承認者: 最終承認・却下
- 管理者: システム全体の管理

### 主要機能
- 申請CRUD（作成・閲覧・編集・削除）
- 3段階ワークフロー（申請→受付→承認）
- 差し戻し・再申請機能
- 添付ファイル管理
- コメント機能
- メール通知（全プロセス）
- 検索・フィルタリング

## 前提条件
- Python 3.8以上
- Django 4.2以上

## 1. プロジェクトのセットアップ

### 1.1 仮想環境の作成と有効化
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 1.2 Djangoと依存パッケージのインストール
```bash
pip install django
pip install pillow  # 画像・ファイル処理用
pip install python-decouple  # 環境変数管理用（オプション）
pip freeze > requirements.txt
```

### 1.3 Djangoプロジェクトの作成
```bash
django-admin startproject config .
python manage.py startapp workflow
```

## 2. アプリケーションの設定

### 2.1 settings.py の設定
`settings_example.py` を参照して、以下を設定:

**必須設定:**
```python
# アプリケーション追加
INSTALLED_APPS = [
    # ...
    'workflow',
]

# 日本語化
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'

# メディアファイル（添付ファイル用）
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# メール設定（開発環境）
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SITE_URL = 'http://localhost:8000'
DEFAULT_FROM_EMAIL = 'workflow-system@example.com'

# ログイン設定
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/workflow/'
LOGOUT_REDIRECT_URL = '/'
```

**本番環境では追加設定:**
- SMTP設定（メール送信）
- セキュリティ設定（SSL、Cookie設定）
- データベース設定（PostgreSQL推奨）
- 環境変数管理（SECRET_KEY等）

### 2.2 プロジェクトのurls.py設定
```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('workflow/', include('workflow.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## 3. モデルの実装

### 3.1 models.pyを作成
`models.py` の内容を `workflow/models.py` にコピー

**主要モデル:**
- UserProfile: ユーザー拡張（役割、企業名、連絡先）
- Application: 申請（5種類の申請に対応）
- WorkflowStep: ワークフロー履歴
- Comment: コメント
- Attachment: 添付ファイル

**主要メソッド:**
- `submit()`: 申請提出＋メール通知
- `receive()`: 受付処理＋メール通知
- `approve()`: 承認＋メール通知
- `reject()`: 却下＋メール通知
- `return_to_applicant()`: 差し戻し＋メール通知

### 3.2 マイグレーションの実行
```bash
python manage.py makemigrations workflow
python manage.py migrate
```

## 4. 管理画面の設定

### 4.1 admin.py の作成
`admin.py` の内容を `workflow/admin.py` にコピー

**管理画面の特徴:**
- ステータスバッジ表示（色分け）
- フィールドセット（折りたたみ可能）
- 検索・フィルタリング機能
- 日付階層ナビゲーション
- 読み取り専用フィールドの設定

## 5. ビュー・フォーム・URLの実装

### 5.1 forms.py を作成
`forms.py` の内容を `workflow/forms.py` にコピー

**フォームの特徴:**
- 申請種別に応じた動的バリデーション
- 必須項目の自動チェック
- 日付の妥当性検証
- ファイルサイズ・拡張子チェック（10MB制限）

### 5.2 views.py を作成
`views.py` の内容を `workflow/views.py` にコピー

**主要ビュー:**
- DashboardView: 役割別ダッシュボード＋検索・フィルター
- ApplicationCreateView: 申請作成（下書き/提出）
- ApplicationDetailView: 申請詳細＋権限判定
- 受付・承認・差し戻しの各処理ビュー
- 添付ファイルアップロード・削除

### 5.3 urls.py を作成
`urls.py` の内容を `workflow/urls.py` にコピー

## 6. テンプレートの作成

### 6.1 ディレクトリ構成
```
workflow/
  templates/
    workflow/
      base.html
      dashboard.html
      application_form.html
      application_detail.html
      confirm_submit.html
      confirm_receive.html
      confirm_approve.html
      my_applications.html
      pending_receive.html
      pending_approve.html
```

### 6.2 base.htmlの作成例
```html
<!-- workflow/templates/workflow/base.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}業務ワークフローシステム{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'workflow:dashboard' %}">ワークフローシステム</a>
            <div class="navbar-nav ms-auto">
                {% if user.is_authenticated %}
                    <span class="navbar-text me-3">{{ user.username }}</span>
                    <a class="nav-link" href="{% url 'workflow:my_applications' %}">自分の申請</a>
                    {% if user.profile.role == 'receiver' or user.profile.role == 'admin' %}
                        <a class="nav-link" href="{% url 'workflow:pending_receive' %}">受付待ち</a>
                    {% endif %}
                    {% if user.profile.role == 'approver' or user.profile.role == 'admin' %}
                        <a class="nav-link" href="{% url 'workflow:pending_approve' %}">承認待ち</a>
                    {% endif %}
                    <a class="nav-link" href="{% url 'logout' %}">ログアウト</a>
                {% else %}
                    <a class="nav-link" href="{% url 'login' %}">ログイン</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        {% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

## 7. 初期データの作成

### 7.1 スーパーユーザーの作成
```bash
python manage.py createsuperuser
```

### 7.2 テストユーザーの作成

**管理画面から作成:**
1. http://localhost:8000/admin/ にアクセス
2. Usersから以下のユーザーを作成:
   - 取引先ユーザー（vendor1）
   - 受付担当ユーザー（receiver1）
   - 承認者ユーザー（approver1）

3. User profilesで各ユーザーに役割と企業名を設定:
   ```
   vendor1:
     - 役割: 取引先
     - 企業名: ABC株式会社
     - 部署: 施工部
   
   receiver1:
     - 役割: 受付担当
     - 企業名: XYZ製作所（自社）
     - 部署: 総務部
   
   approver1:
     - 役割: 承認者
     - 企業名: XYZ製作所（自社）
     - 部署: 管理部
   ```

## 8. 開発サーバーの起動

```bash
python manage.py runserver
```

http://localhost:8000/workflow/ にアクセス

## 9. テストの実施

### 9.1 基本的なワークフローテスト

**シナリオ1: 作業申請の正常フロー**
1. 取引先ユーザー（vendor1）でログイン
2. 「新規申請」から作業申請を作成
   - タイトル: 「A棟3階配管工事」
   - 作業場所: A棟3階
   - 作業開始日: 明日の日付
   - 作業人数: 5
3. 下書き保存 → 内容確認 → 申請提出
4. メール通知を確認（コンソール出力）

5. 受付担当（receiver1）でログイン
6. 「受付待ち」から該当申請を開く
7. 内容確認 → 受付処理
8. コメント追加: 「内容確認しました」

9. 承認者（approver1）でログイン
10. 「承認待ち」から該当申請を開く
11. 内容確認 → 承認
12. コメント追加: 「承認します」

13. 取引先ユーザーでログイン
14. 「自分の申請」でステータスが「承認済」を確認
15. メール通知を確認

**シナリオ2: 差し戻し・再申請フロー**
1. 取引先ユーザーで工具持込申請を作成・提出
2. 受付担当で内容確認後、差し戻し
   - 理由: 「工具リストに型番が未記入です」
3. 取引先ユーザーで差し戻し通知を確認
4. 申請を編集（工具リストに型番追加）
5. 再提出
6. 受付→承認の正常フロー

**シナリオ3: 添付ファイル機能テスト**
1. 工事申請作成時に図面PDFを添付
2. ファイルサイズ・拡張子のチェック
3. ダウンロード確認
4. 削除機能のテスト

### 9.2 単体テストの作成例
```python
# workflow/tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Application, UserProfile, WorkflowStep

class ApplicationWorkflowTest(TestCase):
    def setUp(self):
        # テストユーザー作成
        self.vendor_user = User.objects.create_user('vendor', 'vendor@test.com', 'password')
        self.receiver_user = User.objects.create_user('receiver', 'receiver@test.com', 'password')
        self.approver_user = User.objects.create_user('approver', 'approver@test.com', 'password')
        
        # プロファイル作成
        UserProfile.objects.create(user=self.vendor_user, role='vendor', company_name='ABC株式会社')
        UserProfile.objects.create(user=self.receiver_user, role='receiver', company_name='XYZ製作所')
        UserProfile.objects.create(user=self.approver_user, role='approver', company_name='XYZ製作所')
        
        self.client = Client()
    
    def test_application_creation(self):
        """申請が正しく作成されるか"""
        app = Application.objects.create(
            application_type='work',
            title='テスト作業申請',
            content='テスト内容',
            applicant=self.vendor_user,
            work_location='A棟',
            work_start_date=timezone.now().date() + timedelta(days=1),
            worker_count=3
        )
        self.assertTrue(app.application_number.startswith('APP'))
        self.assertEqual(app.status, 'draft')
        self.assertEqual(app.company_name, 'ABC株式会社')
    
    def test_application_submit(self):
        """申請が正しく提出されるか"""
        app = Application.objects.create(
            application_type='work',
            title='テスト作業申請',
            content='テスト内容',
            applicant=self.vendor_user,
            work_location='A棟',
            work_start_date=timezone.now().date() + timedelta(days=1),
            worker_count=3
        )
        result = app.submit()
        self.assertTrue(result)
        self.assertEqual(app.status, 'submitted')
        self.assertIsNotNone(app.submitted_at)
    
    def test_application_workflow(self):
        """完全なワークフローのテスト"""
        # 申請作成・提出
        app = Application.objects.create(
            application_type='work',
            title='テスト作業申請',
            content='テスト内容',
            applicant=self.vendor_user,
            work_location='A棟',
            work_start_date=timezone.now().date() + timedelta(days=1),
            worker_count=3
        )
        app.submit()
        self.assertEqual(app.status, 'submitted')
        
        # 受付処理
        app.receive(self.receiver_user)
        self.assertEqual(app.status, 'received')
        self.assertIsNotNone(app.received_at)
        
        # 承認処理
        app.approve(self.approver_user)
        self.assertEqual(app.status, 'approved')
        self.assertIsNotNone(app.approved_at)
    
    def test_application_return(self):
        """差し戻し・再申請のテスト"""
        app = Application.objects.create(
            application_type='work',
            title='テスト作業申請',
            content='テスト内容',
            applicant=self.vendor_user,
            work_location='A棟',
            work_start_date=timezone.now().date() + timedelta(days=1),
            worker_count=3
        )
        app.submit()
        
        # 差し戻し
        app.return_to_applicant(self.receiver_user, '情報不足')
        self.assertEqual(app.status, 'returned')
        
        # 再申請
        app.content = '詳細情報を追加'
        result = app.submit()
        self.assertTrue(result)
        self.assertEqual(app.status, 'submitted')
    
    def test_permission_checks(self):
        """権限チェックのテスト"""
        app = Application.objects.create(
            application_type='work',
            title='テスト作業申請',
            content='テスト内容',
            applicant=self.vendor_user,
            work_location='A棟',
            work_start_date=timezone.now().date() + timedelta(days=1),
            worker_count=3
        )
        
        # 取引先ユーザーは編集可能
        self.assertTrue(app.can_edit(self.vendor_user))
        
        # 受付担当は編集不可
        self.assertFalse(app.can_edit(self.receiver_user))
        
        app.submit()
        
        # 受付担当は受付可能
        self.assertTrue(app.can_receive(self.receiver_user))
        
        # 承認者は受付不可
        self.assertFalse(app.can_receive(self.approver_user))
```

実行: `python manage.py test workflow`

## 10. 追加機能の実装（オプション）

### 10.1 メール通知の本番環境設定
```python
# settings.py（本番環境）
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # または企業のSMTPサーバー
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = 'workflow-system@your-company.com'
SITE_URL = 'https://your-domain.com'
```

### 10.2 Excel/PDFエクスポート機能
```bash
pip install openpyxl reportlab
```

### 10.3 検索機能の強化（全文検索）
```bash
pip install django-haystack elasticsearch
```

### 10.4 カレンダー表示（作業予定）
```bash
pip install django-scheduler
```

### 10.5 多段階承認フロー
- ApprovalLevel モデルの追加
- 承認順序の管理
- 並列承認・順次承認の選択

### 10.6 ダッシュボードの統計・グラフ
```bash
pip install django-chartjs
```

### 10.7 モバイル対応
- レスポンシブデザインの改善
- PWA（Progressive Web App）化

## トラブルシューティング

### マイグレーションエラー
```bash
python manage.py makemigrations --empty workflow
python manage.py migrate --fake workflow zero
python manage.py migrate workflow
```

### 静的ファイルが表示されない
```bash
python manage.py collectstatic
```

## 参考リンク
- Django公式ドキュメント: https://docs.djangoproject.com/
- Django Best Practices: https://django-best-practices.readthedocs.io/
