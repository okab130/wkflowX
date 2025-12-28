# ダッシュボード表示条件変更 - 詳細分析と実装ガイド

## 📋 確定仕様

### 表示条件（OR条件）
1. **自分が申請した伝票**（全ステータス）
2. **自分が受付する伝票**（申請中のみ）
3. **自分が承認する伝票**（受付済のみ）

### 重要な設計思想
**責任範囲の明確化**
- 受付担当: 申請中 → 受付済への処理
- 承認者: 受付済 → 承認済への処理
- 各ロールは自分の担当ステータスのみ表示

---

## 🎯 ユーザー別の動作詳細

### パターン1: vendor（取引先）のみ

```
【ユーザー】
- username: vendor1
- ロール: vendor
- 所属ワークフローロール: なし

【表示される伝票】
✓ 自分が申請した全伝票
  - 下書き（draft）
  - 申請中（submitted）
  - 受付済（received）
  - 承認済（approved）
  - 却下（rejected）
  - 差し戻し（returned）

【表示されない伝票】
✗ 他人が申請した伝票（全て）
```

**変更前後の比較:**
- 変更なし ✓

---

### パターン2: receiver（受付担当）のみ

```
【ユーザー】
- username: receiver1
- ロール: receiver
- 所属ワークフローロール: 工事受付チーム

【表示される伝票】
✓ 自分が申請した全伝票（全ステータス）
✓ 工事申請（申請中）← 他人の伝票

【表示されない伝票】
✗ 工事申請（受付済）← 承認者の責任範囲
✗ 工事申請（承認済）
✗ 作業申請（全て）← 担当外
```

**業務フロー:**
```
1. ダッシュボードで「申請中」の工事申請を確認
2. 詳細画面で内容確認
3. 受付処理 → ステータスが「受付済」に変更
4. ダッシュボードから消える（承認者の担当になる）
```

**変更前:**
```
受付前: 工事申請（申請中）✓
受付後: 工事申請（受付済）✓ ← 引き続き見える
承認後: 工事申請（承認済）✓
```

**変更後:**
```
受付前: 工事申請（申請中）✓
受付後: 工事申請（受付済）✗ ← 見えなくなる（仕様）
承認後: 工事申請（承認済）✗
```

**進捗確認方法:**
```
方法1: 詳細画面にブックマーク
方法2: 「受付待ち一覧」から履歴確認
方法3: 申請番号で検索（検索機能）
方法4: 承認ロールも付与（兼任）
```

---

### パターン3: approver（承認者）のみ

```
【ユーザー】
- username: approver1
- ロール: approver
- 所属ワークフローロール: 一般承認チーム

【表示される伝票】
✓ 自分が申請した全伝票（全ステータス）
✓ 一般申請（受付済）← 他人の伝票

【表示されない伝票】
✗ 一般申請（申請中）← 受付担当の責任範囲
✗ 一般申請（承認済）← 処理済み
✗ 工事申請（全て）← 担当外
```

**業務フロー:**
```
1. ダッシュボードで「受付済」の一般申請を確認
2. 詳細画面で内容確認
3. 承認処理 → ステータスが「承認済」に変更
4. ダッシュボードから消える（処理完了）
```

---

### パターン4: receiver + approver（兼任）

```
【ユーザー】
- username: manager1
- ロール: receiver
- 所属ワークフローロール:
  - 工事受付チーム（受付）
  - 一般承認チーム（承認）

【表示される伝票】
✓ 自分が申請した全伝票
✓ 工事申請（申請中）← 受付担当として
✓ 一般申請（受付済）← 承認者として

【業務フロー】
1. 工事申請（申請中）を受付処理
2. 一般申請（受付済）を承認処理
3. 自分の申請も同時に確認可能
```

**メリット:**
- 1つのダッシュボードで複数の責任を管理
- ロール切り替え不要

---

## 📊 具体的な表示例

### ケース1: 通常の受付担当

```
【データベースの状態】
申請ID | 申請種別 | ステータス | 申請者 | 担当ロール
-------|---------|-----------|--------|----------
APP001 | 工事    | 申請中    | vendor1| 工事受付
APP002 | 工事    | 受付済    | vendor2| 工事承認
APP003 | 工事    | 承認済    | vendor3| -
APP004 | 作業    | 申請中    | vendor4| 作業受付
APP005 | 工事    | 申請中    | receiver1（自分）| -

【receiver1のダッシュボード】
✓ APP001（工事/申請中）← 担当範囲
✗ APP002（工事/受付済）← 承認者の範囲
✗ APP003（工事/承認済）← 完了
✗ APP004（作業/申請中）← 担当外
✓ APP005（工事/申請中）← 自分の申請
```

### ケース2: 兼任ユーザー

```
【manager1の設定】
- 工事受付チーム（受付ロール）
- 作業承認チーム（承認ロール）

【ダッシュボード表示】
✓ 工事申請（申請中）← 受付担当として
✓ 作業申請（受付済）← 承認者として
✓ 自分の申請（全ステータス）
✗ 工事申請（受付済）← 承認ロール未所属
✗ 作業申請（申請中）← 受付ロール未所属
```

---

## ⚠️ 業務上の変更点と対応

### 変更点1: 受付後の伝票が見えなくなる

**影響を受ける業務:**
```
【現在の業務】
1. 受付担当が申請を受付
2. ダッシュボードで「受付済」を確認
3. 承認者に電話で確認依頼
4. ダッシュボードで承認状況を監視

【変更後の業務】
1. 受付担当が申請を受付
2. ダッシュボードから消える ← 変更点
3. 承認者に電話で確認依頼
4. 詳細画面または検索で確認 ← 変更点
```

**推奨対応:**
```
オプション1: 受付完了後はメールで進捗通知
オプション2: 申請番号をメモして検索で確認
オプション3: 「受付待ち一覧」に履歴機能を追加
オプション4: 承認ロールも付与（兼任化）
```

### 変更点2: ステータスフィルターの動作

**現在:**
```
受付担当が「承認済」でフィルター
→ 工事申請の承認済伝票が表示される
```

**変更後:**
```
受付担当が「承認済」でフィルター
→ 自分が申請した承認済伝票のみ表示
→ 他人の承認済伝票は表示されない（責任範囲外）
```

**影響:**
- フィルター機能は「自分の責任範囲内」で動作
- より明確な責任分離

---

## 🔧 実装の詳細

### 実装コード（完全版）

```python
class DashboardView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'workflow/dashboard.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # 条件1: 自分が申請した伝票（全ステータス）
        my_applications = Application.objects.filter(applicant=user)
        
        # 条件2: 自分が受付する伝票（申請中のみ）
        receivable_applications = Application.objects.none()
        if hasattr(user, 'profile'):
            receivable_types = self._get_user_receivable_types(user)
            if receivable_types:
                receivable_applications = Application.objects.filter(
                    status='submitted',  # 申請中のみ
                    application_type__in=receivable_types
                ).exclude(
                    applicant=user  # 自分の申請は除外（条件1で含まれる）
                )
        
        # 条件3: 自分が承認する伝票（受付済のみ）
        approvable_applications = Application.objects.none()
        if hasattr(user, 'profile'):
            approvable_types = self._get_user_approvable_types(user)
            if approvable_types:
                approvable_applications = Application.objects.filter(
                    status='received',  # 受付済のみ
                    application_type__in=approvable_types
                ).exclude(
                    applicant=user  # 自分の申請は除外（条件1で含まれる）
                )
        
        # 3条件のOR結合
        queryset = (
            my_applications | 
            receivable_applications | 
            approvable_applications
        ).distinct()
        
        # 検索条件の適用
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(application_number__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )
        
        # ステータスフィルターの適用
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 申請種別フィルターの適用
        type_filter = self.request.GET.get('type', '')
        if type_filter:
            queryset = queryset.filter(application_type=type_filter)
        
        return queryset.select_related(
            'applicant', 
            'applicant__profile'
        ).order_by('-created_at')
```

### SQLクエリの例

```sql
-- 最終的に生成されるSQL（概念的）
SELECT * FROM workflow_application
WHERE (
    -- 条件1: 自分が申請
    applicant_id = 1
    
    OR
    
    -- 条件2: 受付可能（申請中のみ）
    (status = 'submitted' 
     AND application_type IN ('work', 'construction')
     AND applicant_id != 1)
    
    OR
    
    -- 条件3: 承認可能（受付済のみ）
    (status = 'received' 
     AND application_type IN ('work')
     AND applicant_id != 1)
)
ORDER BY created_at DESC
LIMIT 20;
```

---

## 📈 パフォーマンス分析

### インデックス確認

```sql
-- 必要なインデックス
CREATE INDEX idx_app_status ON workflow_application(status);
CREATE INDEX idx_app_type ON workflow_application(application_type);
CREATE INDEX idx_app_applicant ON workflow_application(applicant_id);
CREATE INDEX idx_app_created ON workflow_application(created_at DESC);

-- 複合インデックス（推奨）
CREATE INDEX idx_app_status_type 
ON workflow_application(status, application_type);

CREATE INDEX idx_app_applicant_created 
ON workflow_application(applicant_id, created_at DESC);
```

### クエリプランの確認

```python
# 開発環境で実行
queryset = DashboardView().get_queryset()
print(queryset.query)  # 生成されるSQLを確認
print(queryset.explain())  # クエリプランを確認
```

---

## ✅ テストケース

### テスト1: vendor（取引先）

```python
def test_dashboard_vendor():
    # 準備
    vendor = User.objects.create_user('vendor1')
    vendor.profile.role = 'vendor'
    
    my_app = Application.objects.create(applicant=vendor, status='draft')
    other_app = Application.objects.create(applicant=other_user, status='submitted')
    
    # 実行
    view = DashboardView()
    view.request = RequestFactory().get('/')
    view.request.user = vendor
    queryset = view.get_queryset()
    
    # 検証
    assert my_app in queryset  # 自分の申請
    assert other_app not in queryset  # 他人の申請
```

### テスト2: receiver（受付担当）

```python
def test_dashboard_receiver():
    # 準備
    receiver = User.objects.create_user('receiver1')
    receiver.profile.role = 'receiver'
    
    # 工事受付ロールに追加
    role = WorkflowRole.objects.create(name='工事受付', role_type='receiver')
    RoleMember.objects.create(role=role, user=receiver)
    
    # 申請種別設定
    ApplicationTypeConfig.objects.create(
        application_type='construction',
        receiver_role=role,
        approver_role=approver_role
    )
    
    # テストデータ
    my_app = Application.objects.create(
        applicant=receiver, 
        application_type='work',
        status='draft'
    )
    
    submitted_app = Application.objects.create(
        applicant=other_user,
        application_type='construction',
        status='submitted'
    )
    
    received_app = Application.objects.create(
        applicant=other_user,
        application_type='construction',
        status='received'
    )
    
    # 実行
    view = DashboardView()
    view.request = RequestFactory().get('/')
    view.request.user = receiver
    queryset = view.get_queryset()
    
    # 検証
    assert my_app in queryset  # 自分の申請
    assert submitted_app in queryset  # 受付可能な申請中
    assert received_app not in queryset  # 受付済は見えない
```

### テスト3: 兼任ユーザー

```python
def test_dashboard_multi_role():
    # 準備
    user = User.objects.create_user('multi1')
    user.profile.role = 'receiver'
    
    # 受付と承認の両ロールに追加
    receiver_role = WorkflowRole.objects.create(name='工事受付', role_type='receiver')
    approver_role = WorkflowRole.objects.create(name='作業承認', role_type='approver')
    
    RoleMember.objects.create(role=receiver_role, user=user)
    RoleMember.objects.create(role=approver_role, user=user)
    
    # テストデータ
    construction_submitted = Application.objects.create(
        applicant=other_user,
        application_type='construction',
        status='submitted'
    )
    
    work_received = Application.objects.create(
        applicant=other_user,
        application_type='work',
        status='received'
    )
    
    # 実行
    queryset = view.get_queryset()
    
    # 検証
    assert construction_submitted in queryset  # 受付担当として
    assert work_received in queryset  # 承認者として
```

---

## 🎯 まとめ

### 確定仕様
- ✅ 自分が申請した伝票（全ステータス）
- ✅ 受付可能な申請中の伝票
- ✅ 承認可能な受付済の伝票
- ✅ 責任範囲の明確な分離

### 実装の複雑度
- **低**: 既存のロジックを組み合わせるだけ
- **工数**: 8時間（1日）

### リスク
- **中**: 受付済が見えなくなる仕様変更
- **対策**: 詳細な説明とユーザートレーニング

### 推奨
**実装推奨度**: ★★★★☆

この仕様により、各ロールの責任範囲が明確になり、より管理しやすいワークフローシステムになります。
