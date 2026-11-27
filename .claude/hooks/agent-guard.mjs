// PreToolUse hook for the planner, reviewer and builder subagents.
//
// Claude Code can't limit a subagent's Bash to certain commands through the
// `tools:` field, so each agent's frontmatter runs this script before a tool
// call:   node .claude/hooks/agent-guard.mjs <mode>
//
// planner, reviewer (Bash): read-only git and gh commands only, plus one
//   comment (planner: `gh issue comment <n>`, reviewer: `gh pr comment <n>`),
//   posted as `--body-file -` with a quoted heredoc so the body is never run.
// builder (Bash): only the git and gh subcommands a build needs (no git
//   config/remote/aliases, no gh writes besides `gh pr create`), no inline
//   interpreter code, no merges, no pushes to main, no force pushes, no
//   commits on main, files staged by name only, and nothing that names a
//   .claude path or CLAUDE.md.
// builder-files (Edit/Write/NotebookEdit): no file under a .claude folder and
//   no CLAUDE.md.
//
// Exit 0 = allow (the normal permission rules still apply after this).
// Exit 2 = block; stderr is shown to the agent.

import { execFileSync } from 'node:child_process';

const mode = process.argv[2];

function block(msg) {
  process.stderr.write(`agent-guard (${mode}): ${msg}\n`);
  process.exit(2);
}

let input = '';
for await (const chunk of process.stdin) input += chunk;
let toolInput;
try {
  toolInput = JSON.parse(input).tool_input ?? {};
} catch {
  block('could not read the hook input');
}
const cmd = String(toolInput.command ?? '').trim();

// A `.claude` folder anywhere in a path (the repo's agents, skills, hooks and
// settings, and the user's ~/.claude), and CLAUDE.md / CLAUDE.local.md.
const CLAUDE_DIR = /(^|[\\/])\.claude([\\/]|$)/i;
const CLAUDE_MD = /(^|[\\/])CLAUDE(\.local)?\.md$/i;

// gh api with any write form: -X/--method (incl. -XPOST, --method=POST),
// -f/-F/--field/--raw-field (they switch to POST) or --input.
const GH_API_WRITE = / (-X|--method|-f|-F|--field|--raw-field|--input)/;

// ---------- builder: Edit / Write / NotebookEdit ----------

if (mode === 'builder-files') {
  const p = String(toolInput.file_path ?? toolInput.notebook_path ?? '');
  if (!p) block('no file path in the tool input.');
  if (CLAUDE_DIR.test(p)) block(`the builder never edits anything under .claude/ (${p}); escalate instead.`);
  if (CLAUDE_MD.test(p)) block(`the builder never edits CLAUDE.md (${p}); return ESCALATE instead.`);
  process.exit(0);
}

// ---------- read-only agents ----------

const SHELL_META = /[;&|`<>]|\$\(|\r|\n/;

const READ_ONLY = [
  /^git (status|log|diff|show|rev-parse|ls-files|merge-base|blame)( |$)/,
  /^git branch( (--show-current|-a|-r|-v|-vv|--list|--contains \S+))*$/,
  /^gh issue (view|list)( |$)/,
  /^gh pr (view|list|diff|checks)( |$)/,
  /^gh run (list|view)( |$)/,
  /^gh label list( |$)/,
  /^gh api(?= |$)/,
];

// Flags that would let a "read" command write a file or open a program.
const WRITE_FLAGS = /(^| )(--output|-o|--ext-diff|--web|-w)( |=|$)/;

// `gh issue comment 123 --body-file - <<'EOF'` ... `EOF`, nothing else.
function isHeredocComment(kind) {
  const lines = cmd.split(/\r?\n/);
  const first = lines[0].match(
    new RegExp(`^gh ${kind} comment \\d+ --body-file - <<'([A-Z_]+)'$`),
  );
  if (!first) return false;
  const end = first[1];
  if (lines.length < 3 || lines[lines.length - 1] !== end) return false;
  // The terminator must not appear earlier (that would end the body early).
  return lines.slice(1, -1).every((l) => l !== end);
}

if (mode === 'planner' || mode === 'reviewer') {
  const kind = mode === 'planner' ? 'issue' : 'pr';
  if (isHeredocComment(kind)) process.exit(0);
  if (SHELL_META.test(cmd)) {
    block(
      'one plain command per call: no ; & | > < ` $( or newlines. ' +
        `Comments go as: gh ${kind} comment <n> --body-file - <<'EOF' ... EOF`,
    );
  }
  if (WRITE_FLAGS.test(cmd)) block('--output, --ext-diff and --web are not allowed');
  if (/^gh api/.test(cmd) && GH_API_WRITE.test(cmd)) block('gh api is GET only.');
  if (READ_ONLY.some((re) => re.test(cmd))) process.exit(0);
  block(
    'read-only agent. Allowed: git status/log/diff/show/rev-parse/ls-files/' +
      'merge-base/blame/branch (list only), gh issue view/list, gh pr view/list/' +
      `diff/checks, gh run list/view, gh label list, gh api (GET), and gh ${kind} comment.`,
  );
}

// ---------- builder ----------

if (mode === 'builder') {
  // Where a command word can start: line start or after a separator/quote.
  const S = String.raw`(?:^|[\s;&|(\x60'"])`;

  // 1. Nothing that names a .claude path or CLAUDE.md (Bash can write files).
  if (new RegExp(String.raw`(^|[\s'"=:;&|(<>\\/])\.claude([\\/\s'";&|)]|$)`, 'i').test(cmd)) {
    block('the builder never touches .claude/ from Bash; use Read to read, escalate to change.');
  }
  if (/(^|[\s'"=:;&|(<>\\/])CLAUDE(\.local)?\.md\b/i.test(cmd)) {
    block('the builder never touches CLAUDE.md; return ESCALATE instead.');
  }

  // 2. No inline interpreter code (it could run git or gh out of sight).
  //    Running a script file (python scripts/x.py, python -m pytest) is fine.
  const INTERP = new RegExp(
    S +
      String.raw`(?:\S*[\\/])?(?:python3?|py|node|deno|perl|ruby|bash|sh|zsh|pwsh|powershell|cmd)(?:\.exe)?` +
      String.raw`\s+(?:\S+\s+)*?(?:-c|-e|-p|--eval|--print|-Command|/c|/k|-)(?=\s|$)`,
    'i',
  );
  if (INTERP.test(cmd)) block('no inline interpreter code (-c, -e, -Command, stdin); write a script file and run it.');
  if (new RegExp(S + String.raw`(eval|exec|xargs|source)\s`).test(cmd)) block('no eval, exec, xargs or source.');

  // 3. git: allowed subcommands only. Every `git <word>` in the command is
  //    checked, so aliases, `git config`, `git remote`, `git -C`/`-c` and
  //    options before the subcommand are refused.
  const GIT_OK = new Set([
    'status', 'log', 'diff', 'show', 'branch', 'switch', 'checkout', 'add',
    'commit', 'push', 'pull', 'fetch', 'restore', 'rev-parse', 'ls-files',
    'merge-base', 'blame', 'rm', 'mv',
  ]);
  for (const m of cmd.matchAll(new RegExp(S + String.raw`git\s+(\S+)`, 'g'))) {
    if (!GIT_OK.has(m[1])) block(`git ${m[1]} is not allowed for the builder.`);
  }
  if (/(^|[\s;&|(])git\s+branch\b.*\s(-u|--set-upstream-to|--track|-m|-M|-d|-D|--delete)(\s|=|$)/.test(cmd)) {
    block('git branch may list or create branches only.');
  }
  if (/(^|[\s;&|(])git\s+(checkout|switch)\b.*\s(-B|-C|--force|-f|--orphan)(\s|$)/.test(cmd)) {
    block('no forced or orphan checkouts.');
  }

  // 4. Stage by named path only.
  const add = cmd.match(/(?:^|[\s;&|(])git\s+add\b(.*)/);
  if (add && /(^|\s)(-A|--all|-u|--update|--no-ignore-removal|\.|\.\/|:\/|:\S*|\*\S*|\S*\*\S*)(?=\s|$|[;&|)])/.test(add[1])) {
    block('stage files by named path only: never git add -A, git add ., -u, :/ or wildcards.');
  }
  const commit = cmd.match(/(?:^|[\s;&|(])git\s+commit\b(.*)/);
  if (commit && /(^|\s)(-a\S*|--all|-\S*a\S*m|--include)(?=\s|$)/.test(commit[1])) {
    block('no git commit -a / -am / --all: stage named paths with git add first.');
  }
  // Pathspecs that would sweep in .claude/ or CLAUDE.md without naming them.
  if (/(^|[\s;&|(])git\s+(checkout|restore)\b.*\s(\.|\.\/|:\/|\*)(\s|$)/.test(cmd)) {
    block('restore or check out named paths only (not . or :/).');
  }

  // 5. Merges, force pushes, pushes to main.
  if (/(^|[\s;&|(])git\s+push\b/.test(cmd)) {
    if (/ (--force|-f|--force-with-lease|--mirror|--all|--delete|-d)\b/.test(cmd)) block('never force-push, mirror or delete.');
    if (/\bmain\b/.test(cmd)) block('never push to main.');
    if (cmd !== 'git push' && cmd !== 'git push -u origin HEAD') {
      block('push as a standalone plain `git push` (or `git push -u origin HEAD` the first time).');
    }
  }

  // 6. gh: read commands plus `gh pr create` only.
  const GH_OK = [
    /^issue (view|list)$/, /^pr (view|list|diff|checks|create)$/,
    /^run (list|view)$/, /^label list$/, /^api$/,
  ];
  for (const m of cmd.matchAll(new RegExp(S + String.raw`gh\s+(\S+)(?:\s+(\S+))?`, 'g'))) {
    const sub = m[1] === 'api' ? 'api' : `${m[1]} ${m[2] ?? ''}`.trim();
    if (!GH_OK.some((re) => re.test(sub))) block(`gh ${sub} is not allowed for the builder (Ty merges, runs workflows and changes settings).`);
  }
  if (new RegExp(S + 'gh\\s+api\\b').test(cmd) && GH_API_WRITE.test(cmd)) block('gh api is GET only.');

  // 7. Never commit or push on main.
  if (/(^|[\s;&|(])git\s+(commit|push)\b/.test(cmd)) {
    if (/(^|[\s;&|(])git\s+(switch|checkout)\b/.test(cmd)) block('switch branches and commit/push in separate calls.');
    let branch = '';
    try {
      branch = execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim();
    } catch {
      block('could not read the current branch.');
    }
    if (branch === 'main' || branch === '') block(`refusing to commit or push on "${branch || 'detached HEAD'}".`);
  }
  process.exit(0);
}

block('unknown mode; expected planner, reviewer, builder or builder-files.');
