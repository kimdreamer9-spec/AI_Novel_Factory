import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. 열쇠 준비
KEY_FILE = 'google_key.json'
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

def test_connection():
    print("🔌 [시스템] 구글 드라이브 연결 시도 중...")
    
    try:
        # 2. 열쇠로 인증하기
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=SCOPES
        )
        
        # 3. 드라이브 서비스 빌드 (접속)
        service = build('drive', 'v3', credentials=creds)
        
        # 4. 파일 목록 가져오기 (테스트)
        # 구글 드라이브에 있는 폴더나 파일을 10개만 가져와 봅니다.
        results = service.files().list(
            pageSize=10, 
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])

        if not items:
            print("⚠️ [경고] 연결은 됐는데, 파일이 하나도 안 보입니다.")
            print("   👉 힌트: 'factory-manager' 이메일을 폴더에 초대하셨나요?")
        else:
            print("✅ [성공] 구글 드라이브 문이 열렸습니다! (보이는 파일 목록):")
            print("-" * 50)
            for item in items:
                print(f"📄 파일명: {item['name']} | ID: {item['id']}")
            print("-" * 50)
            print("🚀 이제 AI가 이 파일들을 읽어서 학습할 수 있습니다.")

    except Exception as e:
        print(f"🚨 [에러] 연결 실패: {e}")

if __name__ == '__main__':
    test_connection()