# ⚠️ テスト用のダミーです。実在の製品・仕様ではありません。
"""タスクの作成・取得・更新・削除。"""
from dataclasses import dataclass

from .auth import User, require_role


@dataclass
class Task:
    id: int
    name: str
    due_date: str | None
    assignee_id: int | None
    created_by: int


def list_tasks(user: User) -> list[Task]:
    """ワークスペースのタスクを、作成日時の新しい順に返す。"""
    raise NotImplementedError


def create_task(user: User, name: str, due_date: str | None) -> Task:
    require_role(user, "DUMMY管理者", "DUMMY一般ユーザー")
    if not name.strip():
        raise ValueError("タスク名を入力してください")
    raise NotImplementedError


def update_task(user: User, task: Task, name: str) -> Task:
    if user.role == "DUMMY一般ユーザー" and task.created_by != user.id:
        raise PermissionError("他人のタスクは編集できません")
    require_role(user, "DUMMY管理者", "DUMMY一般ユーザー")
    raise NotImplementedError


def delete_task(user: User, task: Task) -> None:
    if user.role == "DUMMY一般ユーザー" and task.created_by != user.id:
        raise PermissionError("他人のタスクは削除できません")
    require_role(user, "DUMMY管理者", "DUMMY一般ユーザー")
    raise NotImplementedError
