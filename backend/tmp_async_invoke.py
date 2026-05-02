import asyncio
import os

os.chdir(r'C:\Users\manas\OneDrive\Desktop\LAOS\backend')
from app.api.v1.endpoints.admin import list_users, update_user, get_audit_logs, list_departments, get_queue_status, get_system_settings
from app.models.enums import UserRole, AuditEventType, JobStatus
from tests.utils import FakeSession
from tests.factories import make_user, make_department, make_processing_job, make_audit_log
from app.models.domain.models import User, Department, ProcessingJob, AuditLog

print('list_users function is coroutine:', asyncio.iscoroutinefunction(list_users))

async def run():
    db = FakeSession({User: [make_user(email='admin@example.com', role=UserRole.ADMIN)]})
    result = await list_users(db=db, role=UserRole.ADMIN, department_id=None, page=1, per_page=50)
    print('list_users result type', type(result), 'total', result.total, 'items', len(result.items))

    user = make_user(email='user@example.com', role=UserRole.VIEWER, is_active=False)
    db2 = FakeSession({User: [user]})
    result2 = await update_user(user_id=user.id, update_data=type('UpdateData', (), {'role': UserRole.ADMIN, 'is_active': True})(), db=db2)
    print('update_user result type', type(result2), 'role', result2.role, 'is_active', result2.is_active)

    db3 = FakeSession({AuditLog: [make_audit_log(action='UPLOAD', event_type=AuditEventType.DOCUMENT_UPLOADED)]})
    result3 = await get_audit_logs(db=db3, action='UPLOAD', page=1, per_page=50)
    print('get_audit_logs result type', type(result3), 'total', result3.total)

    dept = make_department(name='Audit', code='AUD')
    dept.users = [make_user(email='u@org.com', role=UserRole.OFFICER, department_id=dept.id)]
    db4 = FakeSession({Department: [dept]})
    result4 = await list_departments(db=db4, page=1, per_page=50)
    print('list_departments result type', type(result4), 'total', result4.total, 'active_user_count', result4.items[0].active_user_count)

    db5 = FakeSession({ProcessingJob: [make_processing_job(status=JobStatus.IN_PROGRESS), make_processing_job(status=JobStatus.FAILED)]})
    result5 = await get_queue_status(db=db5)
    print('get_queue_status result type', type(result5), 'processing', result5.processing, 'failed', result5.failed)

    result6 = await get_system_settings()
    print('get_system_settings result type', type(result6), 'app_name', result6.app_name, 'version', result6.version)

asyncio.run(run())
