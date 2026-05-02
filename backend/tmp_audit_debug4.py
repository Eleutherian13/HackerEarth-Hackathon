import asyncio
import os

os.chdir(r'C:\Users\manas\OneDrive\Desktop\LAOS\backend')
from app.api.v1.endpoints.admin import get_audit_logs, AuditLog
from tests.utils import FakeSession, FakeQuery
from tests.factories import make_audit_log
from app.models.enums import AuditEventType

orig_filter = FakeQuery.filter

def debug_filter(self, *conditions):
    print('debug_filter called with', len(conditions), 'conditions')
    for cond in conditions:
        print('  cond type', type(cond), repr(cond))
        left = cond.left
        right = cond.right
        print('   left type', type(left), 'key', getattr(left, 'key', None))
        print('   right type', type(right), 'value', getattr(right, 'value', None))
    result = orig_filter(self, *conditions)
    print('  result count', result.count())
    for item in self._items:
        try:
            actual = getattr(item, left.key)
        except Exception as e:
            actual = f'ERROR {e}'
        print('    item', item, 'actual', actual)
    return result

FakeQuery.filter = debug_filter

async def run():
    db = FakeSession({
        AuditLog: [
            make_audit_log(action='UPLOAD', event_type=AuditEventType.DOCUMENT_UPLOADED),
            make_audit_log(action='VERIFY', event_type=AuditEventType.FIELD_VERIFIED),
        ]
    })
    query = db.query(AuditLog)
    print('manual count', query.count())
    q2 = query.filter(AuditLog.action == 'UPLOAD')
    print('manual filtered count', q2.count())
    print('manual filtered items', [item.action for item in q2.all()])
    result = await get_audit_logs(db=db, action='UPLOAD', page=1, per_page=50)
    print('func result', result)
    print('func total', result.total)
    print('func items', [item.action for item in result.items])

asyncio.run(run())
