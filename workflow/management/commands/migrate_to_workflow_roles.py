"""
既存データを新しいワークフローロールシステムに移行するコマンド
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from workflow.models import WorkflowRole, RoleMember, ApplicationTypeConfig, Application


class Command(BaseCommand):
    help = '既存データを新しいワークフローロールシステムに移行'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ワークフローロール移行開始 ===\n'))
        
        # 1. デフォルトロールの作成
        self.stdout.write('1. デフォルトロールを作成中...')
        receiver_role, created = WorkflowRole.objects.get_or_create(
            name='一般受付',
            defaults={
                'role_type': 'receiver',
                'description': '全ての申請種別の受付を担当するデフォルトロール'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'   ✓ 受付ロール "{receiver_role.name}" を作成しました'))
        else:
            self.stdout.write(self.style.WARNING(f'   - 受付ロール "{receiver_role.name}" は既に存在します'))
        
        approver_role, created = WorkflowRole.objects.get_or_create(
            name='一般承認',
            defaults={
                'role_type': 'approver',
                'description': '全ての申請種別の承認を担当するデフォルトロール'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'   ✓ 承認ロール "{approver_role.name}" を作成しました'))
        else:
            self.stdout.write(self.style.WARNING(f'   - 承認ロール "{approver_role.name}" は既に存在します'))
        
        # 2. 既存ユーザーのロールマッピング
        self.stdout.write('\n2. 既存ユーザーをロールにマッピング中...')
        
        # 受付担当のマッピング
        receivers = User.objects.filter(profile__role='receiver', is_active=True)
        receiver_count = 0
        for user in receivers:
            _, created = RoleMember.objects.get_or_create(
                role=receiver_role,
                user=user,
                defaults={'assigned_by': None}
            )
            if created:
                receiver_count += 1
                self.stdout.write(self.style.SUCCESS(f'   ✓ {user.username} を受付ロールに追加'))
        
        self.stdout.write(self.style.SUCCESS(f'   受付担当: {receiver_count}人を追加しました'))
        
        # 承認者のマッピング
        approvers = User.objects.filter(profile__role='approver', is_active=True)
        approver_count = 0
        for user in approvers:
            _, created = RoleMember.objects.get_or_create(
                role=approver_role,
                user=user,
                defaults={'assigned_by': None}
            )
            if created:
                approver_count += 1
                self.stdout.write(self.style.SUCCESS(f'   ✓ {user.username} を承認ロールに追加'))
        
        self.stdout.write(self.style.SUCCESS(f'   承認者: {approver_count}人を追加しました'))
        
        # 3. 申請種別設定の作成
        self.stdout.write('\n3. 申請種別設定を作成中...')
        
        config_count = 0
        for app_type, app_type_display in Application.APPLICATION_TYPE_CHOICES:
            config, created = ApplicationTypeConfig.objects.get_or_create(
                application_type=app_type,
                defaults={
                    'receiver_role': receiver_role,
                    'approver_role': approver_role,
                    'is_active': True
                }
            )
            if created:
                config_count += 1
                self.stdout.write(self.style.SUCCESS(f'   ✓ {app_type_display} の設定を作成'))
            else:
                self.stdout.write(self.style.WARNING(f'   - {app_type_display} の設定は既に存在します'))
        
        self.stdout.write(self.style.SUCCESS(f'   {config_count}件の申請種別設定を作成しました'))
        
        # 4. サマリー表示
        self.stdout.write(self.style.SUCCESS('\n=== 移行完了 ==='))
        self.stdout.write(f'ロール数: {WorkflowRole.objects.count()}')
        self.stdout.write(f'ロールメンバー数: {RoleMember.objects.count()}')
        self.stdout.write(f'申請種別設定数: {ApplicationTypeConfig.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n移行が正常に完了しました！'))
