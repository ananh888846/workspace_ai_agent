BEGIN;

ALTER TABLE resources
    DROP CONSTRAINT uq_resources_provider_account_type_external;

CREATE UNIQUE INDEX uq_resources_account_identity
    ON resources (provider, user_account_id, resource_type, external_id)
    WHERE user_account_id IS NOT NULL;

CREATE UNIQUE INDEX uq_resources_local_identity
    ON resources (organization_id, provider, resource_type, external_id)
    WHERE user_account_id IS NULL;

COMMIT;
