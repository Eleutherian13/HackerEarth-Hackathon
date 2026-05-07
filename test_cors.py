import sys
sys.path.insert(0, r'c:\Users\manas\OneDrive\Desktop\LAOS\backend')
from app.core.config import settings
print('CORS_ALLOWED_ORIGINS:')
for origin in settings.CORS_ALLOWED_ORIGINS:
    print(f'  - {origin}')
print(f'\nTotal origins: {len(settings.CORS_ALLOWED_ORIGINS)}')
print(f'http://localhost:5174 in origins: {"http://localhost:5174" in settings.CORS_ALLOWED_ORIGINS}')
