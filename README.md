# Django 業務ワークフローシステム（製造業・建設業向け）

取引先企業の作業申請・受付・承認を管理するDjangoアプリケーション

## 📋 システム概要

### 対象業種
製造業・建設業における取引先企業の申請管理

### 申請種別（5種類）
1. **作業申請** - 一般的な作業の申請
2. **工事申請** - 工事に関する申請（図面添付必須）
3. **工具持込申請** - 工具の持込に関する申請
4. **制限エリア立入申請** - セキュリティエリアへの立入申請
5. **制限エリア工具持込申請** - 制限エリアへの工具持込申請

### ユーザー種別
- **取引先**: 申請の作成・提出
- **受付担当**: 申請内容の確認・受理・差し戻し
- **承認者**: 最終承認・却下
- **管理者**: システム全体の管理

## ✨ 主要機能

### 基本機能
- ✅ 申請CRUD（作成・閲覧・編集・削除）
- ✅ 3段階ワークフロー（申請→受付→承認）
- ✅ ステータス管理（下書き/申請中/受付済/承認済/却下/差し戻し）
- ✅ 差し戻し・再申請機能
- ✅ 添付ファイル管理（10MB制限、複数ファイル）
- ✅ コメント機能
- ✅ メール通知（全プロセス）
- ✅ 検索・フィルタリング
- ✅ 申請履歴の記録

### セキュリティ
- ✅ 役割ベースのアクセス制御
- ✅ 権限チェック（編集・承認・受付）
- ✅ CSRF保護
- ✅ ログイン必須

## 🚀 クイックスタート

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd wkflowX
```

### 2. 仮想環境の作成と有効化
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージのインストール
```bash
pip install django pillow
```

### 4. プロジェクトの作成
```bash
django-admin startproject config .
python manage.py startapp workflow
```

### 5. ファイルのコピー
以下のファイルを適切な場所にコピー:
- `models.py` → `workflow/models.py`
- `views.py` → `workflow/views.py`
- `urls.py` → `workflow/urls.py`
- `forms.py` → `workflow/forms.py`
- `admin.py` → `workflow/admin.py`

### 6. settings.pyの設定
`settings_example.py` を参照して設定

### 7. マイグレーション
```bash
python manage.py makemigrations workflow
python manage.py migrate
```

### 8. スーパーユーザーの作成
```bash
python manage.py createsuperuser
```

### 9. 開発サーバーの起動
```bash
python manage.py runserver
```

### 10. アクセス
- アプリケーション: http://localhost:8000/workflow/
- 管理画面: http://localhost:8000/admin/

## 📁 ファイル構成

```
wkflowX/
├── workflow_design.md          # システム設計書
├── implementation_guide.md     # 詳細な実装手順書
├── models.py                   # データモデル定義
├── views.py                    # ビュー実装
├── urls.py                     # URLルーティング
├── forms.py                    # フォーム定義
├── admin.py                    # 管理画面設定
├── settings_example.py         # settings.py設定例
└── README.md                   # このファイル
```

## 📊 ワークフロー

```
┌─────────┐
│ 下書き   │
└────┬────┘
     │ 提出
     ▼
┌─────────┐    差し戻し    ┌──────────┐
│ 申請中   │◄──────────────┤ 差し戻し  │
└────┬────┘                └──────────┘
     │ 受付                     ▲
     ▼                          │
┌─────────┐                     │
│ 受付済   │─────────────────────┘
└────┬────┘
     │ 承認/却下
     ▼
┌─────────┐
│承認済/却下│
└─────────┘
```

## 📧 メール通知タイミング

| タイミング | 通知先 | 内容 |
|----------|--------|------|
| 申請提出時 | 受付担当 | 新規申請の通知 |
| 受付完了時 | 承認者、申請者 | 承認依頼、受付完了通知 |
| 承認時 | 申請者 | 承認完了通知 |
| 却下時 | 申請者 | 却下理由通知 |
| 差し戻し時 | 申請者 | 修正依頼通知 |

## 🔧 開発環境の設定

### 必要な環境変数（本番環境）
```bash
# .env ファイルの例
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password

DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## 🧪 テスト

### 単体テストの実行
```bash
python manage.py test workflow
```

### テストカバレッジ
```bash
pip install coverage
coverage run --source='workflow' manage.py test workflow
coverage report
```

## 📝 使い方

### 取引先ユーザーの場合
1. ログイン後、「新規申請」をクリック
2. 申請種別を選択
3. 必要情報を入力（申請種別により必須項目が変わります）
4. 添付ファイルがあればアップロード
5. 「下書き保存」または「申請提出」

### 受付担当の場合
1. 「受付待ち」から未処理の申請を確認
2. 申請内容を確認
3. 問題なければ「受付」、問題があれば「差し戻し」

### 承認者の場合
1. 「承認待ち」から受付済の申請を確認
2. 申請内容を確認
3. 「承認」または「却下」を選択
4. コメントを記入して決定

## 🛠️ トラブルシューティング

### マイグレーションエラー
```bash
python manage.py migrate --fake workflow zero
python manage.py migrate workflow
```

### メディアファイルが表示されない
```bash
# settings.py で MEDIA_URL, MEDIA_ROOT を確認
# urls.py でメディアファイル配信設定を確認
```

### メールが送信されない
- 開発環境: コンソールに出力されます（`EMAIL_BACKEND = 'console'`）
- 本番環境: SMTP設定を確認

## 📚 ドキュメント

詳細なドキュメント:
- [システム設計書](workflow_design.md)
- [実装手順書](implementation_guide.md)

## 🔐 セキュリティ

- SECRET_KEYは環境変数で管理
- 本番環境では DEBUG=False
- CSRF保護有効
- パスワードは適切にハッシュ化
- ファイルアップロードは拡張子・サイズチェック

## 📄 ライセンス

MIT License

## 👥 サポート

質問や問題がある場合は、Issueを作成してください。

## 🎯 今後の拡張予定

- [ ] 多段階承認フロー
- [ ] Excel/PDFエクスポート
- [ ] カレンダー表示
- [ ] ダッシュボード統計
- [ ] モバイルアプリ対応
- [ ] 全文検索機能
- [ ] 通知設定のカスタマイズ
