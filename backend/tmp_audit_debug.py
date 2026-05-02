import asyncio
import os

os.chdir(r'C:\Users\manas\OneDrive\Desktop\LAOS\backend')
from app.api.v1.endpoints.admin import get_audit_logs
from app.models.enums import AuditEventType
from app.models.domain.models import AuditLog
from tests.utils import FakeSession
from tests.factories import make_audit_log

async def run():
    db = FakeSession({AuditLog: [
        make_audit_log(action='UPLOAD', event_type=AuditEventType.DOCUMENT_UPLOADED),
        make_audit_log(action='VERIFY', event_type=AuditEventType.FIELD_VERIFIED),
    ]})
    result = await get_audit_logs(db=db, action='UPLOAD', page=1, per_page=50)
    print(type(result))
    print(result)
    print('total', result.total)
    print('items', [item.action for item in result.items])

asyncio.run(run())
