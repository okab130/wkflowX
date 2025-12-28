"""
業務ワークフローシステムのURL設定（製造業・建設業向け）
"""
from django.urls import path
from . import views

app_name = 'workflow'

urlpatterns = [
    # ダッシュボード
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # 申請関連
    path('create/', views.ApplicationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='edit'),
    path('<int:pk>/submit/', views.submit_application, name='submit'),
    
    # ワークフロー処理
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
    
    # 一覧
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('pending-receive/', views.PendingReceiveView.as_view(), name='pending_receive'),
    path('pending-approve/', views.PendingApproveView.as_view(), name='pending_approve'),
]
