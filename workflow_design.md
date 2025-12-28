# Django 業務ワークフローシステム 設計書

**最終更新日**: 2025-12-28  
**バージョン**: 2.0（ロールベースワークフロー対応版）

## 1. システム概要

製造業・建設業向けの作業申請・受付・承認フローを管理するDjangoアプリケーション。
ロールベースのアクセス制御により、柔軟な権限管理と申請種別ごとの細かい制御を実現。

### 1.1 主要機能
- ✅ ロールベースのワークフロー管理
- ✅ 申請種別ごとのロール設定（受付・承認）
- ✅ 複数ユーザーによるロール共有
- ✅ ファイル添付機能（複数ファイル対応）
- ✅ コメント機能（履歴管理）
- ✅ レスポンシブデザイン（Bootstrap 5）
- ✅ 利用者マニュアル・運用マニュアル完備

### 1.2 業務要件
- 取引先企業が各種作業・持込申請を作成・提出
- 受付ロールに所属するユーザーが申請内容を確認・受理
- 承認ロールに所属するユーザーが最終的に承認/却下を判断
- 申請種別ごとに異なる受付・承認ロールを設定可能
- 添付ファイルで図面・仕様書等のドキュメントを添付可能（複数可）
- コメント履歴で担当者間のコミュニケーションを記録

## 2. データモデル設計

### 2.1 UserProfile（ユーザープロファイル）
Django標準Userの拡張プロファイル

**フィールド:**
- user: Django User（1対1）
- role: ユーザー種別（vendor/receiver/approver/admin）
- company_name: 企業名
- department: 部署
- phone: 電話番号

**ユーザー種別:**
- `vendor`: 取引先（申請者）
- `receiver`: 受付担当（旧Profile.role利用可、新ロール推奨）
- `approver`: 承認者（旧Profile.role利用可、新ロール推奨）
- `admin`: 管理者

### 2.2 WorkflowRole（ワークフローロール）⭐ NEW
受付・承認の役割を管理。複数ロールの作成が可能。

**フィールド:**
- name: ロール名（例: "工事専門受付"、"一般承認"）
- role_type: ロール種別（receiver/approver）
- description: 説明
- is_active: 有効フラグ
- created_at: 作成日時
- updated_at: 更新日時

**使用例:**
```python
# 受付ロール
一般受付（受付）
工事専門受付（受付）
制限エリア受付（受付）

# 承認ロール  
一般承認（承認）
工事専門承認（承認）
制限エリア承認（承認）
```

### 2.3 RoleMember（ロールメンバー）⭐ NEW
ユーザーとワークフローロールの多対多関係を管理。

**フィールド:**
- role: WorkflowRole（外部キー）
- user: User（外部キー）
- assigned_at: 割当日時
- assigned_by: 割当者（誰が割り当てたか）

**制約:**
- unique_together: (role, user) - 同じロールに同じユーザーは1回のみ

**キャッシュ管理:**
- save/delete時に自動的にユーザーのキャッシュをクリア
- `user_receivable_types_{user_id}`
- `user_approvable_types_{user_id}`

### 2.4 ApplicationTypeConfig（申請種別設定）⭐ NEW
申請種別ごとに受付・承認ロールを設定。

**フィールド:**
- application_type: 申請種別（work/construction/tool/restricted_area/restricted_tool）
- receiver_role: 受付ロール（WorkflowRole）
- approver_role: 承認ロール（WorkflowRole）
- is_active: 有効フラグ
- created_at: 作成日時
- updated_at: 更新日時

**設定例:**
```python
工事申請 → 受付: 工事専門受付、承認: 工事専門承認
作業申請 → 受付: 一般受付、承認: 一般承認
制限エリア立入 → 受付: 制限エリア受付、承認: 制限エリア承認
```

### 2.5 Application（申請）
申請の基本情報を管理。

**フィールド:**
- application_number: 申請番号（自動採番、例: APP20251228-0001）
- application_type: 申請種別（work/construction/tool/restricted_area/restricted_tool）
- title: 申請タイトル
- description: 申請内容（詳細）
- applicant: 申請者（User）
- applicant_company: 申請者企業名
- work_date_from: 作業開始予定日
- work_date_to: 作業終了予定日
- work_location: 作業場所
- worker_count: 作業人数
- status: ステータス（draft/submitted/received/approved/rejected/returned）
- submitted_at: 提出日時
- received_at: 受付日時
- received_by: 受付者
- approved_at: 承認日時
- approved_by: 承認者
- created_at: 作成日時
- updated_at: 更新日時

**申請種別:**
- `work`: 作業申請
- `construction`: 工事申請
- `tool`: 工具持込申請
- `restricted_area`: 制限エリア立入申請
- `restricted_tool`: 制限エリア工具持込申請

**ステータス:**
- `draft`: 下書き
- `submitted`: 申請中（受付待ち）
- `received`: 受付済（承認待ち）
- `approved`: 承認済
- `rejected`: 却下
- `returned`: 差し戻し

### 2.6 Comment（コメント）
各段階でのやり取りを記録。

**フィールド:**
- application: 申請（Application）
- user: コメント者（User）
- comment: コメント内容
- created_at: 作成日時

### 2.7 Attachment（添付ファイル）
申請に関連するファイルを管理（複数添付可能）。

**フィールド:**
- application: 申請（Application）
- file: ファイル（アップロード先: media/attachments/）
- original_filename: 元のファイル名
- uploaded_at: アップロード日時
- uploaded_by: アップロード者（User）

**サポート形式:**
- PDF、Word、Excel、画像（PNG/JPG）、CAD図面など

## 3. URL設計

### 3.1 ワークフロー関連

```python
app_name = 'workflow'

urlpatterns = [
    # ダッシュボード
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # 申請CRUD
    path('create/', views.ApplicationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='edit'),
    
    # ワークフロー処理
    path('<int:pk>/submit/', views.submit_application, name='submit'),
    path('<int:pk>/receive/', views.receive_application, name='receive'),
    path('<int:pk>/approve/', views.approve_application, name='approve'),
    
    # コメント
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    # 添付ファイル
    path('<int:pk>/upload/', views.upload_attachment, name='upload_attachment'),
    path('<int:pk>/attachment/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    
    # マニュアル
    path('manual/user/', views.user_manual, name='user_manual'),
    path('manual/operation/', views.operation_manual, name='operation_manual'),
    
    # 一覧（フィルター済み）
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('pending-receive/', views.PendingReceiveView.as_view(), name='pending_receive'),
    path('pending-approve/', views.PendingApproveView.as_view(), name='pending_approve'),
]
```

### 3.2 認証関連

```python
# config/urls.py
path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
```

### 3.3 管理画面

```python
path('admin/', admin.site.urls),
```

## 4. ビュー設計

### 4.1 DashboardView（ダッシュボード）⭐ UPDATED
**クラス**: ListView  
**テンプレート**: dashboard.html

**表示条件（OR結合）:**
1. 自分が申請した伝票（全ステータス）
2. 自分が受付する伝票（申請中のみ）
3. 自分が承認する伝票（受付済のみ）

**コンテキスト:**
- 申請一覧（フィルター済み）
- 統計情報（ステータス別件数）
- 最近の申請（5件）

**キャッシュ:**
- ユーザーの受付可能申請種別: 1時間
- ユーザーの承認可能申請種別: 1時間

### 4.2 ApplicationCreateView（申請作成）
**クラス**: CreateView  
**テンプレート**: application_form.html  
**権限**: 取引先ユーザー（profile.role='vendor'）

**機能:**
- 申請フォーム入力
- 下書き保存（status='draft'）
- ファイル添付（複数可）

### 4.3 ApplicationDetailView（申請詳細）⭐ UPDATED
**クラス**: DetailView  
**テンプレート**: application_detail.html

**表示内容:**
- 申請基本情報
- ステータス表示（バッジ）
- ワークフロー進行状況
- 添付ファイル一覧（ダウンロード可）
- コメント履歴
- アクションボタン（権限・ステータスに応じて）

**アクションボタン:**
- 申請者: 編集、提出、再申請
- 受付担当: 受付、差し戻し
- 承認者: 承認、却下
- 全員: コメント追加

**権限チェック:**
- 申請者本人、受付可能ユーザー、承認可能ユーザーのみ閲覧可

### 4.4 ApplicationUpdateView（申請編集）
**クラス**: UpdateView  
**テンプレート**: application_form.html  
**権限**: 申請者本人のみ、かつstatus='draft'または'returned'

### 4.5 submit_application（申請提出）
**関数ビュー**  
**処理:**
1. status: draft → submitted
2. submitted_at: 現在日時
3. リダイレクト: 申請詳細

### 4.6 receive_application（受付処理）⭐ UPDATED
**関数ビュー**  
**権限**: 該当申請種別の受付ロールメンバー  
**処理:**
1. status: submitted → received
2. received_at: 現在日時
3. received_by: 現在ユーザー
4. コメント追加（任意）
5. リダイレクト: 申請詳細

**権限チェック:**
```python
# ユーザーの受付ロールを取得
user_roles = user.workflow_roles.filter(role__role_type='receiver')
# 申請種別の設定を取得
config = ApplicationTypeConfig.objects.get(application_type=app.application_type)
# 受付ロールに所属しているか確認
if config.receiver_role in [rm.role for rm in user_roles]:
    # 受付可能
```

### 4.7 approve_application（承認処理）⭐ UPDATED
**関数ビュー**  
**権限**: 該当申請種別の承認ロールメンバー  
**処理:**
1. status: received → approved（または rejected）
2. approved_at: 現在日時
3. approved_by: 現在ユーザー
4. コメント追加（必須）
5. リダイレクト: 申請詳細

**権限チェック:**
```python
# ユーザーの承認ロールを取得
user_roles = user.workflow_roles.filter(role__role_type='approver')
# 申請種別の設定を取得
config = ApplicationTypeConfig.objects.get(application_type=app.application_type)
# 承認ロールに所属しているか確認
if config.approver_role in [rm.role for rm in user_roles]:
    # 承認可能
```

### 4.8 add_comment（コメント追加）
**関数ビュー**  
**処理:**
1. Commentオブジェクト作成
2. リダイレクト: 申請詳細

### 4.9 upload_attachment（ファイルアップロード）
**関数ビュー**  
**処理:**
1. Attachmentオブジェクト作成
2. ファイル保存（media/attachments/）
3. リダイレクト: 申請詳細

### 4.10 delete_attachment（ファイル削除）
**関数ビュー**  
**権限**: 申請者本人のみ  
**処理:**
1. Attachmentオブジェクト削除
2. 物理ファイル削除
3. リダイレクト: 申請詳細

### 4.11 MyApplicationsView（自分の申請一覧）
**クラス**: ListView  
**フィルター**: applicant=current_user

### 4.12 PendingReceiveView（受付待ち一覧）
**クラス**: ListView  
**フィルター**: status='submitted' AND 自分が受付可能な申請種別

### 4.13 PendingApproveView（承認待ち一覧）
**クラス**: ListView  
**フィルター**: status='received' AND 自分が承認可能な申請種別

### 4.14 user_manual（利用者マニュアル）⭐ NEW
**関数ビュー**  
**テンプレート**: user_manual.html  
**権限**: ログイン済みユーザー全員

### 4.15 operation_manual（運用マニュアル）⭐ NEW
**関数ビュー**  
**テンプレート**: operation_manual.html  
**権限**: 管理者またはis_staff=True

## 5. 画面一覧

### 5.1 認証画面
1. **ログイン画面** (login.html)
   - ユーザー名・パスワード入力
   - ログインボタン

### 5.2 ワークフロー画面
2. **ダッシュボード** (dashboard.html) ⭐ UPDATED
   - 申請一覧（自分が関係する伝票のみ）
   - ステータス別統計カード
   - 検索・フィルター機能
   - ステータスバッジ表示

3. **申請作成フォーム** (application_form.html)
   - 申請種別選択
   - 基本情報入力
   - 作業情報入力
   - ファイル添付（複数可）
   - 下書き保存ボタン

4. **申請詳細画面** (application_detail.html) ⭐ UPDATED
   - 申請情報表示
   - ステータス表示（色分けバッジ）
   - ワークフロー進行状況
   - 添付ファイル一覧（ダウンロードリンク）
   - コメント履歴
   - アクションボタン（権限・ステータスに応じて表示）
     - 提出ボタン（申請者・下書き時）
     - 受付ボタン（受付担当・申請中時）
     - 承認ボタン（承認者・受付済時）
     - 却下ボタン（承認者・受付済時）
     - コメント追加ボタン（全員）

5. **申請編集画面** (application_form.html)
   - 申請作成と同じフォーム
   - 既存データ表示
   - 更新ボタン

6. **受付待ち一覧** (pending_receive.html)
   - 申請中（submitted）の伝票
   - 自分が受付可能な申請種別のみ
   - 一括選択機能

7. **承認待ち一覧** (pending_approve.html)
   - 受付済（received）の伝票
   - 自分が承認可能な申請種別のみ
   - 一括選択機能

8. **自分の申請一覧** (my_applications.html)
   - 自分が申請した伝票（全ステータス）
   - ステータスフィルター
   - 申請種別フィルター

### 5.3 確認ダイアログ
9. **提出確認** (confirm_submit.html)
   - 提出前の最終確認
   - 申請内容サマリー表示

10. **受付確認** (confirm_receive.html)
    - 受付前の確認
    - コメント入力欄

11. **承認確認** (confirm_approve.html)
    - 承認/却下の最終確認
    - コメント入力欄（必須）

### 5.4 マニュアル⭐ NEW
12. **利用者マニュアル** (user_manual.html)
    - システム概要
    - ユーザーの役割説明
    - 操作方法（役割別）
    - 検索・フィルター機能
    - トラブルシューティング
    - FAQ

13. **運用マニュアル** (operation_manual.html)
    - システム構成
    - インストール・セットアップ
    - ユーザー管理
    - ロール管理
    - バックアップ・監視
    - セキュリティ設定

## 6. 権限設計

### 6.1 ユーザー種別と権限

#### vendor（取引先）
- ✅ 自社の申請の作成
- ✅ 自社の申請の編集（下書き・差し戻し時のみ）
- ✅ 自社の申請の閲覧（全ステータス）
- ✅ 自社の申請の提出（下書き時のみ）
- ✅ ファイル添付・削除（自社の申請のみ）
- ✅ コメント追加
- ✅ 利用者マニュアル閲覧

#### receiver（受付担当）⭐ UPDATED
- ✅ 所属ロールが設定された申請種別の閲覧
- ✅ 申請中（submitted）の伝票の受付処理
- ✅ 受付可能な申請種別のみ処理可能
- ✅ コメント追加
- ✅ 利用者マニュアル閲覧

**ロールベース権限チェック:**
```python
# ユーザーの受付ロールを取得
user_receiver_roles = user.workflow_roles.filter(role__role_type='receiver')
# 申請種別の受付ロールと比較
config = ApplicationTypeConfig.objects.get(application_type='construction')
if config.receiver_role in [rm.role for rm in user_receiver_roles]:
    # 受付処理可能
```

#### approver（承認者）⭐ UPDATED
- ✅ 所属ロールが設定された申請種別の閲覧
- ✅ 受付済（received）の伝票の承認/却下処理
- ✅ 承認可能な申請種別のみ処理可能
- ✅ コメント追加
- ✅ 利用者マニュアル閲覧

**ロールベース権限チェック:**
```python
# ユーザーの承認ロールを取得
user_approver_roles = user.workflow_roles.filter(role__role_type='approver')
# 申請種別の承認ロールと比較
config = ApplicationTypeConfig.objects.get(application_type='construction')
if config.approver_role in [rm.role for rm in user_approver_roles]:
    # 承認処理可能
```

#### admin（管理者）
- ✅ 全機能アクセス
- ✅ ユーザー管理（Django Admin）
- ✅ ワークフローロール管理
- ✅ ロールメンバー管理
- ✅ 申請種別設定管理
- ✅ 利用者マニュアル・運用マニュアル閲覧

### 6.2 権限チェック実装

#### テンプレート内（例）
```django
{% if user.profile.role == 'vendor' and application.status == 'draft' %}
    <a href="{% url 'workflow:submit' application.pk %}" class="btn btn-primary">
        提出する
    </a>
{% endif %}

{% if can_receive %}
    <a href="{% url 'workflow:receive' application.pk %}" class="btn btn-success">
        受付する
    </a>
{% endif %}

{% if can_approve %}
    <a href="{% url 'workflow:approve' application.pk %}" class="btn btn-primary">
        承認する
    </a>
{% endif %}
```

#### ビュー内（例）
```python
def receive_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    
    # 権限チェック: 受付ロールメンバーのみ
    user_roles = request.user.workflow_roles.filter(role__role_type='receiver')
    config = ApplicationTypeConfig.objects.get(application_type=application.application_type)
    
    if config.receiver_role not in [rm.role for rm in user_roles]:
        return HttpResponseForbidden("この申請を受付する権限がありません")
    
    # 受付処理...
```

### 6.3 ダッシュボード表示条件⭐ UPDATED

すべてのユーザーに対して以下の3条件でOR結合：

1. **自分が申請した伝票**（全ステータス）
   ```python
   Application.objects.filter(applicant=user)
   ```

2. **自分が受付する伝票**（申請中のみ）
   ```python
   Application.objects.filter(
       status='submitted',
       application_type__in=user_receivable_types
   )
   ```

3. **自分が承認する伝票**（受付済のみ）
   ```python
   Application.objects.filter(
       status='received',
       application_type__in=user_approvable_types
   )
   ```

**最終クエリ:**
```python
queryset = my_applications | receivable_applications | approvable_applications
queryset = queryset.distinct().order_by('-created_at')
```

## 7. ステータス遷移

### 7.1 基本フロー

```
下書き (draft)
    ↓ 【提出】申請者
申請中 (submitted)
    ↓ 【受付】受付ロールメンバー
受付済 (received)
    ↓ 【承認】承認ロールメンバー
承認済 (approved) ✅
```

### 7.2 差し戻しフロー

```
申請中 (submitted)
    ↓ 【差し戻し】受付ロールメンバー
差し戻し (returned)
    ↓ 【修正・再提出】申請者
申請中 (submitted)
```

### 7.3 却下フロー

```
受付済 (received)
    ↓ 【却下】承認ロールメンバー
却下 (rejected) ❌
```

### 7.4 ステータス詳細

| ステータス | 値 | 説明 | 操作可能者 | 次の操作 |
|----------|---|------|----------|---------|
| 下書き | draft | 作成中、未提出 | 申請者 | 提出 |
| 申請中 | submitted | 提出済、受付待ち | 受付担当 | 受付、差し戻し |
| 受付済 | received | 受付完了、承認待ち | 承認者 | 承認、却下 |
| 承認済 | approved | ワークフロー完了 | - | - |
| 却下 | rejected | 承認者が却下 | - | - |
| 差し戻し | returned | 修正が必要 | 申請者 | 再提出 |

### 7.5 ステータス色分け

- 🔵 **下書き（draft）**: グレー `secondary`
- 🔵 **申請中（submitted）**: シアン `info`
- 🟡 **受付済（received）**: イエロー `warning`
- 🟢 **承認済（approved）**: グリーン `success`
- 🔴 **却下（rejected）**: レッド `danger`
- 🟠 **差し戻し（returned）**: オレンジ `warning`

## 9. ロールベースワークフローの設定例⭐ NEW

### 9.1 ワークフローロールの作成

#### 受付ロール
```python
# 一般受付ロール
WorkflowRole.objects.create(
    name='一般受付',
    role_type='receiver',
    description='作業申請・工具持込申請の受付を担当'
)

# 工事専門受付ロール
WorkflowRole.objects.create(
    name='工事専門受付',
    role_type='receiver',
    description='工事申請の受付を担当（専門知識が必要）'
)

# 制限エリア受付ロール
WorkflowRole.objects.create(
    name='制限エリア受付',
    role_type='receiver',
    description='制限エリア関連申請の受付を担当'
)
```

#### 承認ロール
```python
# 一般承認ロール
WorkflowRole.objects.create(
    name='一般承認',
    role_type='approver',
    description='作業申請・工具持込申請の承認を担当'
)

# 工事専門承認ロール
WorkflowRole.objects.create(
    name='工事専門承認',
    role_type='approver',
    description='工事申請の承認を担当（管理職）'
)

# 制限エリア承認ロール
WorkflowRole.objects.create(
    name='制限エリア承認',
    role_type='approver',
    description='制限エリア関連申請の承認を担当（セキュリティ管理者）'
)
```

### 9.2 ロールメンバーの割り当て

```python
# 田中太郎を一般受付ロールに追加
general_receiver_role = WorkflowRole.objects.get(name='一般受付')
user_tanaka = User.objects.get(username='tanaka')
RoleMember.objects.create(
    role=general_receiver_role,
    user=user_tanaka,
    assigned_by=admin_user
)

# 佐藤花子を工事専門受付と工事専門承認の両方に追加
construction_receiver = WorkflowRole.objects.get(name='工事専門受付')
construction_approver = WorkflowRole.objects.get(name='工事専門承認')
user_sato = User.objects.get(username='sato')
RoleMember.objects.create(role=construction_receiver, user=user_sato, assigned_by=admin_user)
RoleMember.objects.create(role=construction_approver, user=user_sato, assigned_by=admin_user)
```

### 9.3 申請種別設定

```python
# 作業申請: 一般受付 → 一般承認
ApplicationTypeConfig.objects.create(
    application_type='work',
    receiver_role=WorkflowRole.objects.get(name='一般受付'),
    approver_role=WorkflowRole.objects.get(name='一般承認')
)

# 工事申請: 工事専門受付 → 工事専門承認
ApplicationTypeConfig.objects.create(
    application_type='construction',
    receiver_role=WorkflowRole.objects.get(name='工事専門受付'),
    approver_role=WorkflowRole.objects.get(name='工事専門承認')
)

# 制限エリア立入申請: 制限エリア受付 → 制限エリア承認
ApplicationTypeConfig.objects.create(
    application_type='restricted_area',
    receiver_role=WorkflowRole.objects.get(name='制限エリア受付'),
    approver_role=WorkflowRole.objects.get(name='制限エリア承認')
)
```

### 9.4 運用例

#### シナリオ1: 工事申請のワークフロー
1. **取引先A社の山田さん**が工事申請を提出
2. システムが`ApplicationTypeConfig`で工事申請の設定を確認
   - 受付ロール: 工事専門受付
   - 承認ロール: 工事専門承認
3. **工事専門受付ロールのメンバー**（佐藤さん、鈴木さん）のダッシュボードに表示
4. **佐藤さん**が受付処理を実行
5. **工事専門承認ロールのメンバー**（佐藤さん、田中さん）のダッシュボードに表示
6. **田中さん**が承認処理を実行
7. ワークフロー完了

#### シナリオ2: 複数ロール所属ユーザー
佐藤さんは以下のロールに所属：
- 工事専門受付（receiver）
- 工事専門承認（approver）

佐藤さんのダッシュボードには以下が表示：
- 自分が申請した伝票（全ステータス）
- 工事申請（申請中） ← 受付可能
- 工事申請（受付済） ← 承認可能

### 9.5 管理画面での設定

Django Adminで以下を管理：
1. **ワークフローロール**: 新規ロール作成・編集
2. **ロールメンバー**: ユーザーのロール割り当て
3. **申請種別設定**: 申請種別ごとのロール設定

**設定手順:**
```
1. Django Admin ログイン
2. 「ワークフローロール」→ 受付・承認ロールを作成
3. 「ロールメンバー」→ ユーザーをロールに割り当て
4. 「申請種別設定」→ 各申請種別のロールを設定
```

## 8. 申請種別ごとの必須項目

### 8.1 作業申請（work）
**概要**: 通常の作業を行う際の申請

**必須項目:**
- 申請タイトル
- 作業内容（description）
- 作業予定日（work_date_from）
- 作業場所（work_location）
- 作業人数（worker_count）

**推奨添付ファイル:**
- 作業計画書
- 安全管理計画

### 8.2 工事申請（construction）
**概要**: 建設工事・大規模改修等の申請

**必須項目:**
- 申請タイトル
- 工事内容（description）
- 工事期間（work_date_from ～ work_date_to）
- 工事場所（work_location）
- 工事人数（worker_count）
- 添付ファイル（**図面必須**）

**推奨添付ファイル:**
- 工事図面（必須）
- 施工計画書
- 安全管理計画
- 施工業者情報

### 8.3 工具持込申請（tool）
**概要**: 工具・機材を持ち込む際の申請

**必須項目:**
- 申請タイトル
- 持込工具リスト（description）
- 使用目的（description内に記載）
- 使用期間（work_date_from ～ work_date_to）
- 返却予定日（work_date_to）

**推奨添付ファイル:**
- 工具リスト（Excel等）
- 工具写真
- 安全データシート（必要に応じて）

### 8.4 制限エリア立入申請（restricted_area）
**概要**: 制限エリアへの立ち入りを申請

**必須項目:**
- 申請タイトル
- 立入エリア（work_location）
- 立入目的（description）
- 立入予定日時（work_date_from）
- 立入者リスト（description内に記載）
- 人数（worker_count）

**推奨添付ファイル:**
- 立入者名簿
- 入場証明書
- 安全教育受講証明

### 8.5 制限エリア工具持込申請（restricted_tool）
**概要**: 制限エリアへ工具を持ち込む際の申請

**必須項目:**
- 申請タイトル
- 立入エリア（work_location）
- 持込工具リスト（description）
- 使用目的（description内に記載）
- 使用期間（work_date_from ～ work_date_to）
- 立入者リスト（description内に記載）
- 人数（worker_count）

**推奨添付ファイル:**
- 工具リスト
- 立入者名簿
- 安全データシート
- 入場証明書

## 10. 技術スタック

### 10.1 バックエンド
- **Python**: 3.8+
- **Django**: 4.2.7
- **PostgreSQL**: 13+ (スキーマ: wkflowx)
- **psycopg2-binary**: 2.9.9

### 10.2 フロントエンド
- **Bootstrap**: 5.3.0
- **Bootstrap Icons**: 1.11.0
- **JavaScript**: バニラJS（jQuery不使用）

### 10.3 開発ツール
- **Git**: バージョン管理
- **pip**: パッケージ管理
- **venv**: 仮想環境

### 10.4 デプロイ環境
- **Webサーバー**: Gunicorn（推奨）
- **リバースプロキシ**: Nginx（推奨）
- **データベース**: PostgreSQL
- **OS**: Windows/Linux対応

### 10.5 ディレクトリ構成

```
wkflowX/
├── config/                    # プロジェクト設定
│   ├── __init__.py
│   ├── settings.py           # Django設定
│   ├── urls.py               # ルートURLルーティング
│   ├── wsgi.py               # WSGI設定
│   └── asgi.py               # ASGI設定
│
├── workflow/                  # メインアプリケーション
│   ├── __init__.py
│   ├── models.py             # データモデル定義
│   ├── views.py              # ビュー処理
│   ├── forms.py              # フォーム定義
│   ├── admin.py              # Django Admin設定
│   ├── urls.py               # アプリURLルーティング
│   ├── apps.py               # アプリ設定
│   ├── migrations/           # DBマイグレーション
│   │   ├── 0001_initial.py
│   │   └── 0002_add_workflow_roles.py
│   └── management/           # カスタムコマンド
│       └── commands/
│           └── migrate_to_workflow_roles.py
│
├── templates/                 # HTMLテンプレート
│   ├── registration/
│   │   └── login.html
│   └── workflow/
│       ├── base.html
│       ├── dashboard.html
│       ├── application_form.html
│       ├── application_detail.html
│       ├── user_manual.html
│       └── operation_manual.html
│
├── media/                     # アップロードファイル
│   └── attachments/          # 申請添付ファイル
│
├── staticfiles/              # 静的ファイル（collect後）
│
├── venv/                     # 仮想環境（Git除外）
│
├── .gitignore                # Git除外設定
├── requirements.txt          # Python依存パッケージ
├── manage.py                 # Django管理コマンド
├── README.md                 # プロジェクト概要
├── workflow_design.md        # この設計書
└── GITHUB_UPLOAD.md          # GitHubアップロード手順
```

## 11. 実装状況

### 11.1 Phase 1: 基本機能（✅ 完了）
- ✅ ユーザー認証・権限管理
- ✅ 5種類の申請モデル定義
- ✅ 申請CRUD（作成・閲覧・編集・削除）
- ✅ 基本的なワークフロー（申請→受付→承認）
- ✅ 添付ファイル機能（複数ファイル対応）
- ✅ ロールベースアクセス制御

### 11.2 Phase 2: 業務機能（✅ 完了）
- ✅ コメント機能（履歴管理）
- ✅ 差し戻し・再申請フロー
- ✅ 検索・フィルタリング
- ✅ ステータス別一覧表示
- ✅ ダッシュボード（統計情報）
- ✅ ワークフローロール管理
- ✅ 申請種別設定機能

### 11.3 Phase 3: ドキュメント（✅ 完了）
- ✅ 利用者マニュアル（30,000字）
- ✅ 運用マニュアル（30,000字）
- ✅ README.md
- ✅ 実装ガイド
- ✅ 設計書（このファイル）

### 11.4 Phase 4: 今後の拡張（未実装）
- ⬜ メール通知機能
- ⬜ エクスポート機能（Excel/PDF）
- ⬜ 申請テンプレート機能
- ⬜ カレンダー表示（作業予定）
- ⬜ レポート・分析機能
- ⬜ 多言語対応（i18n）
- ⬜ REST API（Django REST Framework）

## 12. セキュリティ

### 12.1 認証・認可
- ✅ Django標準認証機能
- ✅ ログインRequired装飾子
- ✅ ロールベース権限チェック
- ✅ CSRF保護（Django標準）
- ✅ XSS対策（テンプレート自動エスケープ）

### 12.2 データ保護
- ✅ SQLインジェクション対策（ORMクエリセット使用）
- ✅ パスワードハッシュ化（Django標準）
- ✅ セッション管理（Django標準）
- ⚠️ HTTPS化（本番環境で必須）
- ⚠️ SECRET_KEY管理（環境変数化推奨）

### 12.3 ファイルアップロード
- ✅ ファイルサイズ制限
- ✅ ファイルタイプ検証
- ✅ アップロード先の分離（media/attachments/）
- ⚠️ ウイルススキャン（本番環境で推奨）

### 12.4 PostgreSQL設定
- ✅ スキーマ分離（wkflowx）
- ✅ 接続情報の外部化可能
- ⚠️ SSL接続（本番環境で推奨）
- ⚠️ バックアップ自動化（運用で必須）

## 13. パフォーマンス最適化

### 13.1 データベース
- ✅ select_related / prefetch_related（N+1問題対策）
- ✅ インデックス設定（主要カラム）
- ✅ キャッシュ（ロール判定結果、1時間）
- ⬜ データベース接続プーリング（本番環境推奨）

### 13.2 クエリ最適化
`python
# 良い例: N+1問題を回避
applications = Application.objects.select_related(
    'applicant', 'received_by', 'approved_by'
).prefetch_related(
    'comments__user', 'attachments'
)

# 悪い例: N+1問題が発生
applications = Application.objects.all()
for app in applications:
    print(app.applicant.username)  # ← 毎回DBアクセス
`

### 13.3 キャッシュ戦略
`python
# ユーザーの受付可能申請種別をキャッシュ（1時間）
cache_key = f'user_receivable_types_{user.id}'
types = cache.get(cache_key)
if types is None:
    # DB問い合わせ
    types = _calculate_receivable_types(user)
    cache.set(cache_key, types, 3600)
`

## 14. テスト戦略

### 14.1 単体テスト（推奨）
`python
# models.py のテスト
def test_application_status_transition(self):
    app = Application.objects.create(...)
    app.status = 'submitted'
    app.save()
    self.assertEqual(app.status, 'submitted')

# views.py のテスト
def test_dashboard_shows_my_applications(self):
    self.client.login(username='testuser', password='pass')
    response = self.client.get(reverse('workflow:dashboard'))
    self.assertEqual(response.status_code, 200)
`

### 14.2 統合テスト（推奨）
`python
def test_complete_workflow(self):
    # 申請作成
    # 提出
    # 受付
    # 承認
    # 結果確認
`

### 14.3 カバレッジ目標
- モデル: 80%以上
- ビュー: 70%以上
- フォーム: 80%以上

## 15. デプロイ手順

### 15.1 本番環境セットアップ
`ash
# 1. リポジトリクローン
git clone https://github.com/your-username/wkflowX.git
cd wkflowX

# 2. 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# 3. 依存パッケージインストール
pip install -r requirements.txt

# 4. 環境変数設定（.envファイル）
SECRET_KEY=your-secret-key
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=your-domain.com,127.0.0.1

# 5. PostgreSQLスキーマ作成
python create_schema.py

# 6. マイグレーション実行
python manage.py migrate

# 7. 静的ファイル収集
python manage.py collectstatic

# 8. スーパーユーザー作成
python manage.py createsuperuser

# 9. テストサーバー起動
python manage.py runserver
`

### 15.2 Gunicorn + Nginx（推奨）
`ash
# Gunicorn起動
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

# Nginx設定
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/wkflowX/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/wkflowX/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
`

## 16. 運用・保守

### 16.1 バックアップ
- **日次**: データベース全体のダンプ
- **週次**: mediaフォルダの完全バックアップ
- **月次**: システム全体のスナップショット

### 16.2 監視項目
- サーバーリソース（CPU、メモリ、ディスク）
- データベース接続数
- レスポンスタイム
- エラーログ

### 16.3 メンテナンス
- **定期実行**: ログローテーション
- **月次**: データベース統計更新
- **四半期**: セキュリティパッチ適用
- **年次**: Django/Pythonバージョンアップグレード

## 17. トラブルシューティング

### 17.1 よくある問題

#### データベース接続エラー
`python
# settings.pyを確認
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'options': '-c search_path=wkflowx'  # スキーマ指定
        }
    }
}
`

#### ALLOWED_HOSTSエラー
`python
# settings.py
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'your-domain.com']
`

#### メディアファイルが表示されない
`python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# urls.py（開発環境のみ）
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
`

#### ロールが正しく機能しない
`ash
# キャッシュクリア
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
`

## 18. 更新履歴

| 日付 | バージョン | 内容 |
|------|----------|------|
| 2025-12-28 | 2.0 | ロールベースワークフロー実装、マニュアル追加 |
| 2025-12-27 | 1.5 | ダッシュボード表示条件変更 |
| 2025-12-26 | 1.0 | 初版作成 |

## 19. 参考資料

### 19.1 内部ドキュメント
- README.md - プロジェクト概要
- SETUP_COMPLETE.md - セットアップ完了報告
- WORKFLOW_IMPLEMENTATION_COMPLETE.md - ワークフロー実装完了報告
- DASHBOARD_IMPLEMENTATION_COMPLETE.md - ダッシュボード実装完了報告
- GITHUB_UPLOAD.md - GitHubアップロード手順
- implementation_guide.md - 実装ガイド

### 19.2 外部リンク
- Django公式ドキュメント: https://docs.djangoproject.com/
- Bootstrap公式ドキュメント: https://getbootstrap.com/docs/
- PostgreSQL公式ドキュメント: https://www.postgresql.org/docs/

### 19.3 システム内マニュアル
- 利用者マニュアル: /workflow/manual/user/
- 運用マニュアル: /workflow/manual/operation/

---

**最終更新**: 2025-12-28  
**作成者**: wkflowX開発チーム  
**バージョン**: 2.0（ロールベースワークフロー対応版）
