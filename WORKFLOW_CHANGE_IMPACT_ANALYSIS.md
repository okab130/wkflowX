# ワークフロー変更影響調査報告書

## 変更要件サマリー

### 現在の仕様
- ユーザーに固定のロール（vendor/receiver/approver/admin）を1つ付与
- 全ての受付担当者が全ての申請を処理可能
- 全ての承認者が全ての受付済申請を処理可能

### 変更後の仕様
1. ロールを独立したエンティティとして管理（複数の受付ロール、複数の承認ロール）
2. 申請種別ごとに受付ロールと承認ロールを設定
3. 1つのロールに複数のユーザーを所属可能
4. 申請種別に設定されたロールのユーザーのみが該当申請を処理可能

---

## 影響範囲分析

### 1. データモデル（models.py）- **影響大**

#### 1.1 新規モデルの追加が必要

```python
class WorkflowRole(models.Model):
    """ワークフローロール"""
    name = models.CharField('ロール名', max_length=100, unique=True)
    role_type = models.CharField('ロール種別', max_length=20, 
                                 choices=[('receiver', '受付'), ('approver', '承認')])
    description = models.TextField('説明', blank=True)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

class RoleMember(models.Model):
    """ロールメンバー（ロールとユーザーの多対多関係）"""
    role = models.ForeignKey(WorkflowRole, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflow_roles')
    assigned_at = models.DateTimeField('割当日時', auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                    related_name='role_assignments_made')
    
    class Meta:
        unique_together = ['role', 'user']

class ApplicationTypeConfig(models.Model):
    """申請種別設定"""
    application_type = models.CharField('申請種別', max_length=30, unique=True)
    receiver_role = models.ForeignKey(WorkflowRole, on_delete=models.PROTECT, 
                                      related_name='receiver_for_types', 
                                      limit_choices_to={'role_type': 'receiver'})
    approver_role = models.ForeignKey(WorkflowRole, on_delete=models.PROTECT, 
                                       related_name='approver_for_types',
                                       limit_choices_to={'role_type': 'approver'})
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
```

#### 1.2 既存モデルの変更

**UserProfile**
- `role`フィールドは互換性のため残すが、基本ロールとして機能
- 新しいワークフローロールと併用

**Application**
- 以下のメソッドの変更が必要：
  - `send_notification_to_receivers()` - 申請種別に応じたロールメンバーへ通知
  - `send_notification_to_approvers()` - 申請種別に応じたロールメンバーへ通知
  - `can_receive()` - 該当ロールのメンバーかチェック
  - `can_approve()` - 該当ロールのメンバーかチェック

**影響度**: ★★★★★（重大）
- マイグレーションファイル作成必須
- 既存データの移行スクリプトが必要

---

### 2. ビュー（views.py）- **影響大**

#### 2.1 変更が必要なビュー

**DashboardView**
```python
def get_queryset(self):
    # 現在: user.profile.role == 'receiver'で判定
    # 変更後: ユーザーの所属ロールと申請種別の設定ロールを照合
    
    # 受付担当の場合
    user_receiver_roles = user.workflow_roles.filter(role__role_type='receiver')
    type_configs = ApplicationTypeConfig.objects.filter(receiver_role__in=user_receiver_roles)
    allowed_types = [config.application_type for config in type_configs]
    queryset = queryset.filter(status='submitted', application_type__in=allowed_types)
```

**receive_application**
```python
def receive_application(request, pk):
    # 権限チェックの変更
    # 現在: can_receive(user) - ロールで判定
    # 変更後: ユーザーが申請種別の受付ロールに所属しているか判定
    application = get_object_or_404(Application, pk=pk)
    type_config = ApplicationTypeConfig.objects.get(application_type=application.application_type)
    if not type_config.receiver_role.members.filter(user=request.user).exists():
        messages.error(request, '受付する権限がありません。')
        return redirect('workflow:detail', pk=pk)
```

**approve_application**
- 同様に承認ロールのチェックロジックを変更

**PendingReceiveView / PendingApproveView**
- クエリセットのフィルタリングロジックを変更
- ユーザーが処理可能な申請種別のみ表示

**影響度**: ★★★★☆（大）
- 10箇所以上のコード変更が必要

---

### 3. フォーム（forms.py）- **影響小**

#### 変更不要
- ApplicationFormは影響なし
- 新規にロール管理用のフォームが必要

#### 新規追加が必要
```python
class WorkflowRoleForm(forms.ModelForm):
    """ワークフローロールフォーム"""
    class Meta:
        model = WorkflowRole
        fields = ['name', 'role_type', 'description', 'is_active']

class RoleMemberForm(forms.Form):
    """ロールメンバー追加フォーム"""
    role = forms.ModelChoiceField(queryset=WorkflowRole.objects.filter(is_active=True))
    users = forms.ModelMultipleChoiceField(queryset=User.objects.filter(is_active=True))

class ApplicationTypeConfigForm(forms.ModelForm):
    """申請種別設定フォーム"""
    class Meta:
        model = ApplicationTypeConfig
        fields = ['application_type', 'receiver_role', 'approver_role']
```

**影響度**: ★★☆☆☆（小）

---

### 4. テンプレート - **影響中**

#### 変更が必要なテンプレート

**dashboard.html**
- 統計情報の表示ロジック変更
- フィルタリング条件の変更

**application_detail.html**
- 権限チェックの表示ロジック変更
- アクションボタンの表示条件変更

**新規追加が必要**
- `workflow/role_list.html` - ロール一覧
- `workflow/role_form.html` - ロール作成・編集
- `workflow/role_member_manage.html` - ロールメンバー管理
- `workflow/application_type_config.html` - 申請種別設定

**影響度**: ★★★☆☆（中）

---

### 5. URL設定（urls.py）- **影響中**

#### 新規追加が必要なURL

```python
# ロール管理
path('roles/', RoleListView.as_view(), name='role_list'),
path('roles/create/', RoleCreateView.as_view(), name='role_create'),
path('roles/<int:pk>/edit/', RoleUpdateView.as_view(), name='role_edit'),
path('roles/<int:pk>/members/', RoleMemberManageView.as_view(), name='role_members'),

# 申請種別設定
path('config/application-types/', ApplicationTypeConfigListView.as_view(), name='config_list'),
path('config/application-types/<str:type>/edit/', ApplicationTypeConfigUpdateView.as_view(), name='config_edit'),
```

**影響度**: ★★☆☆☆（小）

---

### 6. 管理画面（admin.py）- **影響中**

#### 新規追加が必要

```python
@admin.register(WorkflowRole)
class WorkflowRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'role_type', 'is_active', 'member_count', 'created_at']
    list_filter = ['role_type', 'is_active']
    search_fields = ['name', 'description']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'メンバー数'

@admin.register(RoleMember)
class RoleMemberAdmin(admin.ModelAdmin):
    list_display = ['role', 'user', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__username', 'user__email']

@admin.register(ApplicationTypeConfig)
class ApplicationTypeConfigAdmin(admin.ModelAdmin):
    list_display = ['application_type', 'receiver_role', 'approver_role', 'updated_at']
    list_filter = ['receiver_role', 'approver_role']
```

**影響度**: ★★★☆☆（中）

---

### 7. メール通知機能 - **影響大**

#### 変更が必要な箇所

**Application.send_notification_to_receivers()**
```python
def send_notification_to_receivers(self):
    """申請種別に設定された受付ロールのメンバーへ通知"""
    try:
        type_config = ApplicationTypeConfig.objects.get(application_type=self.application_type)
        receivers = type_config.receiver_role.members.filter(user__is_active=True).select_related('user')
        recipient_list = [member.user.email for member in receivers if member.user.email]
        # ... メール送信処理
    except ApplicationTypeConfig.DoesNotExist:
        # フォールバック: 全ての受付担当へ通知
        receivers = User.objects.filter(profile__role='receiver', is_active=True)
        recipient_list = [user.email for user in receivers if user.email]
```

**Application.send_notification_to_approvers()**
- 同様に承認ロールのメンバーへの通知に変更

**影響度**: ★★★★☆（大）

---

### 8. 権限チェック機能 - **影響大**

#### Applicationモデルのメソッド変更

```python
def can_receive(self, user):
    """受付可能か判定"""
    if not hasattr(user, 'profile'):
        return False
    if user.profile.role == 'admin':
        return True
    if self.status != 'submitted':
        return False
    
    # 申請種別の受付ロールに所属しているかチェック
    try:
        type_config = ApplicationTypeConfig.objects.get(application_type=self.application_type)
        return type_config.receiver_role.members.filter(user=user).exists()
    except ApplicationTypeConfig.DoesNotExist:
        # 設定がない場合はフォールバック
        return user.profile.role == 'receiver'

def can_approve(self, user):
    """承認可能か判定"""
    if not hasattr(user, 'profile'):
        return False
    if user.profile.role == 'admin':
        return True
    if self.status != 'received':
        return False
    
    # 申請種別の承認ロールに所属しているかチェック
    try:
        type_config = ApplicationTypeConfig.objects.get(application_type=self.application_type)
        return type_config.approver_role.members.filter(user=user).exists()
    except ApplicationTypeConfig.DoesNotExist:
        # 設定がない場合はフォールバック
        return user.profile.role == 'approver'
```

**影響度**: ★★★★★（重大）

---

### 9. テストコード - **影響大**

#### 新規追加が必要なテスト

- `test_workflow_role.py` - ロール管理のテスト
- `test_role_member.py` - ロールメンバー管理のテスト
- `test_application_type_config.py` - 申請種別設定のテスト
- `test_role_based_permissions.py` - ロールベース権限のテスト

#### 既存テストの修正
- 権限チェックのテストを全て見直し
- メール通知のテストを修正

**影響度**: ★★★★☆（大）

---

## 作業工数見積もり

### フェーズ1: データモデル設計・実装（3-5日）
- 新規モデルの設計・実装: 1日
- マイグレーションファイル作成: 0.5日
- データ移行スクリプト作成: 1日
- テスト: 1日
- レビュー・修正: 0.5-2.5日

### フェーズ2: ビジネスロジック変更（5-7日）
- Applicationモデルのメソッド変更: 2日
- ビューの変更: 2日
- 権限チェックロジックの実装: 1日
- テスト: 1-2日
- レビュー・修正: 1-2日

### フェーズ3: 管理機能実装（4-6日）
- ロール管理画面: 1.5日
- ロールメンバー管理画面: 1.5日
- 申請種別設定画面: 1日
- 管理画面の実装: 0.5日
- テスト: 1日
- レビュー・修正: 0.5-2日

### フェーズ4: UI/UX調整（2-3日）
- テンプレート修正: 1日
- 動作確認: 0.5日
- バグ修正: 0.5-1.5日

### フェーズ5: テスト・品質保証（3-5日）
- 単体テスト作成: 1.5日
- 結合テスト: 1日
- バグ修正: 0.5-2.5日

### フェーズ6: ドキュメント作成（1-2日）
- 設計書更新: 0.5日
- 操作マニュアル作成: 0.5-1.5日

**合計工数: 18-28日（約3.6-5.6週間）**

---

## リスク分析

### 高リスク（★★★）

1. **データ移行の複雑性**
   - 既存の申請データを新しいロール体系にマッピングする必要がある
   - 既存ユーザーのロール設定をWorkflowRoleに移行する必要がある
   - リスク: データ不整合、権限喪失

2. **権限チェックの漏れ**
   - 全ての権限チェック箇所を漏れなく修正する必要がある
   - リスク: セキュリティホール、不正アクセス

3. **既存ワークフローへの影響**
   - 進行中の申請が正常に処理できなくなる可能性
   - リスク: 業務停止

### 中リスク（★★）

4. **パフォーマンス低下**
   - ロールチェックのクエリが複雑化
   - リスク: 画面表示の遅延

5. **ユーザー混乱**
   - UIの変更により既存ユーザーが操作に迷う
   - リスク: サポート問い合わせ増加

### 低リスク（★）

6. **メール通知の遅延**
   - 通知先ユーザーの取得処理が複雑化
   - リスク: 通知遅延

---

## 対策・推奨事項

### 1. 段階的移行戦略

#### ステップ1: 新機能の並行稼働
- 既存のロールシステムを残したまま、新しいワークフローロールを追加
- ApplicationTypeConfigが未設定の場合は既存ロジックにフォールバック
- 移行期間: 2週間

#### ステップ2: データ移行
- 既存のロール設定を新しいWorkflowRoleに自動マッピング
- 申請種別ごとにデフォルトのロール設定を作成
- 管理者による設定確認・調整期間: 1週間

#### ステップ3: 完全移行
- 既存ロールシステムを廃止
- フォールバックロジックを削除

### 2. データ移行スクリプト

```python
# management/commands/migrate_to_workflow_roles.py
from django.core.management.base import BaseCommand
from workflow.models import WorkflowRole, RoleMember, ApplicationTypeConfig, Application
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. デフォルトロールの作成
        receiver_role, _ = WorkflowRole.objects.get_or_create(
            name='一般受付',
            defaults={'role_type': 'receiver', 'description': '全ての申請種別の受付を担当'}
        )
        
        approver_role, _ = WorkflowRole.objects.get_or_create(
            name='一般承認',
            defaults={'role_type': 'approver', 'description': '全ての申請種別の承認を担当'}
        )
        
        # 2. 既存ユーザーのロールマッピング
        receivers = User.objects.filter(profile__role='receiver', is_active=True)
        for user in receivers:
            RoleMember.objects.get_or_create(role=receiver_role, user=user)
        
        approvers = User.objects.filter(profile__role='approver', is_active=True)
        for user in approvers:
            RoleMember.objects.get_or_create(role=approver_role, user=user)
        
        # 3. 申請種別設定の作成
        for app_type, _ in Application.APPLICATION_TYPE_CHOICES:
            ApplicationTypeConfig.objects.get_or_create(
                application_type=app_type,
                defaults={
                    'receiver_role': receiver_role,
                    'approver_role': approver_role
                }
            )
        
        self.stdout.write(self.style.SUCCESS('移行完了'))
```

### 3. パフォーマンス最適化

```python
# 頻繁にアクセスされるクエリのキャッシュ
from django.core.cache import cache

def get_user_receivable_types(user):
    """ユーザーが受付可能な申請種別のリストを取得（キャッシュ付き）"""
    cache_key = f'user_receivable_types_{user.id}'
    types = cache.get(cache_key)
    
    if types is None:
        user_roles = user.workflow_roles.filter(role__role_type='receiver', role__is_active=True)
        configs = ApplicationTypeConfig.objects.filter(receiver_role__in=user_roles)
        types = [config.application_type for config in configs]
        cache.set(cache_key, types, 3600)  # 1時間キャッシュ
    
    return types
```

### 4. テスト戦略

- **単体テスト**: 全ての新規モデルとメソッドをカバー
- **結合テスト**: ワークフロー全体の動作確認
- **権限テスト**: 各ロールでのアクセス権限を網羅的にテスト
- **パフォーマンステスト**: 大量データでの動作確認

### 5. ロールバック計画

```python
# ロールバック用マイグレーション
# 新機能を無効化し、既存システムに戻す手順を用意
```

---

## まとめ

### 変更の影響範囲

| 項目 | 影響度 | 作業量 | リスク |
|------|--------|--------|--------|
| データモデル | ★★★★★ | 大 | 高 |
| ビュー | ★★★★☆ | 大 | 高 |
| フォーム | ★★☆☆☆ | 小 | 低 |
| テンプレート | ★★★☆☆ | 中 | 中 |
| URL設定 | ★★☆☆☆ | 小 | 低 |
| 管理画面 | ★★★☆☆ | 中 | 中 |
| メール通知 | ★★★★☆ | 大 | 高 |
| 権限チェック | ★★★★★ | 大 | 高 |
| テスト | ★★★★☆ | 大 | 中 |

### 実装推奨事項

1. **段階的移行**: 一度に全てを変更せず、フォールバック機能を持たせる
2. **十分なテスト期間**: 最低2週間のテスト期間を確保
3. **ドキュメント整備**: ユーザーマニュアルと管理者マニュアルを用意
4. **ロールバック準備**: 問題発生時に即座に戻せる体制を整備
5. **ユーザートレーニング**: 管理者向けに新機能の説明会を実施

### 結論

この変更は**システム全体に大きな影響を与える重要な変更**です。特にデータモデルと権限チェックロジックへの影響が大きく、慎重な設計と実装、十分なテスト期間が必要です。

推奨実装期間: **4-6週間**（テスト・移行期間含む）
