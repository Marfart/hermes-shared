# Stale Remote Refs & False Version Lag

`hermes --version` reports "N commits behind — run 'hermes update'" using
whatever remote refs the local clone has cached. If `git fetch` hasn't run
recently, the count can be wildly inflated.

## Concrete Example (v0.15.1 → 17 real commits)

| Measurement | Value | Source |
|------------|-------|--------|
| `hermes --version` report | 325 commits behind | Cached remote ref, possibly stale since mid-May |
| `git fetch origin` then `git log --oneline HEAD..origin/main | wc -l` | 17 | Fresh refs from current HEAD |
| Latest tag | `v2026.5.29.2` (v0.15.2) | Same as HEAD~1, plus 15 more post-tag commits |

**The 325 was the cumulative delta since the last fetch (possibly weeks old),
not the delta since HEAD.** The real pending delta was 17.

## Why This Happens

- On Windows git-bash, `git fetch` is not automatic unless configured
- `hermes --version` calls `git rev-list --count HEAD..@{upstream}` which
  reads from locally cached remote refs (`refs/remotes/origin/main`)
- Those refs only update when `git fetch` (or `git pull`) runs
- The last `hermes update` or `git pull` may have been days/weeks ago,
  accumulating all upstream commits in the interim as "behind"

## Fix

**Always `git fetch origin` before interpreting the commit count.**

```bash
cd ~/AppData/Local/hermes/hermes-agent
git fetch origin                 # Get fresh remote refs
hermes --version                 # Now the count is accurate
```

If you can't write scripts (doing this from a cron job), at minimum:

```bash
# Stale check: if state.db hasn't been updated in 24h, counter may be stale
# Better: just always fetch before checking
git fetch origin --quiet
```

## Broader Lesson

Any CLI tool that computes "ahead/behind" from local git refs is subject to
this same stale-ref problem. The `hermes --version` output is not lying — it's
working with cached data that hasn't been refreshed. The fix is always to
refresh before interpreting.