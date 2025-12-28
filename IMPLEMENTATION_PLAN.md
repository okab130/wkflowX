# ワークフロー変更実装計画

## 実装フェーズ

### フェーズ1: データモデル実装 ✅ 完了
- [x] 新規モデル追加（WorkflowRole、RoleMember、ApplicationTypeConfig）
- [x] マイグレーションファイル作成
- [x] admin.py更新
- [x] データ移行スクリプト作成

### フェーズ2: ビジネスロジック変更 ✅ 完了
- [x] Applicationモデルのメソッド更新（通知機能）
- [x] 権限チェック機能の実装（can_receive, can_approve）
- [x] ビュー更新（DashboardView, PendingReceiveView, PendingApproveView）

### フェーズ3: ビュー更新 ✅ 完了
- [x] DashboardView更新（ロールベースフィルタリング）
- [x] 権限チェック実装（キャッシュ機能付き）
- [x] 受付・承認一覧のロールベース表示

### フェーズ4: UI/テンプレート
- [ ] ロール管理画面
- [ ] 申請種別設定画面
- [ ] 既存画面の調整

### フェーズ5: テスト・ドキュメント
- [ ] 単体テスト
- [ ] 結合テスト
- [ ] ドキュメント更新

## 開始日時: 2025-12-28
## フェーズ1完了: 2025-12-28 12:36
## フェーズ2完了: 2025-12-28 12:42
## フェーズ3完了: 2025-12-28 12:43

## 実装サマリー

### フェーズ1で実装した内容
1. **新規モデル**
   - WorkflowRole: ワークフローロール（受付/承認）
   - RoleMember: ロールメンバー（ユーザーとロールの紐付け）
   - ApplicationTypeConfig: 申請種別ごとのロール設定

2. **既存モデルの更新**
   - Application.send_notification_to_receivers(): ロールベース通知
   - Application.send_notification_to_approvers(): ロールベース通知
   - Application.can_receive(): ロールベース権限チェック
   - Application.can_approve(): ロールベース権限チェック

3. **管理画面**
   - WorkflowRoleAdmin: ロール管理
   - RoleMemberAdmin: メンバー管理
   - ApplicationTypeConfigAdmin: 申請種別設定管理

4. **データ移行スクリプト**
   - migrate_to_workflow_roles.py: 既存データの自動移行

### 次のステップ
1. マイグレーションを適用: `python manage.py migrate`
2. データ移行を実行: `python manage.py migrate_to_workflow_roles`
3. ビューの更新を開始
