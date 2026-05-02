import asyncio
import os

os.chdir(r'C:\Users\manas\OneDrive\Desktop\LAOS\backend')
from app.api.v1.endpoints.admin import get_audit_logs, AuditLog
from tests.utils import FakeSession
from tests.factories import make_audit_log
from app.models.enums import AuditEventType


db = FakeSession({
    AuditLog: [
        make_audit_log(action='UPLOAD', event_type=AuditEventType.DOCUMENT_UPLOADED),
        make_audit_log(action='VERIFY', event_type=AuditEventType.FIELD_VERIFIED),
    ]
})
action = 'UPLOAD'
query = db.query(AuditLog)
print('direct count', query.count())
q2 = query.filter(AuditLog.action == action)
print('filtered count', q2.count())
items = q2.order_by(AuditLog.created_at.desc()).offset(0).limit(50).all()
print('direct items', [item.action for item in items])

async def run():
    result = await get_audit_logs(db=db, action=action, page=1, per_page=50)
    print('func result', result)
    print('func total', result.total)
    print('func items', [item.action for item in result.items])

asyncio.run(run())
