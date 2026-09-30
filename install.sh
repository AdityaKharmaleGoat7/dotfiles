#!/bin/sh

set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
zshrc_path="$HOME/.zshrc"
start_marker="# >>> dotfiles repository >>>"
end_marker="# <<< dotfiles repository <<<"
git_config="$repo_dir/git/config"
starship_source="$repo_dir/starship/starship.toml"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
starship_target="$config_home/starship.toml"
starship_backup="$config_home/starship.toml.pre-dotfiles"

install_starship() {
    mkdir -p "$config_home"

    if [ -L "$starship_target" ] && [ "$(readlink "$starship_target")" = "$starship_source" ]; then
        printf 'Starship configuration is already installed.\n'
        return
    fi

    if [ -e "$starship_backup" ] || [ -L "$starship_backup" ]; then
        printf 'Cannot install Starship configuration: backup already exists at %s\n' "$starship_backup" >&2
        exit 1
    fi

    if [ -e "$starship_target" ] || [ -L "$starship_target" ]; then
        mv "$starship_target" "$starship_backup"
        printf 'Backed up existing Starship configuration to %s\n' "$starship_backup"
    fi

    ln -s "$starship_source" "$starship_target"
    printf 'Linked Starship configuration at %s\n' "$starship_target"
}

uninstall_starship() {
    if [ -L "$starship_target" ] && [ "$(readlink "$starship_target")" = "$starship_source" ]; then
        unlink "$starship_target"
        printf 'Removed Starship configuration link at %s\n' "$starship_target"

        if [ -e "$starship_backup" ] || [ -L "$starship_backup" ]; then
            mv "$starship_backup" "$starship_target"
            printf 'Restored previous Starship configuration.\n'
        fi
    else
        printf 'No managed Starship configuration link found.\n'
    fi
}

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

    install_starship
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

    uninstall_starship
}

case "${1:-}" in
    "") install_dotfiles ;;
    --uninstall) uninstall_dotfiles ;;
    *)
        printf 'Usage: %s [--uninstall]\n' "$0" >&2
        exit 2
        ;;
esac
