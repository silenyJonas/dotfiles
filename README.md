# dotfiles

Záloha mého nastavení pro Fedoru s Hyprlandem. Konfigurace jsou rozdělené do složek („balíčků") a do domovského adresáře se propojují symlinky pomocí [GNU Stow](https://www.gnu.org/software/stow/).

## Co v repozitáři je

Každá složka kopíruje strukturu domovského adresáře. Například `hypr/.config/hypr/` se po propojení objeví jako `~/.config/hypr/`.

| Složka | Kam se propojí | Obsah |
|---|---|---|
| `hypr` | `~/.config/hypr` | Hyprland (`hyprland.conf`), skript `scripts/focus-or-workspace.sh` |
| `waybar` | `~/.config/waybar` | horní lišta |
| `rofi` | `~/.config/rofi` | launcher, powermenu, applety |
| `kitty` | `~/.config/kitty` | terminál Kitty |
| `wezterm` | `~/.wezterm.lua` | terminál WezTerm |
| `zsh` | `~/.zshrc` | nastavení shellu (vyžaduje oh-my-zsh) |
| `git` | `~/.gitconfig` | jméno, e-mail, přihlašování přes `gh` |
| `nvim` | `~/.config/nvim` | Neovim (AstroNvim) |
| `vscodium` | `~/.config/VSCodium/User` | `settings.json`, `keybindings.json` |
| `fastfetch` | `~/.config/fastfetch` | výpis informací o systému |
| `btop` | `~/.config/btop` | monitor systému |
| `cava` | `~/.config/cava` | vizualizér zvuku |
| `swaylock` | `~/.config/swaylock` | zamykací obrazovka |
| `hyprpaper` | `~/.config/hyprpaper` | tapety přes hyprpaper (aktuálně se používá `swaybg`) |
| `superfile` | `~/.config/superfile` | správce souborů v terminálu |
| `bin` | `~/bin` | vlastní skripty (`yazi.sh`, `yazi-root.sh`, `spf-wrapper.sh`, `spf-wrapper-debug.sh`) |
| `apps` | `~/Apps/pipes.sh` | skript pipes.sh |
| `wallpapers` | `~/Pictures/wallpapers` | tapety |
| `fonts` | `~/.local/share/fonts` | fonty pro rofi a waybar (Iosevka Nerd Font, JetBrains Mono Nerd Font, Icomoon Feather, Grape Nuts) |
| `icons` | `~/.icons` | motivy kurzoru (používá se `Kitty`) |
| `system` | nepropojuje se | seznamy nainstalovaných programů, viz níže |

## Nainstalované programy

Samotné programy v repozitáři nejsou, jen jejich seznamy ve složce `system/`:

| Soubor | Obsah |
|---|---|
| `system/packages.txt` | balíčky ručně nainstalované přes `dnf` |
| `system/copr.txt` | přidané COPR repozitáře (např. pro Hyprland) |
| `system/flatpaks.txt` | aplikace nainstalované přes Flatpak |

Aktualizace seznamů:

```bash
cd ~/dotfiles
dnf repoquery --userinstalled --queryformat '%{name}\n' | sort > system/packages.txt
dnf copr list > system/copr.txt
flatpak list --app --columns=application > system/flatpaks.txt
```

V seznamech nejsou programy nainstalované mimo `dnf` a Flatpak. Ty je potřeba doinstalovat ručně:

- oh-my-zsh (`~/.oh-my-zsh`)
- Postman (`~/Apps/Postman`)
- nástroje z `pip` (`~/.local/bin`) a `cargo` (`~/.cargo/bin`)

## Obnova na novém systému

### 1. Základní nástroje a stažení repozitáře

```bash
sudo dnf install git stow gh
gh auth login
git clone https://github.com/silenyJonas/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

### 2. Programy

Nejdřív povol COPR repozitáře podle `system/copr.txt`, každý zvlášť ve tvaru `uživatel/projekt`:

```bash
cat system/copr.txt
sudo dnf copr enable uživatel/projekt
```

Pak nainstaluj balíčky a Flatpak aplikace:

```bash
sudo dnf install --skip-unavailable $(cat system/packages.txt)
xargs -r -a system/flatpaks.txt flatpak install -y flathub
```

### 3. oh-my-zsh

Instaluje se před propojením konfigurací, protože si vytvoří vlastní `~/.zshrc`, který je potřeba smazat:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
rm ~/.zshrc
```

### 4. Propojení konfigurací

```bash
cd ~/dotfiles
for d in */; do [ "$d" != "system/" ] && stow "$d"; done
fc-cache -f
```

Pokud Stow ohlásí konflikt, na daném místě už existuje soubor nebo složka (typicky `~/.config/hypr`, kterou si Hyprland vytvoří při prvním spuštění). Stačí ji smazat nebo přejmenovat a příkaz spustit znovu.

### 5. Po obnově

- Neovim si pluginy stáhne sám při prvním spuštění.
- V `hyprland.conf` jsou cesty s `/home/joncl/`. Při jiném uživatelském jménu je potřeba je upravit.
- Zsh jako výchozí shell: `chsh -s $(which zsh)`

## Co v repozitáři záměrně není

- SSH a GPG klíče (`~/.ssh`, `~/.gnupg`), zálohují se zvlášť mimo GitHub
- historie shellu, profily prohlížečů, přihlašovací údaje aplikací
- cache a data aplikací (`~/.cache`, `~/.local/share`)

## Běžná práce

Konfigurace se upravují na obvyklých místech (např. `~/.config/hypr/hyprland.conf`), díky symlinkům se změny rovnou projeví tady. Uložení změn:

```bash
cd ~/dotfiles
git add .
git commit -m "popis změny"
git push
```

Přidání další konfigurace (příklad pro `~/.config/neco`):

```bash
cd ~/dotfiles
mkdir -p neco/.config
mv ~/.config/neco neco/.config/ && stow neco
```

Před každým přidáním je dobré zkontrolovat, že soubory neobsahují hesla ani tokeny:

```bash
grep -rniE "token|password|passwd|secret|api_key" ~/dotfiles --exclude-dir=.git
```
