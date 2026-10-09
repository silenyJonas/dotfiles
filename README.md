# dotfiles

Záloha mého nastavení pro Fedoru s Hyprlandem. Konfigurace jsou rozdělené do složek („balíčků") a do domovského adresáře se propojují symlinky pomocí [GNU Stow](https://www.gnu.org/software/stow/).

## Co v repozitáři je

Každá složka kopíruje strukturu domovského adresáře. Například `hypr/.config/hypr/` se po propojení objeví jako `~/.config/hypr/`.

| Složka | Kam se propojí | Obsah |
|---|---|---|
| `hypr` | `~/.config/hypr` | Hyprland (`hyprland.conf`), skript `scripts/focus-or-workspace.sh` |
| `waybar` | `~/.config/waybar` | horní lišta |
| `rofi` | `~/.config/rofi` | launcher, powermenu, applety (vyžaduje balíček `rofi-wayland`) |
| `kitty` | `~/.config/kitty` | terminál Kitty |
| `wezterm` | `~/.wezterm.lua` | terminál WezTerm |
| `zsh` | `~/.zshrc` | nastavení shellu (vyžaduje oh-my-zsh), funkce `spotify` |
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

## Ovládání z klávesnice

`Super` je klávesa Windows.

| Zkratka | Akce |
|---|---|
| `Super + ←/→` | fokus na okno vedle; na krajním okně přepne na sousední plochu |
| `Super + ↑/↓` | fokus na okno nad/pod |
| `Super + Ctrl + ←/→` | předchozí / další plocha |
| `Super + Ctrl + Shift + ←/→` | přesun okna na předchozí / další plochu |
| `Alt + Tab` | další okno na aktuální ploše |
| `Super + R` | launcher (rofi) |
| `Super + O`, `Super + X` | powermenu (rofi) |
| `Super + Q`, `Super + T` | terminál |
| `Super + C` | zavřít okno |
| `Super + S` | screenshot oblasti do editoru Swappy |

Přepínání `Super + ←/→` mezi plochami zajišťuje skript `focus-or-workspace.sh` spolu s volbou `no_focus_fallback = true` v bloku `general`.

## Poznámky k nastavení

**Displej se škálováním 2×.** Aplikace běžící přes XWayland by byly rozmazané, proto je v `hyprland.conf` nastaveno:

```ini
xwayland {
    force_zero_scaling = true
}
```

XWayland aplikace jsou díky tomu ostré, ale v poloviční velikosti, a zvětšení se jim nastavuje zvlášť:

- **Spotify:** funkce `spotify` v `.zshrc` ho spouští s `--force-device-scale-factor=2`, na pozadí a bez výpisů do terminálu.
- **Rofi:** místo balíčku `rofi` je nainstalovaný `rofi-wayland`, který běží nativně a škáluje se sám.

Při jiném škálování displeje je potřeba hodnotu `2` ve funkci `spotify` upravit. Aktuální škálování ukáže `hyprctl monitors | grep scale`.

**Česká klávesnice.** Číselná řada bez Shiftu nepíše číslice, takže zkratky typu `Super + 1` nemusí fungovat. Řešením je v `hyprland.conf` použít kódy kláves `code:10` až `code:19` místo `1` až `0`.

**Okno „Authentication required" (klíčenka).** Vyskakuje, když má klíčenka GNOME Keyring jiné heslo než uživatelský účet. Oprava: smazat `~/.local/share/keyrings/login.keyring` a znovu se přihlásit, klíčenka se vytvoří s aktuálním heslem. Aplikace pak jednou vyžádají nové přihlášení.

## Nainstalované programy

Samotné programy v repozitáři nejsou, jen jejich seznamy ve složce `system/`:

| Soubor | Obsah |
|---|---|
| `system/packages.txt` | balíčky ručně nainstalované přes `dnf` |
| `system/copr.txt` | přidané COPR repozitáře (např. pro Hyprland) |
| `system/flatpaks.txt` | aplikace nainstalované přes Flatpak |
| `system/snaps.txt` | aplikace nainstalované přes Snap (např. Spotify) |

Aktualizace seznamů:

```bash
cd ~/dotfiles
dnf repoquery --userinstalled --queryformat '%{name}\n' | sort > system/packages.txt
dnf copr list > system/copr.txt
flatpak list --app --columns=application > system/flatpaks.txt
snap list | awk 'NR>1{print $1}' > system/snaps.txt
```

V seznamech nejsou programy nainstalované jinou cestou. Ty je potřeba doinstalovat ručně:

- oh-my-zsh (`~/.oh-my-zsh`)
- XAMPP (`/opt/lampp`), instalátor z webu Apache Friends
- Mailpit
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

Snap aplikace se instalují jednotlivě podle `system/snaps.txt`:

```bash
sudo dnf install snapd
sudo snap install spotify
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
- Zkontrolovat škálování displeje a případně upravit hodnotu ve funkci `spotify` (viz Poznámky k nastavení).

## Co v repozitáři záměrně není

- SSH a GPG klíče (`~/.ssh`, `~/.gnupg`), zálohují se zvlášť mimo GitHub
- historie shellu, profily prohlížečů, přihlašovací údaje aplikací
- cache a data aplikací (`~/.cache`, `~/.local/share`)
- projekty a databáze z XAMPPu (`/opt/lampp/htdocs`, `/opt/lampp/var/mysql`), projekty mají vlastní repozitáře

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
