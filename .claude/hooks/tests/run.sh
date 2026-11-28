#!/usr/bin/env bash
# Run from the repo root:  bash .claude/hooks/tests/run.sh < .claude/hooks/tests/cases.tsv
# scripts/check.py runs the same cases ("Agent guard"); this is the by-hand version.
# Each case line: expected-exit <TAB> mode <TAB> key <TAB> value [<TAB> tool-name]
# Backslashes in value are literal; the token <NL> means a newline.
# tool-name (optional) is sent as tool_name, for the *-files modes.
# A line `#@ branch=<name|detached>` sets the branch for the cases after it (#219).
# The guard runs inside a throwaway git repo on that branch (default
# step/guard-test), so the commit/push cases don't depend on the branch you're on.
guard="$(pwd)/.claude/hooks/agent-guard.mjs"
repo="$(mktemp -d)"; trap 'rm -rf "$repo"' EXIT
export GIT_AUTHOR_NAME=guard-test GIT_AUTHOR_EMAIL=guard-test@example.invalid
export GIT_COMMITTER_NAME=guard-test GIT_COMMITTER_EMAIL=guard-test@example.invalid
( cd "$repo" && git init -q -b main && git commit -q --allow-empty -m init ) || { echo "could not set up the test repo"; exit 1; }
setbranch(){ if [ "$1" = detached ]; then ( cd "$repo" && git switch -q --detach main ); else ( cd "$repo" && git switch -q -C "$1" main ); fi; }
setbranch step/guard-test
pass=0; fail=0
run(){ exp="$1"; mode="$2"; key="$3"; val="${4//<NL>/$'\n'}"; tool="$5"
  node -e 'const [k,v,t]=process.argv.slice(1);const o={tool_input:{[k]:v}};if(t)o.tool_name=t;process.stdout.write(JSON.stringify(o))' "$key" "$val" "$tool" \
   | ( cd "$repo" && node "$guard" "$mode" ) >/dev/null 2>&1; got=$?
  if [ "$got" = "$exp" ]; then r=ok; pass=$((pass+1)); else r=FAIL; fail=$((fail+1)); fi
  printf '%-4s exp=%s got=%s  %-14s %-5s %s\n' "$r" "$exp" "$got" "$mode" "$tool" "$(printf '%s' "$4" | cut -c1-90)"; }
while IFS=$'\t' read -r e m k v t; do
  [ -z "$e" ] && continue
  if [ "${e:0:10}" = "#@ branch=" ]; then echo "$e"; setbranch "${e:10}"; continue; fi
  if [ "${e:0:1}" = "#" ]; then echo "$e"; continue; fi
  run "$e" "$m" "$k" "$v" "$t"
done
echo "TOTAL: $pass passed, $fail failed"
