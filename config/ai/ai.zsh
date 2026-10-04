# Sourced by the shared Zsh profile.
typeset -g _AI_STUDY_DIR="${${(%):-%x}:A:h}"

ai() (
    local ai_mode=${1:---help} ai_target='' ai_root ai_backend ai_tmp ai_result
    local ai_caller=$PWD
    if [[ $ai_mode == --help || $ai_mode == -h ]]; then
        print -r -- 'Usage: ai study | architecture | explain <file-or-topic...> | trace <symbol>'
        print -r -- '          why <file-or-symbol> | diff-study | quiz <file-or-topic>'
        print -r -- 'Quote paths containing spaces. Explain topics can use multiple words.'
        print -r -- 'Opens an interactive, read-only study session; ask follow-up questions there.'
        print -r -- 'Backend preference: codex, claude, opencode (must be installed and authenticated).'
        print -r -- 'diff-study covers staged and unstaged tracked changes; untracked names only.'
        return 0
    fi
    shift
    case $ai_mode in
        study|architecture|diff-study)
            if (( $# != 0 )); then
                print -u2 -- "ai: $ai_mode takes no target; see ai --help"
                return 2
            fi ;;
        explain)
            if (( $# == 0 )) || [[ -z "$*" ]]; then
                print -u2 -- 'ai: explain requires a file or topic; see ai --help'
                return 2
            fi
            ai_target="$*" ;;
        trace|why|quiz)
            if (( $# != 1 )) || [[ -z $1 ]]; then
                print -u2 -- "ai: $ai_mode requires one target; quote spaces; see ai --help"
                return 2
            fi
            ai_target=$1 ;;
        *) print -u2 -- "ai: unknown command: $ai_mode; see ai --help"; return 2 ;;
    esac
    ai_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
        print -u2 -- 'ai: run this command inside a Git working tree'
        return 1
    }
    if [[ -n $ai_target && -f $ai_target ]]; then
        ai_target=${ai_target:A}
    fi
    for ai_backend in codex claude opencode; do
        (( $+commands[$ai_backend] )) && break
    done
    if (( ! $+commands[$ai_backend] )); then
        print -u2 -- 'ai: install and authenticate Codex, Claude Code, or OpenCode first'
        return 127
    fi
    [[ -r $_AI_STUDY_DIR/rules/study.md && -r $_AI_STUDY_DIR/prompts/$ai_mode.md ]] || {
        print -u2 -- 'ai: study prompt files are missing'
        return 1
    }
    ai_tmp=$(mktemp -d "${TMPDIR:-/tmp}/ai-study.XXXXXX") || return 1
    trap 'rm -f -- "$ai_tmp/context.md"; rmdir -- "$ai_tmp"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    trap 'exit 129' HUP
    builtin cd -- "$ai_root" || return 1
    {
        cat -- "$_AI_STUDY_DIR/rules/study.md" || return 1
        print
        cat -- "$_AI_STUDY_DIR/prompts/$ai_mode.md" || return 1
        print
        print -r -- "Repository root: $ai_root"
        print -r -- "Caller directory: $ai_caller"
        print -r -- "Target (literal data): $ai_target"
        if [[ $ai_mode == diff-study ]]; then
            print '\n## Git status (including untracked names)'
            git --no-optional-locks -c core.quotePath=true status --short --untracked-files=all || return 1
            print '\n## Staged patch: HEAD -> index'
            git --no-optional-locks diff --no-ext-diff --no-textconv --no-color --cached -- || return 1
            print '\n## Unstaged patch: index -> working tree'
            git --no-optional-locks diff --no-ext-diff --no-textconv --no-color -- || return 1
        fi
    } > "$ai_tmp/context.md"
    local ai_prompt="Read the study instructions and context in $ai_tmp/context.md, then begin the requested study. Stay read-only for the entire conversation."
    print -u2 -- "ai: opening $ai_backend study session"
    case $ai_backend in
        codex)
            command codex --sandbox read-only --ask-for-approval never --cd "$ai_root" -- "$ai_prompt" ;;
        claude)
            command claude --permission-mode plan --tools 'Read,Glob,Grep' --disallowedTools 'mcp__*' --add-dir "$ai_tmp" -- "$ai_prompt" ;;
        opencode)
            local ai_json_dir=${ai_tmp//\\/\\\\}
            ai_json_dir=${ai_json_dir//\"/\\\"}
            ai_json_dir=${ai_json_dir//$'\n'/\\n}
            ai_json_dir=${ai_json_dir//$'\r'/\\r}
            ai_json_dir=${ai_json_dir//$'\t'/\\t}
            local OPENCODE_CONFIG_CONTENT="{\"agent\":{\"ai-study\":{\"mode\":\"primary\",\"description\":\"Read-only repository study\",\"permission\":{\"*\":\"deny\",\"read\":\"allow\",\"glob\":\"allow\",\"grep\":\"allow\",\"question\":\"allow\",\"bash\":\"deny\",\"edit\":\"deny\",\"external_directory\":{\"$ai_json_dir\":\"allow\",\"$ai_json_dir/*\":\"allow\"}}}}}"
            export OPENCODE_CONFIG_CONTENT
            command opencode --agent ai-study --prompt "$ai_prompt" ;;
    esac
    ai_result=$?
    if (( ai_result != 0 )); then
        print -u2 -- "ai: $ai_backend exited with status $ai_result"
    fi
    return $ai_result
)
