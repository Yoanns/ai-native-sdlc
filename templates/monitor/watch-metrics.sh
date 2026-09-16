#!/usr/bin/env bash
# Deterministic metric watcher. Decides WHETHER to wake Claude; Claude never
# decides that for itself. Run on a schedule (cron, CI, or a scheduled task).
#
#   1σ  log only
#   2σ  Claude diagnoses, read-only tools
#   3σ  Claude may act: open a PR, or run a pre-approved runbook
set -euo pipefail

STATE_DIR="${STATE_DIR:-.sdlc/.monitor}"
mkdir -p "$STATE_DIR"

# Kill switch, readable without a deploy.
if [ -f "$STATE_DIR/DISABLED" ]; then
  echo "monitor disabled by kill switch"; exit 0
fi

# TODO: define the metrics this repo watches: a name, a command that prints a
# single number, and the rolling window in samples.
declare -A METRICS=(
  ["test_failure_rate"]="TODO: command printing a number"
  ["post_deploy_5xx"]="TODO: command printing a number"
  ["pr_cycle_time_hours"]="TODO: command printing a number"
)
WINDOW=20
COOLDOWN_SECONDS=3600      # one invocation per metric per hour
DAILY_INVOCATION_CAP=10    # hitting the cap is itself worth a human's attention

invocations_today() { grep -c "^$(date +%F)" "$STATE_DIR/invocations.log" 2>/dev/null || echo 0; }

for name in "${!METRICS[@]}"; do
  value="$(eval "${METRICS[$name]}")" || { echo "metric $name failed to read"; continue; }
  hist="$STATE_DIR/$name.hist"

  echo "$value" >> "$hist"
  tail -n "$WINDOW" "$hist" > "$hist.tmp" && mv "$hist.tmp" "$hist"

  read -r mean sd n <<<"$(python3 - "$hist" <<'PY'
import statistics, sys
vals = [float(x) for x in open(sys.argv[1]) if x.strip()]
if len(vals) < 5:
    print("0 0", len(vals))
else:
    sd = statistics.pstdev(vals[:-1]) or 0.0
    print(statistics.fmean(vals[:-1]), sd, len(vals))
PY
)"

  # Not enough history to judge yet.
  [ "$n" -lt 5 ] && { echo "$name: warming up ($n samples)"; continue; }
  [ "$(echo "$sd == 0" | bc -l)" -eq 1 ] && { echo "$name: no variance yet"; continue; }

  dev="$(echo "scale=2; a=($value - $mean); if (a<0) a=-a; a / $sd" | bc -l)"
  tier=0
  [ "$(echo "$dev >= 2" | bc -l)" -eq 1 ] && tier=2
  [ "$(echo "$dev >= 3" | bc -l)" -eq 1 ] && tier=3

  printf '%s %s value=%s mean=%.3f sd=%.3f dev=%s tier=%s\n' \
    "$(date -Is)" "$name" "$value" "$mean" "$sd" "$dev" "$tier" >> "$STATE_DIR/metrics.log"

  [ "$tier" -eq 0 ] && continue

  # Cooldown: one invocation per metric per window.
  last="$STATE_DIR/$name.last_invocation"
  if [ -f "$last" ] && [ "$(( $(date +%s) - $(cat "$last") ))" -lt "$COOLDOWN_SECONDS" ]; then
    echo "$name: within cooldown, skipping"; continue
  fi

  if [ "$(invocations_today)" -ge "$DAILY_INVOCATION_CAP" ]; then
    echo "daily invocation cap reached — escalate to a human instead"; exit 0
  fi

  date +%s > "$last"
  echo "$(date +%F) $name tier=$tier dev=$dev" >> "$STATE_DIR/invocations.log"

  if [ "$tier" -eq 2 ]; then
    # TODO: invoke Claude with READ-ONLY tools. It diagnoses and writes a
    # finding as a new spec under .sdlc/<slug>/spec.md for on-call triage.
    echo "TODO: wake Claude read-only for $name (dev=$dev)"
  else
    # TODO: invoke Claude with act-permitted tools. Acting still means opening
    # a PR or running a pre-approved runbook — never merging or self-approving.
    echo "TODO: wake Claude act-permitted for $name (dev=$dev)"
  fi
done
