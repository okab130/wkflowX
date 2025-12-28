# GitHub アップロード手順

## ✅ ローカルGit設定完了

以下の作業が完了しました：
- Git リポジトリ初期化
- .gitignore ファイル作成
- 全ファイルをコミット（63ファイル、13,075行）

## 📤 GitHubへのアップロード手順

### 1. GitHubでリポジトリを作成

1. https://github.com にアクセス
2. 右上の「+」→「New repository」をクリック
3. 以下の情報を入力：
   - **Repository name**: `wkflowX`
   - **Description**: `業務ワークフローシステム - ロールベースの申請・受付・承認フローを実現するDjangoアプリケーション`
   - **Public/Private**: お好みで選択
   - **Initialize with README**: ✗ チェックを外す
4. 「Create repository」をクリック

### 2. ローカルからGitHubへプッシュ

リポジトリ作成後、表示される指示に従ってください。または以下のコマンドを実行：

```bash
cd C:\Users\user\gh\wkflowX

# GitHubのリポジトリURLを設定（your-usernameを実際のユーザー名に変更）
git remote add origin https://github.com/your-username/wkflowX.git

# ブランチ名をmainに変更（推奨）
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

### 3. 認証情報の入力

プッシュ時に認証が求められます：
- **Username**: GitHubのユーザー名
- **Password**: Personal Access Token（パスワードは使用不可）

#### Personal Access Tokenの作成方法

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 「Generate new token」→「Generate new token (classic)」
3. Note: 任意の名前（例：wkflowX-upload）
4. Expiration: 任意の期限
5. Scope: `repo` にチェック
6. 「Generate token」をクリック
7. 表示されたトークンをコピー（一度しか表示されません！）
8. パスワードの代わりにこのトークンを使用

### 4. 確認

プッシュ成功後、GitHubのリポジトリページで以下を確認：
- 全ファイルがアップロードされているか
- READMEが表示されているか
- コミット履歴が正しいか

## 📁 アップロードされるファイル

```
wkflowX/
├── .github/
│   └── copilot-instructions.md
├── .gitignore
├── README.md
├── requirements.txt
├── manage.py
├── config/              # Django設定
├── workflow/            # メインアプリ
├── templates/           # HTMLテンプレート
│   ├── registration/
│   └── workflow/
│       ├── user_manual.html
│       └── operation_manual.html
├── ドキュメント類（*.md）
└── その他設定ファイル

63ファイル、13,075行
```

## 🔒 セキュリティ注意事項

### 確認済み（問題なし）
- ✅ .gitignoreで重要ファイルを除外済み
- ✅ db.sqlite3 は除外
- ✅ 仮想環境（venv/）は除外
- ✅ メディアファイル（/media）は除外
- ✅ .env ファイルは除外

### 注意点
- settings.pyにパスワードが含まれている場合は、環境変数化を推奨
- SECRET_KEYは公開リポジトリの場合、必ず変更してください

## 🎯 次のステップ

1. GitHubリポジトリを作成
2. git remote add でリモートを追加
3. git push でアップロード
4. README.mdを確認
5. リポジトリURLを共有

---

**準備完了！上記の手順でGitHubにアップロードしてください。**
