What's Missing / Natural Next Extensions

Media sync routes — IGMedia model is ready but no endpoint fetches/stores media from the Graph API
Redis for OAuth state — the in-memory dict won't survive restarts or multi-instance deployments
Token refresh cron — long-lived IG tokens expire in 60 days, needs auto-refresh before expiry
Admin routes — UserRole.ADMIN exists but no admin-only endpoints
Media posting — scopes exist to enable it (commented out)
Pagination on account/media list endpoints
Webhook support — for real-time IG updates