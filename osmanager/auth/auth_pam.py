class PamNotAvailable(Exception):
    """系统未安装/不可用 python-pam"""
    pass

class PamAuthError(Exception):
    """PAM 认证过程异常（非凭据错误）"""
    pass
def verify_with_pam(username: str, password: str, service: str = 'login') -> bool:
    try:
        import pam
    except ImportError as e:
        raise PamNotAvailable("python-pam 未安装或不可用") from e

    try:
        p = pam.pam()
        auth_ans = p.authenticate(username, password, service=service)
        return bool(auth_ans)
    except Exception as e:
        raise PamAuthError(f"PAM 认证异常: {e}") from e
