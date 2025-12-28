"""
PostgreSQLにwkflowxスキーマを作成するスクリプト
"""
import psycopg2

# データベース接続
conn = psycopg2.connect(
    host='localhost',
    port='5432',
    database='postgres',
    user='postgres',
    password='pass'
)

# オートコミット設定
conn.autocommit = True
cursor = conn.cursor()

# スキーマ作成
try:
    cursor.execute("CREATE SCHEMA IF NOT EXISTS wkflowx;")
    print("✅ スキーマ 'wkflowx' を作成しました")
except Exception as e:
    print(f"❌ エラー: {e}")

# 接続クローズ
cursor.close()
conn.close()

print("完了しました！")
