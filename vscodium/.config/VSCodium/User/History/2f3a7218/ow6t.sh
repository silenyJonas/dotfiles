#!/usr/bin/env bash
# =============================================================================
# @file init-workspace.sh
# @path init-workspace.sh (root of the web-platform monorepo)
# @project RPSW Web
# @author RPSW
# @created 2026
# @description Prepares a freshly cloned application for LOCAL development on
# Fedora. It is universal – the same unchanged script works for web-platform and
# for every application cloned from it (the app name is taken from the directory):
#
#   git clone git@github.com:jonclsolutions/web-platform.git my-app
#   cd my-app && ./init-workspace.sh
#
# (No SSH key on GitHub yet? Clone over HTTPS - https://github.com/jonclsolutions/web-platform.git -
#  and let step 1 connect this computer over SSH; it then offers to switch the remote to SSH.)
#
# PREREQUISITE (checked right after step 1 – the script stops without it):
#   XAMPP installed in /opt/lampp – https://www.apachefriends.org/download.html
#
# Steps (each one is skipped when already done – safe to run again, nothing
# existing is overwritten):
#   1. GitHub (SSH)    – checks the SSH connection to GitHub; when missing it offers to connect
#                        (SSH key, adding it on GitHub, check) – may be skipped
#   2. Temp folder     – .temp/ with temp.txt: local scratch space (media, notes, …), git-ignored
#   3. System packages – PHP + extensions (incl. pcov for test coverage), Composer, Node.js, tools
#                        (Fedora: dnf, Arch Linux: pacman)
#   4. Mailpit         – local SMTP catcher, verified release → ~/.local/bin
#   5. Laravel         – api/.env, composer install, APP_KEY, storage symlink, permissions
#   6. Database        – creates the database (XAMPP MariaDB), runs the migrations and the seeders:
#                        base data + the local test account sysadmin@sysadmin.sysadmin / 123456Ab.
#   7. Angular         – npm ci, local SSL certificate for `ng serve`
#   8. Repository      – .gitignore entries, executable scripts, git remote check
#   9. Shell aliases   – <app>, <app>-dev, <app>-build in your shell profile
#  10. Summary         – result + the manual step: review api/.env
#
# @refactor-note (2026-10-24) Open finding #54: the dev certificate of `ng serve` was a committed
#   Laragon key pair (`erp/ssl/laragon.*`). Laragon is no longer used (XAMPP); the pair is now
#   generated per developer as `erp/ssl/localhost.{crt,key}` and the whole `erp/ssl/` is git-ignored.
# @refactor-note (2026-10-30) Arch Linux support (step 1): packages via pacman, the PHP extensions
#   Arch ships disabled are enabled in /etc/php/conf.d/20-laravel-dev.ini, pcov (AUR only) is
#   reported, not installed. Step 3 stops with a clear message when Composer / PHP is missing
#   (before: "composer: command not found" from the ERR trap).
# @refactor-note (2026-10-30d) New step 4 "Database" replaces the manual phpMyAdmin import of
#   database/db.sql; step 6 creates the git-ignored .temp/ folder for local scratch files.
# @bugfix-note (2026-10-30) This file was stored without the executable bit (mode 100644): after a
#   clone / checkout `./init-workspace.sh` could not be started and git showed a mode change once
#   the script had made itself executable. Stored as 100755 now; a trailing space removed.
# @bugfix-note (2026-10-30b) Fresh Arch Linux (e.g. a VM): stops with instructions when sudo is
#   missing (not in a base installation) or the pacman database was never synced; installs
#   net-tools (netstat, used by XAMPP's lampp script).
# @bugfix-note (2026-10-30c) Used Arch Linux: installed packages are checked with `pacman -T`
#   (honours "provides") instead of `pacman -Q` (exact name) - with e.g. nodejs-lts-jod the script
#   tried to install nodejs, which conflicts and stopped the step.
# @refactor-note (2026-10-31) Summary lists the new test role set (full-web-core, full-shop-core,
#   all-permissions instead of editor-web, editor-shop, manager).
# @refactor-note (2026-10-31b) New first step "GitHub (SSH)" (check, optional connection, optional
#   switch of an HTTPS remote to SSH); the XAMPP prerequisite is checked right after it; the
#   .temp/ folder is created as step 2 (right after the clone, before the long installs) and its
#   description file is now .temp/temp.txt (an older .temp/info.txt is left as it is). Steps
#   renumbered (10 in total). Step numbers in the notes above refer to the old numbering.
# @note THE DATABASE IS CREATED BY THIS SCRIPT (step 6, since 2026-10-30): `db:create-if-missing`,
# `migrate`, `db:seed` - an existing database is never dropped or overwritten, only missing
# migrations and missing base data are added. Only one application runs at a time (all use
# ports 8000/4200).
#
# @note ISOLATION: everything the script writes belongs to this checkout
# (api/.env, vendor/, node_modules/, erp/ssl/, .dev/) or is a block named after
# the app (shell aliases), so any number of cloned apps can be set up on one
# machine without affecting each other. The user crontab is never touched.
#
# @security
#   - GitHub SSH: github.com is trusted only with the host key GitHub publishes (pinned below, no
#     "trust on first use"); a new key pair is created only after asking, with ssh-keygen (it asks
#     for a passphrase); only the PUBLIC key is ever printed / copied, the private key never leaves
#     ~/.ssh. An existing key, ~/.ssh/config or known_hosts entry is never changed.
#   - Never overwrites an existing api/.env and never regenerates an existing APP_KEY.
#   - Mailpit is installed only if its SHA-256 matches the digest GitHub publishes.
#   - Does not run as root; sudo is used only for the package manager (dnf / pacman) and, on
#     Arch Linux, to enable the required PHP extensions (/etc/php/conf.d/20-laravel-dev.ini).
#   - Never installs from the AUR (user-submitted, unreviewed) – it only tells what is missing.
#   - The generated SSL key is for localhost only and is git-ignored.
#
# @usage
#   ./init-workspace.sh                full setup
#   ./init-workspace.sh --skip-system  skip the system packages (dnf / pacman)
#   ./init-workspace.sh --no-aliases   do not touch the shell profile
#   ./init-workspace.sh --help
# =============================================================================

set -Eeuo pipefail

# -----------------------------------------------------------------------------
# Paths and settings
# -----------------------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$ROOT_DIR/api"
ERP_DIR="$ROOT_DIR/erp"
DEV_DIR="$ROOT_DIR/.dev"
XAMPP_DIR="${XAMPP_DIR:-/opt/lampp}"
LOCAL_BIN="$HOME/.local/bin"

# Application name = directory name (lower-case, [a-z0-9-]); used for aliases
# and as the suggested database name of a new app.
APP_SLUG="$(basename "$ROOT_DIR" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
APP_SLUG="${APP_SLUG:-app}"

# Angular `ng serve` uses these (erp/angular.json → serve.options.sslKey/sslCert).
SSL_DIR="$ERP_DIR/ssl"
SSL_CERT="$SSL_DIR/localhost.crt"   # per developer, git-ignored (finding #54)
SSL_KEY="$SSL_DIR/localhost.key"

# GitHub over SSH. Host key of github.com as published by GitHub
# (https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints,
# Ed25519 SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU) - added to ~/.ssh/known_hosts only
# when github.com is not there yet, so the first connection needs no "trust on first use".
GITHUB_SSH="git@github.com"
GITHUB_HOST_KEY="github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
GITHUB_KEYS_URL="https://github.com/settings/ssh/new"

SKIP_SYSTEM=0
WITH_ALIASES=1
ENV_CREATED=0      # 1 = api/.env was created by this run (summary asks to review it)

# -----------------------------------------------------------------------------
# Output helpers and result tracking (printed in the summary)
# -----------------------------------------------------------------------------
STEP=0
TOTAL_STEPS=10
DONE=()
SKIPPED=()
WARNINGS=()

step() { STEP=$((STEP + 1)); printf '\n\e[34m[%d/%d]\e[0m %s\n' "$STEP" "$TOTAL_STEPS" "$*"; }
info() { printf '   - %s\n' "$*"; }
done_() { printf '\e[32m   ✓ %s\e[0m\n' "$*"; DONE+=("$*"); }
skip() { printf '   · %s\n' "$*"; SKIPPED+=("$*"); }
warn() { printf '\e[33m   ! %s\e[0m\n' "$*" >&2; WARNINGS+=("$*"); }
die()  { printf '\e[31mERROR: %s\e[0m\n' "$*" >&2; exit 1; }

trap '[[ $BASH_SUBSHELL -eq 0 ]] && die "setup failed at line $LINENO (command: $BASH_COMMAND)"; exit 1' ERR

for arg in "$@"; do
    case "$arg" in
        --skip-system) SKIP_SYSTEM=1 ;;
        --no-aliases)  WITH_ALIASES=0 ;;
        -h|--help) sed -n '/^# @usage/,/^# =====/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' | sed '$d'; exit 0 ;;
        *) die "unknown option: $arg (see --help)" ;;
    esac
done

# -----------------------------------------------------------------------------
# @description Reads one value from api/.env with the same semantics as Laravel:
# vlucas/phpdotenv when vendor/ exists, a simple parser otherwise.
# @param $1 key
# -----------------------------------------------------------------------------
env_get() {
    local key="$1"
    if [[ -f "$API_DIR/vendor/vlucas/phpdotenv/src/Dotenv.php" ]]; then
        (cd "$API_DIR" && php -r '
            require "vendor/autoload.php";
            $env = Dotenv\Dotenv::parse(file_get_contents(".env"));
            echo $env[$argv[1]] ?? "";' "$key")
        return
    fi
    local v
    v="$(grep -E "^[[:space:]]*$key=" "$API_DIR/.env" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
    if [[ "$v" == \"* ]]; then
        v="${v#\"}"; v="${v%\"*}"; v="${v//\\\"/\"}"; v="${v//\\\\/\\}"
    elif [[ "$v" == \'* ]]; then
        v="${v#\'}"; v="${v%\'*}"
    else
        v="${v%%[[:space:]]#*}"
    fi
    printf '%s' "$v"
}

# -----------------------------------------------------------------------------
# @description Sets KEY=VALUE in api/.env (replaces the line or appends).
# Used only on a freshly created .env, never on an existing one.
# @param $1 key, $2 value
# -----------------------------------------------------------------------------
env_set() {
    local key="$1" value="$2" file="$API_DIR/.env" tmp
    tmp="$(mktemp)"
    if grep -qE "^[[:space:]]*#?[[:space:]]*$key=" "$file"; then
        awk -v k="$key" -v v="$value" '
            !done && $0 ~ "^[[:space:]]*#?[[:space:]]*" k "=" { print k "=" v; done = 1; next }
            { print }' "$file" > "$tmp"
    else
        cat "$file" > "$tmp"
        printf '%s=%s\n' "$key" "$value" >> "$tmp"
    fi
    cat "$tmp" > "$file"
    rm -f "$tmp"
}

# -----------------------------------------------------------------------------
# @description Basic checks before anything is changed: not root, sudo available, run from the
# repository root.
# -----------------------------------------------------------------------------
preflight() {
    [[ "$EUID" -ne 0 ]] || die "do not run as root – the script uses sudo only for the package manager"
    # A minimal installation (e.g. Arch Linux base) has no sudo.
    command -v sudo >/dev/null \
        || die "sudo not found – install it as root (Arch: pacman -S sudo, then add your user to the wheel group: usermod -aG wheel <user>, and allow the group with EDITOR=nano visudo), then run this script again"
    [[ -f "$API_DIR/composer.json" ]] || die "api/composer.json not found – run from the repository root"
    [[ -f "$ERP_DIR/package.json" ]]  || die "erp/package.json not found – run from the repository root"
    mkdir -p "$DEV_DIR"
}

# -----------------------------------------------------------------------------
# @description Prerequisite XAMPP (checked right after step 1). XAMPP is installed once per
# machine by hand, so its absence stops the script before anything is installed.
# -----------------------------------------------------------------------------
require_xampp() {
    printf '\nPREREQUISITE: XAMPP must be installed in %s before running this script.\n' "$XAMPP_DIR"
    printf '  Download: https://www.apachefriends.org/download.html\n'
    printf '  Install:  chmod +x xampp-linux-*-installer.run && sudo ./xampp-linux-*-installer.run\n\n'
    [[ -x "$XAMPP_DIR/lampp" ]] \
        || die "XAMPP not found in $XAMPP_DIR – install it first (see above), then run this script again"
    printf '\e[32m   ✓ XAMPP found in %s\e[0m\n' "$XAMPP_DIR"
}

# -----------------------------------------------------------------------------
# 1. GitHub (SSH) – checks that this computer can reach GitHub over SSH. When it cannot (and a
#    terminal is attached) it offers to connect: uses the existing default key or creates one
#    with ssh-keygen, shows the PUBLIC key with the GitHub page to add it, and checks again until
#    it works or the user skips. Skipping never stops the script (GitHub is needed only to push /
#    pull, not to run the app).
# -----------------------------------------------------------------------------
setup_github_ssh() {
    step "GitHub (SSH)"
    if ! command -v ssh >/dev/null || ! command -v ssh-keygen >/dev/null; then
        skip "ssh not installed – GitHub SSH check skipped (Fedora: sudo dnf install openssh-clients, Arch: sudo pacman -S openssh)"
        return 0
    fi
    pin_github_host_key

    local user
    if user="$(github_ssh_user batch)"; then
        done_ "connected to GitHub over SSH as $user"
        offer_ssh_remote
        return 0
    fi
    if [[ ! -t 0 ]]; then
        skip "not connected to GitHub over SSH (no terminal to ask) – run the script in a terminal to connect"
        return 0
    fi

    local answer
    printf '   This computer is not connected to GitHub over SSH (needed to push / pull with git@github.com).\n'
    read -r -p "   Connect now? [y/N] " answer || answer=""
    if [[ ! "$answer" =~ ^[YyAa]$ ]]; then
        skip "GitHub SSH connection skipped – run the script again to connect later"
        return 0
    fi

    local pub
    pub="$(github_public_key)" || { warn "no SSH key created – GitHub SSH connection skipped"; return 0; }

    printf '\n   Add this PUBLIC key on GitHub (Settings → SSH and GPG keys → New SSH key):\n'
    printf '     %s\n' "$GITHUB_KEYS_URL"
    printf '     Title: %s, Key type: Authentication Key, Key:\n\n' "$(uname -n)"
    printf '%s\n\n' "$(cat "$pub")"
    if copy_to_clipboard < "$pub"; then info "the public key is also in the clipboard"; fi

    while true; do
        read -r -p "   Press Enter once the key is added on GitHub (s = skip): " answer || answer="s"
        if [[ "$answer" =~ ^[Ss]$ ]]; then
            skip "GitHub SSH connection skipped – the key ${pub/#$HOME/\~} stays, add it on GitHub later"
            return 0
        fi
        if user="$(github_ssh_user)"; then
            done_ "connected to GitHub over SSH as $user"
            offer_ssh_remote
            return 0
        fi
        printf '\e[33m   ! GitHub does not accept the key yet – check that the whole line above was pasted, then try again\e[0m\n'
    done
}

# @description Adds GitHub's published Ed25519 host key to ~/.ssh/known_hosts when github.com is
# not known yet (an existing entry is never changed).
pin_github_host_key() {
    local kh="$HOME/.ssh/known_hosts"
    if [[ -f "$kh" ]] && ssh-keygen -F github.com -f "$kh" >/dev/null 2>&1; then return 0; fi
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    printf '%s\n' "$GITHUB_HOST_KEY" >> "$kh"
    chmod 600 "$kh"
    info "GitHub host key (published by GitHub) added to ~/.ssh/known_hosts"
}

# @description Prints the GitHub user name when `ssh -T git@github.com` authenticates.
# @param $1 'batch' = never ask anything (no passphrase prompt) - for the silent first check.
# @return 0 connected (user name printed), 1 not connected.
github_ssh_user() {
    local opts=(-T -o ConnectTimeout=15 -o StrictHostKeyChecking=yes) out
    [[ "${1:-}" == "batch" ]] && opts+=(-o BatchMode=yes)
    # GitHub answers "Hi <user>! You've successfully authenticated…" and exits with 1 (no shell).
    out="$(ssh "${opts[@]}" "$GITHUB_SSH" 2>&1 </dev/null)" || true
    [[ "$out" =~ Hi\ ([^!]+)!\ You\'ve\ successfully\ authenticated ]] || return 1
    printf '%s' "${BASH_REMATCH[1]}"
}

# @description Path of the public key to add on GitHub: the first default key that exists
# (id_ed25519, id_ecdsa, id_rsa), else a new Ed25519 pair created by ssh-keygen (it asks for a
# passphrase - recommended). Only the .pub path is printed.
# @return 0 path printed, 1 no key (ssh-keygen cancelled / failed).
github_public_key() {
    local k
    for k in id_ed25519 id_ecdsa id_rsa; do
        if [[ -f "$HOME/.ssh/$k" && -f "$HOME/.ssh/$k.pub" ]]; then
            info "using the existing key ~/.ssh/$k" >&2
            printf '%s' "$HOME/.ssh/$k.pub"
            return 0
        fi
    done
    local comment
    comment="$(git config --get user.email 2>/dev/null || true)"
    comment="${comment:-$USER@$(uname -n)}"
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    info "creating a new SSH key ~/.ssh/id_ed25519 ($comment) – choose a passphrase (recommended)" >&2
    ssh-keygen -t ed25519 -C "$comment" -f "$HOME/.ssh/id_ed25519" </dev/tty >&2 || return 1
    printf '%s' "$HOME/.ssh/id_ed25519.pub"
}

# @description Copies stdin to the clipboard when a clipboard tool exists (Wayland / X11).
copy_to_clipboard() {
    if command -v wl-copy >/dev/null && [[ -n "${WAYLAND_DISPLAY:-}" ]]; then wl-copy 2>/dev/null; return; fi
    if command -v xclip >/dev/null && [[ -n "${DISPLAY:-}" ]]; then xclip -selection clipboard 2>/dev/null; return; fi
    return 1
}

# @description When `origin` is a GitHub HTTPS URL, offers to switch it to SSH (asked, never
# automatic) - with a working SSH key git then needs no password / token.
offer_ssh_remote() {
    local origin ssh_url answer
    origin="$(git -C "$ROOT_DIR" remote get-url origin 2>/dev/null || true)"
    [[ "$origin" =~ ^https://github\.com/([^/]+/[^/]+)$ ]] || return 0
    ssh_url="$GITHUB_SSH:${BASH_REMATCH[1]%.git}.git"
    [[ -t 0 ]] || { info "origin uses HTTPS – switch to SSH with: git remote set-url origin $ssh_url"; return 0; }
    read -r -p "   origin uses HTTPS ($origin). Switch it to SSH ($ssh_url)? [y/N] " answer || answer=""
    if [[ "$answer" =~ ^[YyAa]$ ]]; then
        git -C "$ROOT_DIR" remote set-url origin "$ssh_url"
        done_ "origin switched to $ssh_url"
    else
        skip "origin left on HTTPS"
    fi
}

# -----------------------------------------------------------------------------
# 3. System packages – only missing packages are installed.
#    Fedora: dnf. Arch Linux: pacman (+ PHP extensions enabled in conf.d).
# -----------------------------------------------------------------------------
install_system_packages() {
    step "System packages"
    if [[ "$SKIP_SYSTEM" == "1" ]]; then skip "system packages (--skip-system)"; return 0; fi
    if command -v dnf >/dev/null; then
        install_packages_fedora
    elif command -v pacman >/dev/null; then
        install_packages_arch
    else
        warn "neither dnf (Fedora) nor pacman (Arch Linux) found – install PHP 8.2+ with the extensions of api/composer.lock, Composer, Node.js, zip, rsync, openssl manually"
        return 0
    fi
    check_tool_versions
}

# -----------------------------------------------------------------------------
# Fedora / dnf.
# @note php-process = pcntl/posix (queue workers), php-mysqlnd = pdo_mysql,
# libxcrypt-compat = libcrypt.so.1 needed by XAMPP on current Fedora.
# Unit tests (tests/unit_tests/api): php-pdo = pdo_sqlite (the tests run on SQLite
# in memory), php-pecl-pcov = code coverage driver (without it the tests still run,
# only the coverage is missing).
# -----------------------------------------------------------------------------
install_packages_fedora() {
    local wanted=(
        php-cli php-common php-mbstring php-xml php-mysqlnd php-intl php-pecl-zip
        php-gd php-bcmath php-process php-opcache php-sodium
        php-pdo php-pecl-pcov
        composer nodejs npm
        git unzip zip rsync openssl curl tar libxcrypt-compat
    )
    local missing=() p
    for p in "${wanted[@]}"; do
        rpm -q --whatprovides "$p" >/dev/null 2>&1 || missing+=("$p")
    done
    if [[ ${#missing[@]} -eq 0 ]]; then
        skip "all system packages already installed"
    else
        info "installing: ${missing[*]} (sudo)"
        sudo dnf install -y "${missing[@]}"
        done_ "installed: ${missing[*]}"
    fi
}

# -----------------------------------------------------------------------------
# Arch Linux / pacman.
# @note The `php` package contains mbstring, xml, curl, openssl, pcntl, posix, … built in, but
# ships bcmath, iconv, intl, mysqli, pdo_mysql and zip DISABLED; gd, sodium and sqlite
# (pdo_sqlite + sqlite3, needed by the unit tests) are separate packages, also disabled after
# installation. A package name the repositories do not know (renamed / merged) is reported, not
# installed, so one rename cannot stop the whole step. The script enables exactly the missing ones in ONE file of its own,
# /etc/php/conf.d/20-laravel-dev.ini (php.ini itself is never edited; delete the file to undo).
# libxcrypt-compat = libcrypt.so.1 and net-tools = netstat, both needed by XAMPP (its `lampp`
# script checks the ports with netstat; a base Arch has neither). No `-Sy`: a sync without upgrade is a partial
# upgrade, which Arch does not support - when packages cannot be found, run `sudo pacman -Syu`.
# pcov (coverage driver of the unit tests) exists only in the AUR, which this script never uses.
# -----------------------------------------------------------------------------
install_packages_arch() {
    local wanted=(
        php php-gd php-sodium php-sqlite
        composer nodejs npm
        git unzip zip rsync openssl curl tar libxcrypt-compat net-tools
    )
    local missing=() unknown=() p
    for p in "${wanted[@]}"; do
        # -T (deptest) also accepts a package that PROVIDES the name (nodejs-lts-* → nodejs, …),
        # so an existing alternative is kept instead of being replaced (= conflict, abort).
        pacman -T "$p" >/dev/null 2>&1 && continue
        if pacman -Si "$p" >/dev/null 2>&1; then missing+=("$p"); else unknown+=("$p"); fi
    done
    # `php` unknown = the package database was never synced (fresh installation) - nothing would work.
    [[ " ${unknown[*]} " != *" php "* ]] \
        || die "pacman does not know the package 'php' – the package database is not synced: run sudo pacman -Syu, then this script again"
    [[ ${#unknown[@]} -eq 0 ]] \
        || warn "not found in the pacman repositories: ${unknown[*]} – update the package database (sudo pacman -Syu) or install them yourself"
    if [[ ${#missing[@]} -eq 0 ]]; then
        skip "all system packages already installed"
    else
        info "installing: ${missing[*]} (sudo pacman)"
        sudo pacman -S --needed --noconfirm "${missing[@]}" \
            || die "pacman could not install the packages – update the system first (sudo pacman -Syu), then run this script again"
        done_ "installed: ${missing[*]}"
    fi

    enable_php_extensions_arch

    if php -m 2>/dev/null | grep -qix pcov; then
        skip "pcov (test coverage) already available"
    else
        # Optional - not a warning (the setup is complete without it).
        skip "pcov not installed (AUR only): the unit tests run, only their coverage is missing – for coverage install it yourself, e.g. 'yay -S php-pcov' (review the PKGBUILD first)"
    fi
}

# -----------------------------------------------------------------------------
# @description Enables the PHP extensions Laravel / the tests need and Arch ships disabled.
# Only extensions php -m does not list yet are written; an existing file of this script is
# extended, never replaced.
# -----------------------------------------------------------------------------
enable_php_extensions_arch() {
    local wanted=(bcmath gd iconv intl mysqli pdo_mysql pdo_sqlite sodium sqlite3 zip)
    local scan_dir ini loaded missing=() e
    scan_dir="$(php -r 'echo PHP_CONFIG_FILE_SCAN_DIR;' 2>/dev/null || true)"
    [[ -n "$scan_dir" ]] || scan_dir=/etc/php/conf.d
    ini="$scan_dir/20-laravel-dev.ini"
    loaded="$(php -m 2>/dev/null | tr '[:upper:]' '[:lower:]')"
    for e in "${wanted[@]}"; do
        grep -qx "$e" <<<"$loaded" || missing+=("$e")
    done
    if [[ ${#missing[@]} -eq 0 ]]; then
        skip "PHP extensions already enabled"
        return 0
    fi

    info "enabling PHP extensions in $ini: ${missing[*]} (sudo)"
    sudo mkdir -p "$scan_dir"
    if [[ ! -f "$ini" ]]; then
        printf '; Written by init-workspace.sh (Laravel development) - extensions Arch ships disabled.\n; Delete this file to undo.\n' \
            | sudo tee "$ini" >/dev/null
    fi
    for e in "${missing[@]}"; do
        printf 'extension=%s\n' "$e" | sudo tee -a "$ini" >/dev/null
    done

    loaded="$(php -m 2>/dev/null | tr '[:upper:]' '[:lower:]')"
    local still=()
    for e in "${missing[@]}"; do grep -qx "$e" <<<"$loaded" || still+=("$e"); done
    if [[ ${#still[@]} -eq 0 ]]; then
        done_ "PHP extensions enabled: ${missing[*]}"
    else
        warn "PHP extensions still not loaded: ${still[*]} – check $ini and 'php -m'"
    fi
}

# -----------------------------------------------------------------------------
# @description Prints / checks the versions of PHP, Composer and Node.js.
# -----------------------------------------------------------------------------
check_tool_versions() {
    # Angular 21 requires Node.js ^20.19 || ^22.12 || >=24.
    local node_major
    node_major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    if (( node_major < 20 )); then
        warn "Node.js $(node -v 2>/dev/null || echo 'missing') is too old for Angular 21 (need 20.19+, 22.12+ or 24+)"
    else
        info "PHP $(php -r 'echo PHP_VERSION;'), Composer $(composer --version 2>/dev/null | awk '{print $3}'), Node.js $(node -v)"
    fi
}

# -----------------------------------------------------------------------------
# 4. Mailpit – latest GitHub release, installed only after checksum verification.
# Mailpit ships no checksums file; GitHub publishes a SHA-256 `digest` for every
# release asset in its REST API – that is what is verified. Nothing unverified runs.
# -----------------------------------------------------------------------------
install_mailpit() {
    step "Mailpit"
    if command -v mailpit >/dev/null || [[ -x "$LOCAL_BIN/mailpit" ]]; then
        skip "Mailpit already installed"
        return 0
    fi

    local arch
    case "$(uname -m)" in
        x86_64)  arch=amd64 ;;
        aarch64) arch=arm64 ;;
        *) warn "unsupported CPU $(uname -m) – install Mailpit manually"; return 0 ;;
    esac

    local tmp asset="mailpit-linux-$arch.tar.gz" meta tag url digest
    tmp="$(mktemp -d)"
    if ! curl -fsSL -o "$tmp/release.json" https://api.github.com/repos/axllent/mailpit/releases/latest; then
        rm -rf "$tmp"; warn "cannot reach GitHub – install Mailpit manually"; return 0
    fi
    meta="$(php -r '
        $r = json_decode(file_get_contents($argv[1]), true);
        foreach ($r["assets"] ?? [] as $a) {
            if ($a["name"] === $argv[2]) {
                echo $r["tag_name"], " ", $a["browser_download_url"], " ", preg_replace("/^sha256:/", "", $a["digest"] ?? ""), "\n";
            }
        }' "$tmp/release.json" "$asset")"
    read -r tag url digest <<< "$meta"
    if [[ -z "${url:-}" || ! "${digest:-}" =~ ^[0-9a-f]{64}$ ]]; then
        rm -rf "$tmp"; warn "Mailpit release has no verifiable $asset – NOT installed, install it manually"; return 0
    fi
    if ! curl -fsSL -o "$tmp/$asset" "$url"; then
        rm -rf "$tmp"; warn "Mailpit $tag download failed – install it manually"; return 0
    fi
    if ! printf '%s  %s\n' "$digest" "$tmp/$asset" | sha256sum -c --status -; then
        rm -rf "$tmp"; warn "Mailpit checksum mismatch – NOT installed"; return 0
    fi

    mkdir -p "$LOCAL_BIN"
    tar -xzf "$tmp/$asset" -C "$tmp" mailpit
    install -m 0755 "$tmp/mailpit" "$LOCAL_BIN/mailpit"
    rm -rf "$tmp"
    done_ "Mailpit $tag installed to ~/.local/bin (checksum verified)"
}

# -----------------------------------------------------------------------------
# 5. Laravel: .env, dependencies, application key, storage symlink, permissions.
# -----------------------------------------------------------------------------
setup_laravel() {
    step "Laravel (api/)"

    if [[ -f "$API_DIR/.env" ]]; then
        skip "api/.env exists – left unchanged"
    else
        [[ -f "$API_DIR/.env.example" ]] || die "api/.env.example is missing"
        cp "$API_DIR/.env.example" "$API_DIR/.env"
        chmod 600 "$API_DIR/.env"
        # Local development defaults – applied only to this freshly created file.
        env_set APP_ENV local
        env_set APP_DEBUG true
        env_set APP_URL "http://127.0.0.1:8000"
        env_set FRONTEND_URL "https://localhost:4200"
        env_set DB_CONNECTION mysql
        env_set DB_HOST 127.0.0.1
        env_set DB_PORT 3306
        env_set DB_DATABASE "${APP_SLUG//-/_}"
        env_set DB_USERNAME root
        env_set DB_PASSWORD ""
        env_set QUEUE_CONNECTION database
        env_set MAIL_MAILER smtp
        env_set MAIL_HOST 127.0.0.1      # not "localhost": may resolve to ::1 where Mailpit does not listen
        env_set MAIL_PORT 1025
        env_set ANGULAR_I18N_PATH ../erp/src/assets/i18n
        # Cloudflare Turnstile official always-pass TEST secret (public, local only).
        [[ -n "$(env_get TURNSTILE_SECRET_KEY)" ]] || env_set TURNSTILE_SECRET_KEY 1x0000000000000000000000000000000AA
        ENV_CREATED=1
        done_ "api/.env created with local defaults (database: ${APP_SLUG//-/_}) – review it, see the summary"
    fi

    command -v php >/dev/null || die "PHP not found – install PHP 8.2+ (step 3), then run this script again"
    command -v composer >/dev/null || die "Composer not found – install it (step 3), then run this script again"
    info "composer install"
    (cd "$API_DIR" && composer install --no-interaction --no-progress)
    done_ "Composer dependencies installed"

    # Never regenerate an existing key: it would invalidate sessions and encrypted data.
    if [[ -z "$(env_get APP_KEY)" ]]; then
        (cd "$API_DIR" && php artisan key:generate --no-interaction >/dev/null)
        done_ "APP_KEY generated"
    else
        skip "APP_KEY already set – not regenerated"
    fi

    # Git does not keep empty directories – create the storage skeleton Laravel
    # expects BEFORE checking the symlink (its target must exist to be resolved).
    mkdir -p "$API_DIR"/storage/{logs,app/private,app/public} \
             "$API_DIR"/storage/framework/{cache/data,sessions,views} "$API_DIR"/bootstrap/cache
    chmod -R u+rwX,g+rwX "$API_DIR/storage" "$API_DIR/bootstrap/cache"
    info "storage/ and bootstrap/cache are writable"

    # The repository may contain a stale symlink from an old checkout path:
    # dangling, or resolving somewhere else than this checkout's storage.
    local link="$API_DIR/public/storage" target="$API_DIR/storage/app/public"
    if [[ -L "$link" ]] && { [[ ! -e "$link" ]] || [[ "$(readlink -f "$link")" != "$(readlink -f "$target")" ]]; }; then
        info "removing stale storage symlink → $(readlink "$link")"
        rm "$link"
    fi
    if [[ -L "$link" ]]; then
        skip "public/storage symlink OK"
    else
        (cd "$API_DIR" && php artisan storage:link --no-interaction >/dev/null)
        done_ "public/storage symlink created"
    fi

    # Config cache only – the cache store may be the database, which may not exist yet.
    (cd "$API_DIR" && php artisan config:clear --no-interaction >/dev/null 2>&1) || true
}

# -----------------------------------------------------------------------------
# 6. Database – created, migrated and seeded through Laravel (no phpMyAdmin step).
# @note Only a LOCAL database (DB_HOST 127.0.0.1 / localhost) is handled here; MariaDB of XAMPP
# is started for the step when it is not running and stopped again afterwards (dev.sh starts it
# for the work itself). An existing database is never dropped: `migrate` adds only missing
# migrations (the baseline migration is a no-op on a filled database) and the seeders add only
# missing base data. With APP_ENV=local the seeders also create the test sysadmin
# sysadmin@sysadmin.sysadmin / 123456Ab. and the test roles (DevelopmentSeeder).
# -----------------------------------------------------------------------------
MYSQL_STARTED=0

setup_database() {
    step "Database"
    local db host port
    db="$(env_get DB_DATABASE)"; host="$(env_get DB_HOST)"; port="$(env_get DB_PORT)"
    port="${port:-3306}"
    if [[ "$host" != "127.0.0.1" && "$host" != "localhost" ]]; then
        warn "DB_HOST=$host is not local – the database is not created by this script (create it there, then run: cd api && php artisan migrate && php artisan db:seed)"
        return 0
    fi

    if ! port_open "$port"; then
        info "starting MariaDB of XAMPP for this step (sudo)"
        sudo "$XAMPP_DIR/lampp" startmysql >/dev/null
        MYSQL_STARTED=1
        local _
        for _ in $(seq 1 30); do port_open "$port" && break; sleep 1; done
        port_open "$port" || { warn "MariaDB of XAMPP did not start on port $port – see $XAMPP_DIR/var/mysql/*.err, then run this script again"; return 0; }
    fi

    if ! (cd "$API_DIR" && php artisan db:create-if-missing --no-interaction); then
        warn "database '${db:-?}' could not be created – check DB_* in api/.env, then run this script again"
        stop_started_mysql; return 0
    fi
    if ! (cd "$API_DIR" && php artisan migrate --force --no-interaction); then
        warn "migrations failed – see the output above, then run this script again"
        stop_started_mysql; return 0
    fi
    if ! (cd "$API_DIR" && php artisan db:seed --force --no-interaction); then
        warn "seeding the base data failed – see the output above, then run this script again"
        stop_started_mysql; return 0
    fi

    if [[ "$(env_get APP_ENV)" == "local" ]]; then
        done_ "database '$db' ready – test login: sysadmin@sysadmin.sysadmin / 123456Ab. (2FA code in Mailpit)"
    else
        done_ "database '$db' ready (APP_ENV is not local – no test account created)"
    fi
    stop_started_mysql
}

# @description Whether something listens on 127.0.0.1:<port> (bash /dev/tcp, no extra tools).
port_open() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

# @description Stops MariaDB of XAMPP again when this script started it.
stop_started_mysql() {
    if [[ "$MYSQL_STARTED" == "1" ]]; then
        sudo "$XAMPP_DIR/lampp" stopmysql >/dev/null || true
        MYSQL_STARTED=0
        info "MariaDB of XAMPP stopped again (./dev.sh starts it)"
    fi
}

# -----------------------------------------------------------------------------
# 2. Temp folder – the git-ignored .temp/ folder for local scratch files (media, notes, …),
#    created right after the clone, with temp.txt explaining it. An existing temp.txt is left
#    unchanged; an .temp/info.txt of an older version of this script is left as it is.
# -----------------------------------------------------------------------------
setup_temp_dir() {
    step "Temp folder (.temp/)"
    local dir="$ROOT_DIR/.temp"
    mkdir -p "$dir"
    if [[ -f "$dir/temp.txt" ]]; then
        skip ".temp/ exists"
        return 0
    fi
    cat > "$dir/temp.txt" <<'TXT'
.temp/ – VYGENEROVANÉ DOČASNÉ PROSTŘEDÍ
======================================

Tuto složku vytvořil skript init-workspace.sh. Je to dočasné lokální prostředí pro
ukládání médií, obrázků, souborů, poznámek apod. při vývoji – vše na jednom místě
jen na tomto počítači.

Nic odtud nejde do gitu (složka je v .gitignore) ani na server.

UPOZORNĚNÍ: nedávejte sem nic důležitého. Obsah se může kdykoliv smazat (úklid,
nový checkout, nová instalace) a NENÍ ZÁLOHOVANÝ. Co je potřeba zachovat, patří
do repozitáře nebo do zálohy.

---
.temp/ – GENERATED TEMPORARY WORKSPACE
Created by init-workspace.sh: a temporary local place for media, images, files, notes, …
used during development, on this computer only. Git-ignored, never deployed.
WARNING: keep nothing important here – the content may be deleted at any time and is
NOT BACKED UP.
TXT
    done_ ".temp/ created (local scratch folder, git-ignored – see .temp/temp.txt)"
}

# -----------------------------------------------------------------------------
# 7. Angular: dependencies and the local SSL certificate used by `ng serve`.
# -----------------------------------------------------------------------------
setup_angular() {
    step "Angular (erp/)"

    info "installing npm dependencies"
    if [[ -f "$ERP_DIR/package-lock.json" ]]; then
        (cd "$ERP_DIR" && npm ci --no-audit --no-fund)
    else
        (cd "$ERP_DIR" && npm install --no-audit --no-fund)
    fi
    done_ "npm dependencies installed"

    if [[ -f "$SSL_CERT" && -f "$SSL_KEY" ]]; then
        skip "local SSL certificate exists"
    else
        mkdir -p "$SSL_DIR"
        if command -v mkcert >/dev/null; then
            mkcert -cert-file "$SSL_CERT" -key-file "$SSL_KEY" localhost 127.0.0.1 ::1 >/dev/null 2>&1
            done_ "trusted local SSL certificate created with mkcert"
        else
            openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 825 \
                -keyout "$SSL_KEY" -out "$SSL_CERT" -subj "/CN=localhost" \
                -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1" >/dev/null 2>&1
            done_ "self-signed local SSL certificate created (install mkcert for a browser-trusted one)"
        fi
        chmod 600 "$SSL_KEY"
    fi
}

# -----------------------------------------------------------------------------
# 8. Repository hygiene – ignore rules, executable scripts, remote check.
# -----------------------------------------------------------------------------
setup_repository() {
    step "Repository"
    local gi="$ROOT_DIR/.gitignore" rule added=()
    touch "$gi"
    for rule in '.dev/' '/build/' '/app_build/' '.~lock.*#' '/erp/ssl/' '/.temp/'; do
        grep -qxF "$rule" "$gi" || { printf '%s\n' "$rule" >> "$gi"; added+=("$rule"); }
    done
    if [[ ${#added[@]} -gt 0 ]]; then done_ ".gitignore: added ${added[*]}"; else skip ".gitignore complete"; fi

    local s
    for s in dev.sh deploy/build.sh init-workspace.sh; do
        [[ -f "$ROOT_DIR/$s" ]] && chmod +x "$ROOT_DIR/$s"
    done
    info "scripts are executable"

    # A new application cloned from web-platform must not push into the base repository.
    local origin
    origin="$(git -C "$ROOT_DIR" remote get-url origin 2>/dev/null || true)"
    if [[ "$APP_SLUG" != "web-platform" && "$origin" =~ /web-platform(\.git)?$ ]]; then
        warn "this app still pushes to web-platform – run: git remote rename origin upstream && git remote add origin <new-app-repo-url>"
    fi
    return 0
}

# -----------------------------------------------------------------------------
# 9. Shell aliases – one marked block per application in ~/.zshrc or ~/.bashrc,
# replaced on every run (so several cloned apps never overwrite each other).
# -----------------------------------------------------------------------------
setup_aliases() {
    step "Shell aliases"
    local names="$APP_SLUG, $APP_SLUG-dev, $APP_SLUG-build"
    if [[ "$WITH_ALIASES" == "0" ]]; then skip "aliases (--no-aliases)"; return 0; fi

    local rc
    case "${SHELL##*/}" in zsh) rc="$HOME/.zshrc" ;; *) rc="$HOME/.bashrc" ;; esac
    touch "$rc"
    local start="# >>> init-workspace: $APP_SLUG >>>" end="# <<< init-workspace: $APP_SLUG <<<"
    # Block written by the first version of this script (wp/wpdev/wpbuild) – replaced.
    local legacy_s='# >>> web-platform (init-workspace.sh) >>>' legacy_e='# <<< web-platform (init-workspace.sh) <<<'
    local tmp; tmp="$(mktemp)"
    awk -v s="$start" -v e="$end" -v ls="$legacy_s" -v le="$legacy_e" '
        $0 == s || $0 == ls {skip = 1}
        !skip {print}
        $0 == e || $0 == le {skip = 0}' "$rc" > "$tmp"
    {
        printf '%s\n' "$start"
        # shellcheck disable=SC2016  # $HOME/$PATH are expanded by the shell profile, not here
        printf 'case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH" ;; esac\n'
        printf "alias %s='cd %q'\n" "$APP_SLUG" "$ROOT_DIR"
        printf "alias %s-dev='%q/dev.sh'\n" "$APP_SLUG" "$ROOT_DIR"
        printf "alias %s-build='%q/deploy/build.sh'\n" "$APP_SLUG" "$ROOT_DIR"
        printf '%s\n' "$end"
    } >> "$tmp"
    cat "$tmp" > "$rc"
    rm -f "$tmp"
    done_ "aliases $names added to ~${rc#"$HOME"} (open a new terminal)"
}

# -----------------------------------------------------------------------------
# 10. Summary – including the manual review of api/.env.
# -----------------------------------------------------------------------------
summary() {
    step "Summary"
    if (cd "$API_DIR" && composer check-platform-reqs --lock --no-interaction >/dev/null 2>&1); then
        info "PHP satisfies api/composer.lock"
    else
        warn "PHP does not satisfy api/composer.lock – run 'composer check-platform-reqs --lock' in api/"
    fi

    local db; db="$(env_get DB_DATABASE)"
    echo
    printf 'Done: %d · already set up: %d\n' "${#DONE[@]}" "${#SKIPPED[@]}"
    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        printf '\e[33mWarnings: %d – fix them and run ./init-workspace.sh again:\e[0m\n' "${#WARNINGS[@]}"
        local w; for w in "${WARNINGS[@]}"; do printf '  ! %s\n' "$w"; done
    fi

    local env_state="existing file – check it still matches this app"
    [[ "$ENV_CREATED" == "1" ]] && env_state="CREATED NOW from .env.example – review it before the first start"

    cat <<EOF

LAST STEP – BY HAND
  1. Review api/.env   ($env_state)
       APP_NAME, APP_URL, FRONTEND_URL      name and local URLs of this app
       DB_DATABASE=${db:-<name>}, DB_USERNAME, DB_PASSWORD
                                            database of step 6 (XAMPP default: root, no password)
       MAIL_FROM_ADDRESS, MAIL_FROM_NAME    sender of e-mails (caught locally by Mailpit)
       TURNSTILE_SECRET_KEY                 captcha – a public TEST key is preset for local use
       any other keys of this app (API keys, payment gateway, …) – see .env.example
     Never commit api/.env – it is git-ignored.
     After changing DB_* run this script again – step 6 creates and fills the new database.

  LOCAL TEST LOGIN (APP_ENV=local only)
       e-mail:   sysadmin@sysadmin.sysadmin
       password: 123456Ab.
       2FA code: in Mailpit – http://127.0.0.1:8025 (sysadmin always needs 2FA)
       test roles: read-only-core, read-only-web, read-only-shop, full-web-core, full-shop-core, all-permissions
EOF

    echo
    echo "=========================================="
    if [[ ${#WARNINGS[@]} -eq 0 ]]; then
        printf '\e[32m WORKSPACE SETUP COMPLETE – %s\e[0m\n' "$APP_SLUG"
        echo "=========================================="
        echo "Once api/.env is reviewed, start the application:"
        echo "  ./dev.sh        (Ctrl+C stops everything)"
    else
        printf '\e[33m WORKSPACE SETUP INCOMPLETE – %s\e[0m\n' "$APP_SLUG"
        echo "=========================================="
        echo "Fix the warnings above and run ./init-workspace.sh again."
    fi
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
echo "------------------------------------------"
echo "Workspace setup – $APP_SLUG"
echo "------------------------------------------"
preflight
setup_github_ssh
require_xampp
setup_temp_dir
install_system_packages
install_mailpit
setup_laravel
setup_database
setup_angular
setup_repository
setup_aliases
summary
