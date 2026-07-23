from .models import OperationAudit
from .security import get_client_ip, sanitize_detail


def record_audit(request, module, action, target='', success=False, message='', detail=None):
    actor = 'anonymous'
    if hasattr(request, 'session'):
        actor = request.session.get('username') or actor
    try:
        return OperationAudit.objects.create(
            actor=actor,
            client_ip=get_client_ip(request),
            module=module,
            action=action,
            target=str(target or ''),
            success=bool(success),
            message=str(message or ''),
            detail=sanitize_detail(detail or {}),
        )
    except Exception:
        return None