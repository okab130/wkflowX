# ダッシュボード表示条件変更 影響調査報告書

## 変更要件

### 現在の仕様
ダッシュボードに表示される申請一覧は、ユーザーロールに応じて以下のように表示：

| ロール | 表示される申請 |
|--------|----------------|
| vendor（取引先） | 自分が申請した伝票のみ |
| receiver（受付担当） | 自分が受付可能な申請種別の「申請中」「受付済」ステータスの伝票 |
| approver（承認者） | 自分が承認可能な申請種別の「受付済」ステータスの伝票 |
| admin（管理者） | 全ての伝票 |

### 変更後の仕様（要望）
**全ユーザー共通**: 以下の3条件のOR条件で表示
1. **自分が申請した伝票**（全ステータス）
2. **自分が受付する伝票**（受付可能な申請種別の申請中ステータスのみ）
3. **自分が承認する伝票**（承認可能な申請種別の受付済ステータスのみ）

**重要な仕様確認:**
- 受付担当は「受付済」ステータスの伝票を見ない（承認ロールに所属していない限り）
- 承認者は「申請中」ステータスの伝票を見ない（受付ロールに所属していない限り）
- 各ロールは自分の担当範囲のステータスのみを見る（明確な責任分離）

---

## 影響分析

### 1. 表示ロジックの変更

#### 現在のDashboardView.get_queryset()
```python
def get_queryset(self):
    user = self.request.user
    queryset = Application.objects.select_related('applicant', 'applicant__profile').all()
    
    # 検索・フィルター条件...
    
    # ユーザー種別でフィルタリング（ロールベース）
    if hasattr(user, 'profile'):
        if user.profile.role == 'vendor':
            queryset = queryset.filter(applicant=user)
        elif user.profile.role == 'receiver':
            receivable_types = self._get_user_receivable_types(user)
            queryset = queryset.filter(
                status__in=['submitted', 'received'],
                application_type__in=receivable_types
            )
        elif user.profile.role == 'approver':
            approvable_types = self._get_user_approvable_types(user)
            queryset = queryset.filter(
                status='received',
                application_type__in=approvable_types
            )
    
    return queryset
```

#### 変更後のロジック（提案）
```python
def get_queryset(self):
    user = self.request.user
    
    # 基本的なクエリセット
    queryset = Application.objects.select_related('applicant', 'applicant__profile').none()
    
    # 検索・フィルター条件...
    
    # 条件1: 自分が申請した伝票
    my_applications = Application.objects.filter(applicant=user)
    
    # 条件2: 自分が受付する伝票
    receivable_applications = Application.objects.none()
    if hasattr(user, 'profile'):
        receivable_types = self._get_user_receivable_types(user)
        if receivable_types:
            receivable_applications = Application.objects.filter(
                status='submitted',
                application_type__in=receivable_types
            )
    
    # 条件3: 自分が承認する伝票
    approvable_applications = Application.objects.none()
    if hasattr(user, 'profile'):
        approvable_types = self._get_user_approvable_types(user)
        if approvable_types:
            approvable_applications = Application.objects.filter(
                status='received',
                application_type__in=approvable_types
            )
    
    # 3条件のOR結合
    queryset = (my_applications | receivable_applications | approvable_applications).distinct()
    
    # 検索・フィルター適用
    if search_query:
        queryset = queryset.filter(...)
    
    return queryset
```

---

### 2. 影響を受けるユーザー種別

#### 2.1 vendor（取引先）

**現在:**
- 自分が申請した伝票のみ表示

**変更後:**
- 自分が申請した伝票のみ表示（変更なし）

**影響度:** ★☆☆☆☆（影響なし）

---

#### 2.2 receiver（受付担当）

**現在:**
- 自分が受付可能な申請種別の「申請中」「受付済」の伝票
- 例: user1が受付担当の場合、工事申請の申請中・受付済がすべて表示

**変更後:**
- 自分が申請した伝票 **（追加）**
- 自分が受付可能な申請種別の「申請中」の伝票のみ
- 「受付済」の伝票は表示されない **（削除）**

**具体例:**
```
【シナリオ】
- user1: receiver（受付担当）
- user1が工事申請の受付ロールに所属
- user1が自分で工事申請を提出

【現在】
- 他人が提出した工事申請（申請中） → 表示される ✓
- 他人が提出した工事申請（受付済） → 表示される ✓
- 他人が提出した工事申請（承認済） → 表示される ✓
- 自分が提出した作業申請（下書き） → 表示されない ✗

【変更後】
- 他人が提出した工事申請（申請中） → 表示される ✓
- 他人が提出した工事申請（受付済） → 表示されない ✗
- 他人が提出した工事申請（承認済） → 表示されない ✗
- 自分が提出した作業申請（下書き） → 表示される ✓（追加）
- 自分が提出した作業申請（全ステータス） → 表示される ✓（追加）
```

**影響:**
- ✅ 受付担当が自分で申請した伝票も見えるようになる（利便性向上）
- ⚠️ 受付済の伝票が見えなくなる（仕様変更）
  - 理由: 受付担当の責任範囲は「受付」まで
  - 承認フェーズは承認者の責任範囲
  - 責任分離の明確化

**業務への影響:**
```
【ケース1】受付担当が進捗確認したい場合
質問: 「自分が受付した伝票がその後どうなったか確認したい」

対応:
1. 「受付待ち一覧」から確認（status='submitted'の専用画面）
2. 詳細画面から確認（個別に閲覧可能）
3. 必要に応じて承認ロールも付与

【ケース2】受付と承認を兼任する場合
- 受付ロール: 申請中の伝票を処理
- 承認ロール: 受付済の伝票を処理
- 両方の伝票がダッシュボードに表示される ✓
```

**影響度:** ★★★★☆（大・仕様変更）

---

#### 2.3 approver（承認者）

**現在:**
- 自分が承認可能な申請種別の「受付済」の伝票のみ

**変更後:**
- 自分が申請した伝票 **（追加）**
- 自分が受付可能な申請種別の「申請中」の伝票 **（追加）**
- 自分が承認可能な申請種別の「受付済」の伝票

**具体例:**
```
【シナリオ】
- manager1: approver（承認者）
- manager1が工事申請の承認ロールに所属
- manager1が自分で作業申請を提出

【現在】
- 工事申請（受付済） → 表示される
- 自分が提出した作業申請 → 表示されない

【変更後】
- 工事申請（受付済） → 表示される
- 自分が提出した作業申請 → 表示される（追加）
```

**影響:**
- ✅ 承認者が自分で申請した伝票も見えるようになる（利便性向上）
- ⚠️ 受付担当も兼任している場合、申請中の伝票も表示される

**影響度:** ★★☆☆☆（小）

---

#### 2.4 兼任ユーザー

**ケース1: 受付と承認を兼任**
```
user_multi:
  - 工事受付ロールに所属
  - 一般承認ロールに所属
```

**現在の問題:**
- ロールが1つ（profile.role）のため、どちらか一方しか機能しない

**変更後:**
- 工事申請（申請中） → 表示される（受付担当として）
- 一般申請（受付済） → 表示される（承認者として）
- 自分が提出した伝票 → 表示される

**影響:**
- ✅ 複数ロールの機能が正しく動作する

**影響度:** ★★★★☆（大・改善）

---

### 3. パフォーマンスへの影響

#### 3.1 クエリの複雑化

**現在:**
```sql
-- vendor の場合
SELECT * FROM application WHERE applicant_id = 1;

-- receiver の場合
SELECT * FROM application 
WHERE status IN ('submitted', 'received')
  AND application_type IN ('work', 'construction');
```

**変更後:**
```sql
-- 全ユーザー共通
SELECT * FROM application
WHERE (
    applicant_id = 1  -- 自分が申請
    OR (status = 'submitted' AND application_type IN ('work'))  -- 受付可能
    OR (status = 'received' AND application_type IN ('construction'))  -- 承認可能
)
```

**影響:**
- OR条件の増加によりクエリプランが複雑化
- インデックスの効果が低下する可能性

**対策:**
- `UNION` を使用してクエリを分割（Django ORMの `|` 演算子を使用）
- 既存のインデックスが有効に機能

**影響度:** ★★☆☆☆（小・対策済み）

---

#### 3.2 キャッシュへの影響

**現在:**
- `user_receivable_types_{user.id}`: 受付可能な申請種別（1時間キャッシュ）
- `user_approvable_types_{user.id}`: 承認可能な申請種別（1時間キャッシュ）

**変更後:**
- 同じキャッシュを利用可能
- 追加のキャッシュは不要

**影響度:** ★☆☆☆☆（影響なし）

---

### 4. 統計情報への影響

#### 現在の統計情報（get_context_data）
```python
if user.profile.role == 'vendor':
    context['draft_count'] = Application.objects.filter(applicant=user, status='draft').count()
    context['submitted_count'] = Application.objects.filter(applicant=user, status='submitted').count()
    context['approved_count'] = Application.objects.filter(applicant=user, status='approved').count()
elif user.profile.role == 'receiver':
    context['pending_receive_count'] = Application.objects.filter(status='submitted').count()
    context['received_count'] = Application.objects.filter(status='received').count()
elif user.profile.role == 'approver':
    context['pending_approve_count'] = Application.objects.filter(status='received').count()
```

#### 変更後の統計情報（提案）
```python
# 全ユーザー共通の統計
context['my_draft_count'] = Application.objects.filter(applicant=user, status='draft').count()
context['my_submitted_count'] = Application.objects.filter(applicant=user, status='submitted').count()

# 受付待ち（受付可能な申請種別）
receivable_types = self._get_user_receivable_types(user)
if receivable_types:
    context['pending_receive_count'] = Application.objects.filter(
        status='submitted',
        application_type__in=receivable_types
    ).count()

# 承認待ち（承認可能な申請種別）
approvable_types = self._get_user_approvable_types(user)
if approvable_types:
    context['pending_approve_count'] = Application.objects.filter(
        status='received',
        application_type__in=approvable_types
    ).count()
```

**影響:**
- 統計情報がより正確になる
- ユーザーの役割に応じた適切な情報を表示

**影響度:** ★★★☆☆（中・改善）

---

### 5. UIへの影響

#### テンプレート（dashboard.html）

**現在:**
- ロールに応じて異なる統計情報を表示
- vendor: 下書き、申請中、承認済の件数
- receiver: 受付待ち、受付済の件数
- approver: 承認待ちの件数

**変更後:**
- 全ユーザー共通で以下を表示:
  - 自分の申請（下書き、申請中、承認済など）
  - 受付待ち（受付可能な場合のみ）
  - 承認待ち（承認可能な場合のみ）

**影響:**
- テンプレートの条件分岐を簡素化できる
- より直感的なUIになる

**影響度:** ★★☆☆☆（小・改善）

---

### 6. 検索・フィルター機能への影響

#### 現在
- 検索とフィルターは、ロールによる絞り込み**後**に適用

#### 変更後
- 検索とフィルターは、OR条件による絞り込み**後**に適用

**問題点:**
```
【例】
受付担当が「承認済」でフィルターした場合

【現在】
- 受付可能な申請種別の承認済伝票が表示される

【変更後】
- 自分が申請した承認済伝票
- 受付可能な申請種別の承認済伝票（ただしstatus='submitted'のみなので表示されない）
- 承認可能な申請種別の承認済伝票

→ 意図した結果と異なる可能性
```

**対策:**
- ステータスフィルターを適用する場合、OR条件の各部分に適用する必要がある

**影響度:** ★★★☆☆（中・要実装調整）

---

### 7. 既存機能への影響

#### 7.1 PendingReceiveView（受付待ち一覧）
- **影響なし**: 独立したビュー
- 引き続き受付可能な申請中の伝票のみ表示

#### 7.2 PendingApproveView（承認待ち一覧）
- **影響なし**: 独立したビュー
- 引き続き承認可能な受付済の伝票のみ表示

#### 7.3 MyApplicationsView（自分の申請一覧）
- **影響なし**: 独立したビュー
- 引き続き自分が申請した伝票のみ表示

#### 7.4 ApplicationDetailView（詳細画面）
- **影響なし**: 個別の権限チェックを実施
- アクセス制御は変更なし

---

## 実装方法

### 方法1: OR条件でクエリを結合（推奨）

```python
def get_queryset(self):
    user = self.request.user
    
    # ベースとなる空のクエリセット
    queryset = Application.objects.none()
    
    # 条件1: 自分が申請した伝票
    my_applications = Application.objects.filter(applicant=user)
    
    # 条件2: 自分が受付する伝票
    receivable_applications = Application.objects.none()
    if hasattr(user, 'profile'):
        receivable_types = self._get_user_receivable_types(user)
        if receivable_types:
            receivable_applications = Application.objects.filter(
                status='submitted',
                application_type__in=receivable_types
            )
    
    # 条件3: 自分が承認する伝票
    approvable_applications = Application.objects.none()
    if hasattr(user, 'profile'):
        approvable_types = self._get_user_approvable_types(user)
        if approvable_types:
            approvable_applications = Application.objects.filter(
                status='received',
                application_type__in=approvable_types
            )
    
    # OR条件で結合（UNION相当）
    queryset = (my_applications | receivable_applications | approvable_applications).distinct()
    
    # 検索条件の適用
    search_query = self.request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(
            Q(application_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    
    # ステータスフィルターの適用（再度絞り込み）
    status_filter = self.request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # 申請種別フィルターの適用
    type_filter = self.request.GET.get('type', '')
    if type_filter:
        queryset = queryset.filter(application_type=type_filter)
    
    return queryset.select_related('applicant', 'applicant__profile').order_by('-created_at')
```

**利点:**
- シンプルで理解しやすい
- Django ORMが最適化してくれる
- インデックスが有効に機能

**欠点:**
- 大量データの場合、パフォーマンスに注意が必要

---

### 方法2: Q オブジェクトで条件を構築

```python
def get_queryset(self):
    user = self.request.user
    
    # Q オブジェクトで条件構築
    conditions = Q(applicant=user)  # 自分が申請した伝票
    
    # 受付可能な伝票を追加
    if hasattr(user, 'profile'):
        receivable_types = self._get_user_receivable_types(user)
        if receivable_types:
            conditions |= Q(status='submitted', application_type__in=receivable_types)
        
        # 承認可能な伝票を追加
        approvable_types = self._get_user_approvable_types(user)
        if approvable_types:
            conditions |= Q(status='received', application_type__in=approvable_types)
    
    queryset = Application.objects.filter(conditions).distinct()
    
    # 検索・フィルター適用...
    
    return queryset.select_related('applicant', 'applicant__profile').order_by('-created_at')
```

**利点:**
- より効率的なSQL生成
- パフォーマンスが良い

**欠点:**
- ややコードが複雑

---

## リスク分析

### 高リスク（★★★）

1. **ステータスフィルターの動作変更**
   - 現在: ロール別にフィルター
   - 変更後: OR条件後にフィルター
   - **対策**: フィルター適用後の結果を確認、テストケース追加

2. **受付担当が受付済を見られなくなる**
   - 承認ロールに所属していない場合、受付済伝票が見えない
   - **対策**: 
     - オプション1: 受付済も表示する（status__in=['submitted', 'received']）
     - オプション2: 仕様として受け入れる

### 中リスク（★★）

3. **パフォーマンス低下**
   - OR条件の増加によるクエリの複雑化
   - **対策**: 
     - インデックス確認（status, application_type, applicant_id）
     - ページネーション維持（20件/ページ）
     - N+1問題の回避（select_related, prefetch_related）

4. **統計情報の整合性**
   - 表示件数と統計情報が一致しない可能性
   - **対策**: 統計情報のロジックも同様に変更

### 低リスク（★）

5. **キャッシュの整合性**
   - キャッシュ戦略は変更なし
   - **対策**: 不要（既存キャッシュが有効）

---

## 作業工数見積もり

| 作業項目 | 工数 |
|---------|------|
| DashboardView.get_queryset() 変更 | 2時間 |
| 統計情報（get_context_data）変更 | 1時間 |
| テンプレート調整 | 1時間 |
| 単体テスト作成 | 2時間 |
| 結合テスト | 1時間 |
| レビュー・修正 | 1時間 |
| **合計** | **8時間** |

---

## 推奨事項

### 1. 段階的実装

#### ステップ1: 基本実装（2時間）
- DashboardViewのget_queryset()を変更
- 方法1（OR条件）で実装

#### ステップ2: 統計情報更新（1時間）
- get_context_data()を更新
- テンプレートの表示を調整

#### ステップ3: テスト（3時間）
- 各ロールでの動作確認
- 検索・フィルター機能の確認
- パフォーマンステスト

#### ステップ4: 本番適用（1時間）
- ドキュメント更新
- ユーザー通知

### 2. 受付済の扱い

**確定仕様:**
- 受付担当は受付済伝票を見ない
- 理由: 責任範囲の明確化
  - 受付担当: 申請中 → 受付済への処理が責任範囲
  - 承認者: 受付済 → 承認済への処理が責任範囲

```python
# 条件2: 受付可能な伝票（申請中のみ）
receivable_applications = Application.objects.filter(
    status='submitted',  # 申請中のみ
    application_type__in=receivable_types
)

# 条件3: 承認可能な伝票（受付済のみ）
approvable_applications = Application.objects.filter(
    status='received',  # 受付済のみ
    application_type__in=approvable_types
)
```

**業務上の対応:**
- 受付後の進捗確認: 詳細画面から個別に確認
- 継続的な監視が必要: 受付と承認の両ロールを付与

### 3. パフォーマンス対策

- インデックスの確認・追加
```sql
CREATE INDEX idx_application_status_type 
ON application (status, application_type);

CREATE INDEX idx_application_applicant 
ON application (applicant_id, created_at DESC);
```

---

## まとめ

### 変更の影響範囲

| 項目 | 影響度 | 対応 |
|------|--------|------|
| DashboardView | ★★★★☆ | 要変更 |
| 統計情報 | ★★★☆☆ | 要変更 |
| テンプレート | ★★☆☆☆ | 軽微な調整 |
| 他のビュー | ★☆☆☆☆ | 影響なし |
| パフォーマンス | ★★☆☆☆ | 監視が必要 |

### 期待される効果

✅ **利便性向上**
- 受付・承認担当が自分の申請も見られる
- 兼任ユーザーの複数ロール機能が正しく動作
- 一画面で全ての関連伝票を確認可能

✅ **ロールベースワークフローの完成**
- 申請種別ごとの細かい権限制御と連携
- より柔軟な権限管理

⚠️ **注意点**
- 受付担当が受付済を見られなくなる可能性
- フィルター機能の動作が変わる
- パフォーマンス監視が必要

### 実装推奨

**推奨実装期間**: 1日（8時間）
**リスクレベル**: 中（十分なテストが必要）
**優先度**: 中〜高（ユーザビリティ向上）

**この変更により、ダッシュボードがより直感的で使いやすくなります！**
