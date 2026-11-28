// PreToolUse hook for the planner, reviewer and builder subagents.
//
// Claude Code can't limit a subagent's Bash to certain commands through the
// `tools:` field, so each agent's frontmatter runs this script before a tool
// call:   node .claude/hooks/agent-guard.mjs <mode>
//
// planner, reviewer (Bash): read-only git and gh commands only, plus one
//   comment (planner: `gh issue comment <n>`, reviewer: `gh pr comment <n>`),
//   posted as `--body-file <file>` where the file is the agent's own comment
//   file in the Claude scratchpad. No heredoc, no inline --body / -b (#215).
// planner-files, reviewer-files (Write/Edit/NotebookEdit): the Write tool
//   only, and only the agent's own comment file in the Claude scratchpad
//   (planner: plan-<n>[-r<k>].md, reviewer: review-<pr>-r<r>.md).
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
let toolName = '';
try {
  const parsed = JSON.parse(input);
  toolInput = parsed.tool_input ?? {};
  toolName = String(parsed.tool_name ?? '');
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

// ---------- planner / reviewer: comment files ----------

// Each read-only agent may write one kind of file: its comment body.
const COMMENT_FILE = {
  planner: /^plan-\d+(-r\d+)?\.md$/,
  reviewer: /^review-\d+-r\d+\.md$/,
};

// True when `p` is a file directly inside a Claude scratchpad folder
// (…/Users/<you>/AppData/Local/Temp/claude/…/scratchpad/<name>) and <name> is
// this agent's comment file. Accepts C:\…, C:/… and Git Bash /c/… forms.
function isOwnCommentFile(agent, p) {
  const s = p.replace(/\\/g, '/');
  if (s.split('/').includes('..')) return false;
  const m = s.match(
    /^(?:[A-Za-z]:|\/[A-Za-z])\/Users\/[A-Za-z0-9._-]+\/AppData\/Local\/Temp\/claude\/(?:[A-Za-z0-9._-]+\/)+scratchpad\/([A-Za-z0-9._-]+)$/i,
  );
  return Boolean(m) && COMMENT_FILE[agent].test(m[1]);
}

if (mode === 'planner-files' || mode === 'reviewer-files') {
  const agent = mode.replace('-files', '');
  if (toolName !== 'Write') block(`the ${agent} may use Write only (got ${toolName || 'no tool name'}).`);
  const p = String(toolInput.file_path ?? '');
  if (!isOwnCommentFile(agent, p)) {
    const name = agent === 'planner' ? 'plan-<n>.md or plan-<n>-r<k>.md' : 'review-<pr>-r<r>.md';
    block(`the ${agent} writes only ${name} directly inside its Claude scratchpad folder (got ${p || 'no path'}).`);
  }
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

if (mode === 'planner' || mode === 'reviewer') {
  const kind = mode === 'planner' ? 'issue' : 'pr';
  const howTo = `gh ${kind} comment <n> --body-file <your comment file in the scratchpad, forward slashes>`;
  if (SHELL_META.test(cmd)) {
    block(`one plain command per call: no ; & | > < \` $( or newlines. Comments go as: ${howTo}`);
  }
  // `gh issue comment <n> --body-file <file>` (planner) or
  // `gh pr comment <n> --body-file <file>` (reviewer), exactly; nothing else.
  if (/^gh (issue|pr) comment( |$)/.test(cmd)) {
    const m = cmd.match(new RegExp(`^gh ${kind} comment \\d+ --body-file ([A-Za-z0-9._/:-]+)$`));
    if (m && isOwnCommentFile(mode, m[1])) process.exit(0);
    block(`comments go only as: ${howTo}`);
  }
  if (WRITE_FLAGS.test(cmd)) block('--output, --ext-diff and --web are not allowed');
  if (/^gh api/.test(cmd) && GH_API_WRITE.test(cmd)) block('gh api is GET only.');
  if (READ_ONLY.some((re) => re.test(cmd))) process.exit(0);
  block(
    'read-only agent. Allowed: git status/log/diff/show/rev-parse/ls-files/' +
      'merge-base/blame/branch (list only), gh issue view/list, gh pr view/list/' +
      `diff/checks, gh run list/view, gh label list, gh api (GET), and ${howTo}.`,
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

block('unknown mode; expected planner, reviewer, planner-files, reviewer-files, builder or builder-files.');
