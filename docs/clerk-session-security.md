# Clerk production session preparation

Repository review: the backend verifies Clerk session tokens and uses their `sub`
as the sole authorization identity. It restricts authorized parties and accepts
session tokens only. The frontend uses Clerk's session/token handling; its API
helper signs out on HTTP 401. No custom idle timer or authentication database was
added. Authentication failures no longer print SDK exception text.

## Manual production configuration — not applied

In the production Clerk instance, review Sessions settings and initially choose
a **30-minute inactivity timeout** and **7-day maximum session lifetime**. These
are project recommendations, not settings changed by this repository. Confirm
availability for the selected Clerk plan and test the user experience before
launch. Clerk describes both controls in its
[session options documentation](https://clerk.com/docs/guides/secure/session-options).

Use production publishable/secret keys from the same instance. Configure the
production application domain and permitted redirect/origin settings in Clerk.
Set backend `CLERK_AUTHORIZED_PARTIES` to the exact trusted HTTPS frontend origins
(comma-separated), and `FRONTEND_URL` to the production frontend origin for CORS.
Do not use wildcard origins or retain localhost in production. Configure preview
environments deliberately with separate development credentials.

Preserve registration: email/password → email OTP verification → session.
Preserve login: email/password → session. This phase does not add login OTP.
The account settings UI continues to use Clerk. Verify sign-out, expired sessions,
direct analysis links, and cross-origin API calls with the production instance.
No Clerk Dashboard settings, keys, or Vercel configuration were changed.
