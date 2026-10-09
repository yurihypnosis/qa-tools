# ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
"""ログインと、リクエストしたユーザーの特定。"""
from dataclasses import dataclass

ROLES = ("DUMMY管理者", "DUMMY一般ユーザー", "DUMMY閲覧者")


@dataclass
class User:
    id: int
    email: str
    role: str | None


def login(email: str, password: str) -> str:
    """メールアドレスとパスワードを確かめ、トークンを返す。"""
    raise NotImplementedError


def current_user(token: str) -> User:
    """トークンからユーザーを引く。"""
    raise NotImplementedError


def require_role(user: User, *roles: str) -> None:
    if user.role not in roles:
        raise PermissionError("権限がありません")
