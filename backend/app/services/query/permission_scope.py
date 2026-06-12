"""Permission scope calculation from UserContext."""
from app.schemas.auth import UserContext


class PermissionScope:
    """Calculate WHERE filter conditions based on user role.

    Rules (QueryExecutor injects the first matching column):
      role_level=0 superadmin -> no filter
      role_level=1 admin     -> WHERE org_code = ?
      role_level=2 teacher   -> WHERE dept_code = ?
      role_level=3 student   -> WHERE user_id = ?
    """

    def __init__(self, user_ctx: UserContext):
        self.role_level = user_ctx.role_level
        self.user_id = user_ctx.user_id
        self.dept_code = user_ctx.dept_code

    @property
    def is_superadmin(self) -> bool:
        return self.role_level == 0

    def get_filters(self) -> list[tuple[str, str]]:
        """Return [(column_name, value), ...] in priority order.
        QueryExecutor picks the first column that exists in the queried table.
        """
        if self.role_level == 0:
            return []
        elif self.role_level == 1:
            return [("org_code", self.dept_code)]
        elif self.role_level == 2:
            return [("dept_code", self.dept_code)]
        else:
            return [("user_id", self.user_id)]
