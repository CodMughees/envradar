# Launch notes

## Positioning

Pitch envradar as a tiny developer tool that fixes the most boring source of broken setup instructions: env drift.

## Demo angle

Use a repo that intentionally has:

- one missing variable in `.env.example`
- one stale variable that no longer exists in code
- one CI secret
- one Docker Compose placeholder

Then show `envradar . --format markdown` in a short terminal demo.

## Good first launch channels

- GitHub README + animated terminal GIF
- Hacker News: "Show HN: envradar – catch undocumented env vars before publishing your repo"
- Reddit communities for Python, JavaScript, DevOps, and self-hosting
- Dev.to or Hashnode post about fixing `.env.example` drift
- X / LinkedIn post with before-and-after terminal output
