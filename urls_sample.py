"""
業務ワークフローシステムのURL設定
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
    
    # 一覧
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('pending-receive/', views.PendingReceiveView.as_view(), name='pending_receive'),
    path('pending-approve/', views.PendingApproveView.as_view(), name='pending_approve'),
]
