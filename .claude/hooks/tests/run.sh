#!/usr/bin/env bash
# Run from the repo root:  bash .claude/hooks/tests/run.sh < .claude/hooks/tests/cases.tsv
# Each case line: expected-exit <TAB> mode <TAB> key <TAB> value
# Backslashes in value are literal; the token <NL> means a newline.
pass=0; fail=0
run(){ exp="$1"; mode="$2"; key="$3"; val="${4//<NL>/$'\n'}"
  node -e 'const [k,v]=process.argv.slice(1);process.stdout.write(JSON.stringify({tool_input:{[k]:v}}))' "$key" "$val" \
   | node .claude/hooks/agent-guard.mjs "$mode" >/dev/null 2>&1; got=$?
  if [ "$got" = "$exp" ]; then r=ok; pass=$((pass+1)); else r=FAIL; fail=$((fail+1)); fi
  printf '%-4s exp=%s got=%s  %-13s %s\n' "$r" "$exp" "$got" "$mode" "$(printf '%s' "$4" | cut -c1-90)"; }
while IFS=$'\t' read -r e m k v; do
  [ -z "$e" ] && continue
  if [ "${e:0:1}" = "#" ]; then echo "$e"; continue; fi
  run "$e" "$m" "$k" "$v"
done
echo "TOTAL: $pass passed, $fail failed"
