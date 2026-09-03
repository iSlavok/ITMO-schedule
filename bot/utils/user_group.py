from app.models import Group, User


def get_user_group(user: User) -> Group:
    """The group of a registered user.

    Only guests are groupless, and every handler asking for a group sits behind a
    role filter, so a missing group here means the roles and the data disagree.
    """
    if user.group is None:
        msg = f"User {user.id} has the {user.role} role but no group"
        raise RuntimeError(msg)
    return user.group
