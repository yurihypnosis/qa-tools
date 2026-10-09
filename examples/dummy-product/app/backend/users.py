# ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
"""ワークスペースのメンバーとプロフィール。"""
from .auth import User, require_role


def list_members(user: User) -> list[User]:
    require_role(user, "DUMMY管理者")
    raise NotImplementedError


def update_profile(user: User, name: str) -> None:
    raise NotImplementedError
