#!/bin/zsh
set -eu

local_repo=${0:A:h:h}
test_tmp=$(mktemp -d "${TMPDIR:-/tmp}/ai-tests.XXXXXX")
test_tmp=${test_tmp:A}
trap 'rm -rf -- "$test_tmp"' EXIT
git_bin=$(command -v git)
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
mkdir -p "$test_tmp/bin" "$test_tmp/repo/nested" "$test_tmp/study config"
cp -R "$local_repo/config/ai/" "$test_tmp/study config/"
source "$test_tmp/study config/ai.zsh"
export AI_TEST_RECORD="$test_tmp/record"
export AI_TEST_CONTEXT="$test_tmp/context"
export AI_TEST_EXIT=0

cat > "$test_tmp/fake" <<'FAKE'
#!/bin/zsh
print -r -- "${0:t}" > "$AI_TEST_RECORD"
print -r -- "$PWD" >> "$AI_TEST_RECORD"
printf '%s\n' "$@" >> "$AI_TEST_RECORD"
print -r -- "${OPENCODE_CONFIG_CONTENT:-}" > "$AI_TEST_RECORD.env"
prompt=${argv[-1]}
context=${prompt#Read the study instructions and context in }
context=${context%, then begin the requested study. Stay read-only for the entire conversation.}
print -r -- "$context" > "$AI_TEST_RECORD.path"
/bin/cp "$context" "$AI_TEST_CONTEXT"
exit "$AI_TEST_EXIT"
FAKE
chmod +x "$test_tmp/fake"
for tool in git mktemp cat rm rmdir ln chmod mkdir mv; do
    ln -s "$(command -v $tool)" "$test_tmp/bin/$tool"
done
for cli in codex claude opencode; do
    ln -s "$test_tmp/fake" "$test_tmp/bin/$cli"
done

"$git_bin" -C "$test_tmp/repo" init -q
print 'old behavior' > "$test_tmp/repo/file with spaces.txt"
"$git_bin" -C "$test_tmp/repo" add -- 'file with spaces.txt'
"$git_bin" -C "$test_tmp/repo" -c user.name=Test -c user.email=test@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -qm baseline
cd "$test_tmp/repo/nested"
export PATH="$test_tmp/bin"
passed=0
assert_contains() {
    [[ "$(< "$1")" == *"$2"* ]] || { print -u2 -- "FAIL: expected $2 in $1"; exit 1; }
}
expect_status() {
    local expected=$1 actual=0
    shift
    "$@" > "$test_tmp/output" 2> "$test_tmp/error" || actual=$?
    [[ $actual == $expected ]] || { print -u2 -- "FAIL: $*: expected $expected, got $actual"; exit 1; }
    (( ++passed ))
}
expect_status 0 ai --help
expect_status 0 ai
for mode in study architecture; do
    expect_status 0 ai "$mode"
    assert_contains "$AI_TEST_CONTEXT" "$(< "$_AI_STUDY_DIR/prompts/$mode.md")"
    assert_contains "$AI_TEST_CONTEXT" 'Do not modify code'
    assert_contains "$AI_TEST_CONTEXT" 'ASD-STE100'
done
for mode in explain why quiz; do
    expect_status 0 ai "$mode" '../file with spaces.txt'
    assert_contains "$AI_TEST_CONTEXT" "Target (literal data): $test_tmp/repo/file with spaces.txt"
done
expect_status 0 ai explain event loop
assert_contains "$AI_TEST_CONTEXT" 'Target (literal data): event loop'
assert_contains "$AI_TEST_CONTEXT" 'follow-up questions'
expect_status 0 ai trace 'run$(touch injected); --flag'
assert_contains "$AI_TEST_CONTEXT" 'Target (literal data): run$(touch injected); --flag'
[[ ! -e injected && $PWD == "$test_tmp/repo/nested" ]]
assert_contains "$AI_TEST_RECORD" '--sandbox'
assert_contains "$AI_TEST_RECORD" 'read-only'
assert_contains "$AI_TEST_RECORD" 'never'
[[ "$(< "$AI_TEST_RECORD")" == codex$'\n'* ]]
[[ ! -e "$(< "$AI_TEST_RECORD.path")" ]]

expect_status 2 ai missing
expect_status 2 ai study extra
expect_status 2 ai explain
expect_status 2 ai trace one two
expect_status 2 ai quiz ''
expect_status 0 ai explain nonexistent
assert_contains "$AI_TEST_CONTEXT" 'Target (literal data): nonexistent'

expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" '## Staged patch: HEAD -> index'
[[ "$(< "$AI_TEST_CONTEXT")" != *'diff --git'* ]]
print 'staged behavior' > '../file with spaces.txt'
"$git_bin" add -- '../file with spaces.txt'
expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" '+staged behavior'
print 'working behavior' > '../file with spaces.txt'
print 'untracked contents must not be read' > ../untracked.txt
before=$("$git_bin" status --porcelain; "$git_bin" diff; "$git_bin" diff --cached)
expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" '+staged behavior'
assert_contains "$AI_TEST_CONTEXT" '+working behavior'
assert_contains "$AI_TEST_CONTEXT" '?? untracked.txt'
[[ "$(< "$AI_TEST_CONTEXT")" != *'untracked contents must not be read'* ]]
after=$("$git_bin" status --porcelain; "$git_bin" diff; "$git_bin" diff --cached)
[[ $before == $after ]]
"$git_bin" restore --staged -- '../file with spaces.txt'
expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" '+working behavior'

export AI_TEST_EXIT=23
expect_status 23 ai study
assert_contains "$test_tmp/error" 'codex exited with status 23'
[[ ! -e "$(< "$AI_TEST_RECORD.path")" && $PWD == "$test_tmp/repo/nested" ]]
export AI_TEST_EXIT=0
rm "$test_tmp/bin/codex"
rehash
expect_status 0 ai architecture
[[ "$(< "$AI_TEST_RECORD")" == claude$'\n'* ]]
assert_contains "$AI_TEST_RECORD" 'Read,Glob,Grep'
assert_contains "$AI_TEST_RECORD" 'mcp__*'
rm "$test_tmp/bin/claude"
rehash
export OPENCODE_CONFIG_CONTENT='original config'
expect_status 0 ai study
[[ "$(< "$AI_TEST_RECORD")" == opencode$'\n'* ]]
assert_contains "$AI_TEST_RECORD.env" '"bash":"deny"'
assert_contains "$AI_TEST_RECORD.env" '"edit":"deny"'
[[ $OPENCODE_CONFIG_CONTENT == 'original config' ]]
rm "$test_tmp/bin/opencode"
rehash
expect_status 127 ai study
cd "$test_tmp"
expect_status 0 ai --help
expect_status 1 ai study

/bin/ln -s "$test_tmp/fake" "$test_tmp/bin/codex"
rehash
mkdir_cmd=/bin/mkdir
"$mkdir_cmd" "$test_tmp/new-repo"
"$git_bin" -C "$test_tmp/new-repo" init -q
cd "$test_tmp/new-repo"
print 'first file' > first.txt
"$git_bin" add -- first.txt
expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" '+first file'

# Binary patches are represented by Git's marker, not decoded as source.
printf '\0binary data' > binary.dat
"$git_bin" add -- binary.dat
expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" 'Binary files'

# A large diff stays in a file rather than becoming a CLI argument.
for (( line=0; line<12000; line++ )); do
    print -r -- "large diff line $line"
done > large.txt
"$git_bin" add -- large.txt
expect_status 0 ai diff-study
assert_contains "$AI_TEST_CONTEXT" '+large diff line 11999'
(( ${#$(< "$AI_TEST_RECORD")} < 4096 ))

# Git failures must not launch a session or leave context behind.
cat > "$test_tmp/bin/git-fail" <<FAKE
#!/bin/zsh
if [[ \$* == *diff* ]]; then exit 19; fi
exec "$git_bin" "\$@"
FAKE
chmod +x "$test_tmp/bin/git-fail"
rm "$test_tmp/bin/git"
ln -s "$test_tmp/bin/git-fail" "$test_tmp/bin/git"
before_record=$(< "$AI_TEST_RECORD")
expect_status 1 ai diff-study
[[ "$(< "$AI_TEST_RECORD")" == $before_record ]]
rm "$test_tmp/bin/git"
ln -s "$git_bin" "$test_tmp/bin/git"

# Load the real profile with an isolated home and no real AI CLI on PATH.
mkdir "$test_tmp/home"
expect_status 0 /usr/bin/env HOME="$test_tmp/home" TERM=xterm /bin/zsh -f -c 'source "$1"; ai --help' -- "$local_repo/config/zsh/zshrc"
assert_contains "$test_tmp/output" 'Usage: ai'
if [[ -s "$test_tmp/error" ]]; then
    print -u2 -- 'FAIL: profile wrote to stderr'
    /bin/cat -- "$test_tmp/error" >&2
    exit 1
fi

print -- "PASS: $passed command cases; routing, arguments, diff snapshots, read-only flags, cleanup, and state preservation"
