# テンプレート設定ガイド

## 📁 テンプレートファイル構成

```
templates/
├── workflow/
│   ├── base.html                   # ベーステンプレート
│   ├── dashboard.html              # ダッシュボード
│   ├── application_form.html       # 申請作成・編集フォーム
│   ├── application_detail.html     # 申請詳細
│   ├── confirm_submit.html         # 申請提出確認
│   ├── confirm_receive.html        # 受付処理確認
│   ├── confirm_approve.html        # 承認処理確認
│   ├── my_applications.html        # 自分の申請一覧
│   ├── pending_receive.html        # 受付待ち一覧
│   └── pending_approve.html        # 承認待ち一覧
└── registration/
    └── login.html                  # ログイン画面
```

## 🎨 デザインの特徴

### Bootstrap 5 使用
- レスポンシブデザイン対応
- モダンなUIコンポーネント
- モバイルフレンドリー

### カラーリング
- **プライマリー**: 青系（#0d6efd）
- **成功**: 緑系（#198754）- 承認・受付
- **警告**: オレンジ系（#ffc107）- 差し戻し
- **危険**: 赤系（#dc3545）- 却下
- **情報**: 水色系（#0dcaf0）- 申請中

### アイコン
Bootstrap Icons を使用:
- 📄 `bi-file-text` - 申請
- 📤 `bi-send` - 提出
- 📥 `bi-inbox` - 受付
- ✅ `bi-check-circle` - 承認
- ❌ `bi-x-circle` - 却下
- 🔙 `bi-arrow-return-left` - 差し戻し

## ⚙️ settings.py の設定

テンプレートディレクトリを認識させるため、以下を設定:

```python
# settings.py

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 追加
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

## 🖼️ 画面一覧

### 1. ログイン画面 (login.html)
- グラデーション背景
- シンプルなログインフォーム
- エラーメッセージ表示

### 2. ダッシュボード (dashboard.html)
- 役割別の統計カード表示
- 検索・フィルタリング機能
- 申請一覧テーブル
- ページネーション

### 3. 申請作成フォーム (application_form.html)
- 申請種別に応じた動的フォーム表示
- 必須項目の明示
- ヘルプアコーディオン
- 下書き保存・提出ボタン

### 4. 申請詳細 (application_detail.html)
- 2カラムレイアウト
  - 左: 申請内容（基本情報、作業情報、添付ファイル、コメント）
  - 右: ワークフロー情報（日時、履歴）
- 役割に応じたアクションボタン表示
- 添付ファイルアップロード・削除
- コメント追加フォーム

### 5. 確認画面
- **confirm_submit.html**: 申請提出前の確認
- **confirm_receive.html**: 受付処理（受付/差し戻し）
- **confirm_approve.html**: 承認処理（承認/却下）
- 各画面で詳細へのリンク提供
- 確認ダイアログ（JavaScript）

### 6. 一覧画面
- **my_applications.html**: 自分の申請一覧
- **pending_receive.html**: 受付待ち一覧
- **pending_approve.html**: 承認待ち一覧
- テーブル形式で見やすく表示
- ステータスバッジで状態を視覚化

## 🎯 カスタマイズ方法

### 1. カラーリングの変更

base.htmlのstyle内で色を変更:

```css
.stat-card.draft {
    border-left-color: #6c757d; /* 下書き */
}
.stat-card.submitted {
    border-left-color: #0dcaf0; /* 申請中 */
}
```

### 2. ロゴの追加

base.htmlのnavbar-brand部分を変更:

```html
<a class="navbar-brand" href="{% url 'workflow:dashboard' %}">
    <img src="/static/img/logo.png" height="30"> ワークフローシステム
</a>
```

### 3. フッターのカスタマイズ

base.htmlのfooter部分を編集:

```html
<footer class="py-3 mt-4">
    <div class="container text-center">
        <p class="text-muted mb-0">
            <small>&copy; 2024 あなたの会社名. All rights reserved.</small>
        </p>
    </div>
</footer>
```

### 4. 追加のスタイル

各テンプレートで `{% block extra_css %}` を使用:

```html
{% block extra_css %}
<style>
    .custom-class {
        /* カスタムスタイル */
    }
</style>
{% endblock %}
```

### 5. 追加のJavaScript

各テンプレートで `{% block extra_js %}` を使用:

```html
{% block extra_js %}
<script>
    // カスタムJavaScript
</script>
{% endblock %}
```

## 📱 レスポンシブ対応

すべてのテンプレートはBootstrap 5のグリッドシステムを使用し、以下のブレークポイントに対応:

- **モバイル**: < 576px
- **タブレット**: 576px ~ 992px
- **デスクトップ**: > 992px

## 🔧 トラブルシューティング

### テンプレートが見つからない

```python
# settings.py でDIRSを確認
TEMPLATES = [
    {
        ...
        'DIRS': [BASE_DIR / 'templates'],
        ...
    },
]
```

### 静的ファイルが読み込まれない

CDNを使用しているため、インターネット接続を確認してください。
オフライン環境の場合は、Bootstrap/Iconsをダウンロードして配置:

```python
# settings.py
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
```

### CSSが反映されない

ブラウザのキャッシュをクリアするか、ハードリロード（Ctrl+F5）を試してください。

## 🎨 テーマのカスタマイズ例

### ダークモード対応

base.htmlに追加:

```html
<style>
    @media (prefers-color-scheme: dark) {
        body {
            background-color: #1a1a1a;
            color: #e0e0e0;
        }
        .card {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        .table {
            color: #e0e0e0;
        }
    }
</style>
```

### 企業カラーへの変更

```css
/* プライマリーカラーを変更 */
.navbar-dark.bg-primary {
    background-color: #your-color !important;
}
.btn-primary {
    background-color: #your-color;
    border-color: #your-color;
}
```

## 📚 参考リンク

- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [Bootstrap Icons](https://icons.getbootstrap.com/)
- [Django Template Language](https://docs.djangoproject.com/en/stable/topics/templates/)
