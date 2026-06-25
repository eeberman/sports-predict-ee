# SportsPredict Email Automation Handoff

## Current Status

- MVP automation code has been implemented locally.
- GitHub Actions workflow has been added at `.github/workflows/sportspredict-email.yml`.
- The workflow runs every 15 minutes, builds one email per match in the T-65 to T-50 minute window, and never auto-submits to SportsPredict.
- The email table uses `# | Question | Prob | Source tier | Derivation`.
- The MVP source stack is SportsPredict + The Odds API + Resend.
- Resend domain chosen: `sportspredictee.com`.
- Resend DNS verification is still pending. Resend says DNS record checks can take a few hours.
- A local API check against Resend returned `401 Unauthorized` before DNS was verified, so the sender could not be confirmed programmatically yet.

## Files Added

- `automation/`: automation package and CLI.
- `automation/runner.py`: entrypoint, run with `python -m automation.runner`.
- `automation/resolver.py`: market-only resolver rules.
- `automation/odds.py`: The Odds API fetch/normalization.
- `automation/emailer.py`: email markdown rendering and Resend delivery.
- `automation_state/sent_emails.json`: duplicate-send state.
- `.github/workflows/sportspredict-email.yml`: off-machine scheduled workflow.
- `tests/test_automation.py`: resolver tests.

## Required GitHub Secrets

Add these at GitHub repo `Settings -> Secrets and variables -> Actions -> New repository secret`:

- `SPORTSPREDICT_API_KEY`
- `ODDS_API_KEY`
- `RESEND_API_KEY`
- `EMAIL_FROM`
- `EMAIL_TO`

Recommended values once Resend verifies DNS:

- `EMAIL_FROM`: `SportsPredict <alerts@sportspredictee.com>`
- `EMAIL_TO`: the personal email address that should receive predictions

Also set GitHub `Settings -> Actions -> General -> Workflow permissions` to `Read and write permissions`, because the workflow commits `automation_state` and generated email outputs.

## Next Steps

1. Wait for Resend to show `sportspredictee.com` as verified.
2. In Resend, create or confirm a valid API key.
3. Add the five GitHub Actions secrets listed above.
4. Commit and push the automation files.
5. In GitHub Actions, run `SportsPredict Email Automation` manually with `dry_run_email=true`.
6. Confirm artifacts/state are created and no email is sent.
7. Run again with `dry_run_email=false` after Resend verification to test real delivery.
8. Let the scheduled workflow handle future matches automatically.

## Local Test Commands

```powershell
python -m unittest discover -s tests
python -m automation.runner --dry-run-email
```

Use `--match-id` to target one match and `--now-utc` to simulate the send window.
