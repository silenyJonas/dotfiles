export ZSH="$HOME/.oh-my-zsh"
export ELECTRON_OZONE_PLATFORM_HINT=auto
export GDK_BACKEND=wayland
ZSH_THEME="robbyrussell"
plugins=(git zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

# ───── APPS ─────
alias discord='flatpak run dev.vencord.Vesktop >/dev/null 2>&1 &!'
alias fastfetch='clear && fastfetch'
alias pipes="~/Apps/pipes.sh"
alias clock='tty-clock -sbc -C 7'
alias cmatrix='cmatrix -C white'
alias firefox='nohup firefox >/dev/null 2>&1 &'
alias postmanstart="\"$HOME/Apps/Postman Agent/app/postman-agent\" &"
alias postmanstop="pkill -f postman-agent"
alias brave="nohup brave-browser > /dev/null 2>&1 & disown"

# ───── XAMPP ─────
alias xamppstart='sudo /opt/lampp/lampp start'
alias xamppstop='sudo /opt/lampp/lampp stop'
alias xampprestart='sudo /opt/lampp/lampp restart'
alias xamppgui='sudo /opt/lampp/manager-linux-x64.run'
alias xamppstatus='sudo /opt/lampp/lampp status 2>/dev/null'

# ───── SYSTEM ─────
alias update='sudo dnf update -y && sudo dnf upgrade -y'
alias reboot='sudo systemctl reboot'
alias shutdown='sudo systemctl poweroff'
alias meminfo='free -h'
alias diskinfo='df -h'
alias cls='clear'

# ───── NAVIGACE ─────
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ~='cd ~'

# ───── GIT ─────
alias gst='git status'
alias gco='git checkout'
alias gcm='git commit -m'
alias ga='git add'
alias gl='git log --oneline --graph --all'

# ───── NETWORK ─────
alias myip='curl ifconfig.me'
alias ping8='ping 8.8.8.8'
alias ports='ss -tuln'

# ───── MAIL PIT EMAIL SERVICE ─────
alias mailpitstart='pgrep -x mailpit > /dev/null && echo "Mailpit už běží (http://localhost:8025)" || { mailpit > /dev/null 2>&1 &! ; echo "Mailpit spuštěn: http://localhost:8025" }'
alias mailpitstop='pkill -x mailpit && echo "Mailpit vypnut" || echo "Mailpit neběžel"'

# ───── FUN / UTILITIES ─────
alias weather='curl wttr.in'
alias cowsay='cowsay -f tux'  # pokud máš nainstalovaný cowsay
alias timer='echo "Spuštěno: $(date)" && sleep 60 && echo "Čas uplynul!"'

# ───── DEVELOPMENT ─────
alias serve='python3 -m http.server'
alias py='python3'
alias node='node'
alias npm='npm'
#_________________________
# Neovide GUI editor, otevře zadanou složku nebo soubor
neovide() {
    if [ -z "$1" ]; then
        gtk-launch neovide
    else
        gtk-launch neovide "$1"
    fi
}
# =========================
# Otevření souboru nebo složky ve VSCodium
# =========================
codium() {
    if [ -z "$1" ]; then
        # Pokud není argument, otevře aktuální složku
        command codium .
    else
        # Otevře složku nebo soubor z argumentu
        command codium "$1"
    fi
}

alias rofi_launcher="$HOME/.config/rofi/launchers/type-6/launcher.sh"



export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$HOME/.cargo/bin:$PATH"

unalias spotify 2>/dev/null
spotify() {
    flatpak run com.spotify.Client "$@" >/dev/null 2>&1 &!
}

export PATH=$PATH:/home/joncl/.spicetify
alias spotify='~/.local/bin/spotify-launch'

# --- island: odpojené GUI programy (zavření konzole je neukončí, konzole hned zase poslouchá)
setopt NO_HUP NO_CHECK_JOBS
detach() { (setsid "$@" >/dev/null 2>&1 &) }
for _app in kwrite kate dolphin okular gwenview ark brave-browser codium nautilus loupe evince; do
  command -v $_app >/dev/null && alias $_app="detach $_app"
done
unset _app

# --- island: yazi
[[ ":$PATH:" != *":$HOME/.local/bin:"* ]] && export PATH="$HOME/.local/bin:$PATH"
y() {
  local tmp="$(mktemp -t yazi-cwd.XXXXXX)" cwd
  yazi "$@" --cwd-file="$tmp"
  if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then builtin cd -- "$cwd"; fi
  rm -f -- "$tmp"
}
command -v zoxide >/dev/null && eval "$(zoxide init zsh)"

# --- island: ys = yazi jako správce (root) se stejným vzhledem; POZOR, smí smazat i systémové soubory
ys() { sudo YAZI_CONFIG_HOME="$HOME/.config/yazi" "$(command -v yazi)" "$@"; }
