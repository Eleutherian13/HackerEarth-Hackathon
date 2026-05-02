import asyncio
import os

os.chdir(r'C:\Users\manas\OneDrive\Desktop\LAOS\backend')
from app.api.v1.endpoints.admin import get_audit_logs, AuditLog
from tests.utils import FakeSession, FakeQuery
from tests.factories import make_audit_log
from app.models.enums import AuditEventType

orig_filter = FakeQuery.filter

def debug_filter(self, *conditions):
    print('debug_filter called with', conditions)
    result = orig_filter(self, *conditions)
    print('debug_filter returned', result.count(), 'items')
    return result

FakeQuery.filter = debug_filter

async def run():
    db = FakeSession({
        AuditLog: [
            make_audit_log(action='UPLOAD', event_type=AuditEventType.DOCUMENT_UPLOADED),
            make_audit_log(action='VERIFY', event_type=AuditEventType.FIELD_VERIFIED),
        ]
    })
    result = await get_audit_logs(db=db, action='UPLOAD', page=1, per_page=50)
    print('result', result)
    print('total', result.total)
    print('items', [item.action for item in result.items])

asyncio.run(run())
