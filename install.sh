#!/bin/sh

set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
zshrc_path="$HOME/.zshrc"
start_marker="# >>> dotfiles repository >>>"
end_marker="# <<< dotfiles repository <<<"
git_config="$repo_dir/git/config"

install_dotfiles() {
    touch "$zshrc_path"

    if ! grep -Fq "$start_marker" "$zshrc_path"; then
        {
            printf '\n%s\n' "$start_marker"
            printf '[ -r "%s/zsh/zshrc" ] && source "%s/zsh/zshrc"\n' "$repo_dir" "$repo_dir"
            printf '%s\n' "$end_marker"
        } >> "$zshrc_path"
        printf 'Added dotfiles loader to %s\n' "$zshrc_path"
    else
        printf 'Shell configuration is already installed.\n'
    fi

    if git config --global --get-all include.path 2>/dev/null | grep -Fxq "$git_config"; then
        printf 'Git configuration is already installed.\n'
    else
        git config --global --add include.path "$git_config"
        printf 'Added Git include for %s\n' "$git_config"
    fi
}

uninstall_dotfiles() {
    if [ -f "$zshrc_path" ] && grep -Fq "$start_marker" "$zshrc_path"; then
        temp_file=$(mktemp "${TMPDIR:-/tmp}/dotfiles-zshrc.XXXXXX")
        awk -v start="$start_marker" -v end="$end_marker" '
            $0 == start { skipping = 1; next }
            $0 == end { skipping = 0; next }
            !skipping { print }
        ' "$zshrc_path" > "$temp_file"
        mv "$temp_file" "$zshrc_path"
        printf 'Removed dotfiles loader from %s\n' "$zshrc_path"
    else
        printf 'No dotfiles loader found in %s.\n' "$zshrc_path"
    fi

    git config --global --fixed-value --unset-all include.path "$git_config" 2>/dev/null || true
    printf 'Removed Git include for %s, if it was present.\n' "$git_config"
}

case "${1:-}" in
    "") install_dotfiles ;;
    --uninstall) uninstall_dotfiles ;;
    *)
        printf 'Usage: %s [--uninstall]\n' "$0" >&2
        exit 2
        ;;
esac
