#!/usr/bin/env bash
# Run from the repo root:  bash .claude/hooks/tests/run.sh < .claude/hooks/tests/cases.tsv
# Each case line: expected-exit <TAB> mode <TAB> key <TAB> value [<TAB> tool-name]
# Backslashes in value are literal; the token <NL> means a newline.
# tool-name (optional) is sent as tool_name, for the *-files modes.
pass=0; fail=0
run(){ exp="$1"; mode="$2"; key="$3"; val="${4//<NL>/$'\n'}"; tool="$5"
  node -e 'const [k,v,t]=process.argv.slice(1);const o={tool_input:{[k]:v}};if(t)o.tool_name=t;process.stdout.write(JSON.stringify(o))' "$key" "$val" "$tool" \
   | node .claude/hooks/agent-guard.mjs "$mode" >/dev/null 2>&1; got=$?
  if [ "$got" = "$exp" ]; then r=ok; pass=$((pass+1)); else r=FAIL; fail=$((fail+1)); fi
  printf '%-4s exp=%s got=%s  %-14s %-5s %s\n' "$r" "$exp" "$got" "$mode" "$tool" "$(printf '%s' "$4" | cut -c1-90)"; }
while IFS=$'\t' read -r e m k v t; do
  [ -z "$e" ] && continue
  if [ "${e:0:1}" = "#" ]; then echo "$e"; continue; fi
  run "$e" "$m" "$k" "$v" "$t"
done
echo "TOTAL: $pass passed, $fail failed"
