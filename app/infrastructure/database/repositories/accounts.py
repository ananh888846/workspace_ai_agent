from __future__ import annotations

from typing import Any, Sequence

from app.application.core_runtime import AccountCandidate, ExternalAccount


class PostgresAccountRepository:
    """Triển khai AccountRepository bằng PostgreSQL.

    Repository này chỉ đọc metadata tài khoản. Không đọc
    account_credentials và không tự phân giải secret.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def find_candidates(
        self,
        *,
        user_id: str,
        organization_id: str,
        provider: str,
        account_hint: str | None = None,
    ) -> Sequence[AccountCandidate]:
        params: list[Any] = [user_id, organization_id, provider]
        hint_clause = ""
        if account_hint:
            hint_clause = """
              AND (
                    ua.id::text = %s
                 OR ua.external_account_id = %s
                 OR ua.email = %s
              )
            """
            params.extend([account_hint, account_hint, account_hint])

        query = f"""
            SELECT
                account_rows.id,
                account_rows.user_id,
                account_rows.provider,
                account_rows.account_type,
                account_rows.external_account_id,
                account_rows.display_name,
                account_rows.email,
                account_rows.status,
                account_rows.account_grant_id,
                account_rows.grant_scope
            FROM (
                SELECT DISTINCT
                    ua.id,
                    ua.user_id,
                    ua.provider,
                    ua.account_type,
                    ua.external_account_id,
                    ua.display_name,
                    ua.email,
                    ua.status,
                    ag.id AS account_grant_id,
                    ag.scope AS grant_scope
                FROM user_accounts AS ua
            JOIN organization_members AS om_owner
              ON om_owner.organization_id = %s
             AND om_owner.user_id = ua.user_id
             AND om_owner.status = 'active'
            LEFT JOIN account_grants AS ag
              ON ag.user_account_id = ua.id
             AND ag.owner_user_id = ua.user_id
             AND ag.organization_id = om_owner.organization_id
             AND ag.grantee_user_id = %s
             AND ag.status = 'active'
             AND (ag.starts_at IS NULL OR ag.starts_at <= CURRENT_TIMESTAMP)
             AND (ag.expires_at IS NULL OR ag.expires_at > CURRENT_TIMESTAMP)
             AND ag.revoked_at IS NULL
            WHERE ua.provider = %s
              AND ua.status IN ('active', 'pending_oauth')
              AND (
                    ua.user_id = %s
                 OR ag.id IS NOT NULL
              )
              {hint_clause}
            ) AS account_rows
            ORDER BY account_rows.display_name NULLS LAST,
                     account_rows.email NULLS LAST,
                     account_rows.id::text
        """

        # Giữ thứ tự placeholder rõ ràng để dễ đối chiếu với authorization contract.
        # Tạo lại danh sách tham số đúng theo thứ tự xuất hiện trong câu SQL.
        if account_hint:
            params = [organization_id, user_id, provider, user_id, account_hint, account_hint, account_hint]
        else:
            params = [organization_id, user_id, provider, user_id]

        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._to_account_candidate(row, current_user_id=user_id, organization_id=organization_id) for row in rows]

    @staticmethod
    def _to_account_candidate(row: Sequence[Any], *, current_user_id: str, organization_id: str) -> AccountCandidate:
        account = ExternalAccount(
            id=str(row[0]),
            user_id=str(row[1]),
            provider=str(row[2]),
            account_type=str(row[3]),
            external_account_id=str(row[4]),
            display_name=row[5],
            email=row[6],
            status=str(row[7]),
        )
        return AccountCandidate(
            account=account,
            access_mode="owner" if account.user_id == current_user_id else "grant",
            account_grant_id=str(row[8]) if row[8] else None,
            organization_id=organization_id,
            grant_scope=row[9] if isinstance(row[9], dict) else None,
        )
