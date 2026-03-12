# Release And Rollback Runbook (uni-app + MCP Gateway)

## Gray Release Steps

1. Deploy gateway service with new endpoints enabled.
2. Verify `/health` and five API routes in staging.
3. Release uni-app to internal testers (or limited user scope).
4. Observe gateway logs for:
- request error rate
- timeout rate (`MCP_TIMEOUT`)
- downstream failures (`MCP_DOWNSTREAM_ERROR`)
5. Promote to full release when metrics are stable for one observation window.

## Feature Switch / Degrade

- Frontend degrade: keep encyclopedia read-only mode (hide register/generate/email actions).
- Gateway degrade: keep `/api/species/search` and `/api/users/{userId}/stats` available first.

## Rollback Steps

1. Roll back gateway to previous stable image/version.
2. Roll back frontend package to previous release artifact.
3. Verify homepage and encyclopedia are available.
4. Notify stakeholders and keep incident notes with `trace_id` samples.

