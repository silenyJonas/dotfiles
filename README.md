# dotfiles

Záloha mého nastavení pro Fedoru s Hyprlandem. Konfigurace jsou rozdělené do složek („balíčků") a do domovského adresáře se propojují symlinky pomocí [GNU Stow](https://www.gnu.org/software/stow/).

## Co v repozitáři je

Každá složka kopíruje strukturu domovského adresáře. Například `hypr/.config/hypr/` se po propojení objeví jako `~/.config/hypr/`.

| Složka | Kam se propojí | Obsah |
|---|---|---|
| `hypr` | `~/.config/hypr` | Hyprland (`hyprland.conf`), skript `scripts/focus-or-workspace.sh` |
| `waybar` | `~/.config/waybar` | horní lišta |
| `island-panel` | `~/.config/island-panel` | vlastní panel (`panel.py`, `style.css`): rozbalovací panel shora, hlasitost a jas, ovládací centrum, oznámení, přepínač tapet |
| `rofi` | `~/.config/rofi` | launcher, powermenu, applety (vyžaduje balíček `rofi-wayland`) |
| `kitty` | `~/.config/kitty` | terminál Kitty |
| `wezterm` | `~/.wezterm.lua` | terminál WezTerm |
| `zsh` | `~/.zshrc` | nastavení shellu (vyžaduje oh-my-zsh), funkce `spotify`, cesta ke Spicetify |
| `git` | `~/.gitconfig` | jméno, e-mail, přihlašování přes `gh` |
| `nvim` | `~/.config/nvim` | Neovim (AstroNvim) |
| `vscodium` | `~/.config/VSCodium/User` | `settings.json`, `keybindings.json` |
| `fastfetch` | `~/.config/fastfetch` | výpis informací o systému |
| `btop` | `~/.config/btop` | monitor systému |
| `cava` | `~/.config/cava` | vizualizér zvuku |
| `swaylock` | `~/.config/swaylock` | zamykací obrazovka |
| `hyprpaper` | `~/.config/hyprpaper` | tapety přes hyprpaper (nepoužívá se, tapetu nastavuje `swaybg` přes přepínač tapet) |
| `superfile` | `~/.config/superfile` | správce souborů v terminálu |
| `bin` | `~/bin` | vlastní skripty (`yazi.sh`, `yazi-root.sh`, `spf-wrapper.sh`, `spf-wrapper-debug.sh`) |
| `apps` | `~/Apps/pipes.sh` | skript pipes.sh |
| `wallpapers` | `~/Pictures/wallpapers` | tapety |
| `fonts` | `~/.local/share/fonts` | fonty pro rofi a waybar (Iosevka Nerd Font, JetBrains Mono Nerd Font, Icomoon Feather, Grape Nuts) |
| `icons` | `~/.icons` | motivy kurzoru (používá se `Kitty`) |
| `kde-colors` | `~/.local/share/color-schemes` | barevné schéma `Island` pro Dolphin a další KDE aplikace |
| `spicetify` | nepropojuje se | kopie nastavení Spicetify (`config-xpui.ini`), viz Obnova |
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
| `Super + D` | Island panel (přehled, média, výkon) |
| `Super + A` | Island panel na seznamu aplikací s hledáním |
| `Super + W` | přepínač tapet |
| `Super + O`, `Super + X` | powermenu (rofi) |
| `Super + Q`, `Super + T` | terminál |
| `Super + C` | zavřít okno |
| `Super + S` | screenshot oblasti do editoru Swappy |

Přepínání `Super + ←/→` mezi plochami zajišťuje skript `focus-or-workspace.sh` spolu s volbou `no_focus_fallback = true` v bloku `general`. Při více monitorech zůstává fokus na tom, kde zrovna jsi.

## Island panel

Jeden program v Pythonu (GTK 3 + gtk-layer-shell), který po přihlášení spouští `hyprland.conf` a který vypadá jako ostrůvky ve Waybaru.

| Kde | Co se stane |
|---|---|
| kurzor na horním okraji uprostřed, nebo `Super + D` | vyjede panel se záložkami Dashboard, Media, Performance, Apps |
| kurzor krátce na pravém okraji | posuvníky hlasitosti a jasu |
| kurzor asi vteřinu na pravém okraji | ovládací centrum: oznámení, otevřená okna, rychlé přepínače, vypnutí a odhlášení |
| `Super + W` | přepínač tapet ze složky `~/Pictures/wallpapers` |

Přepínač tapet: šipky vybírají, Enter nebo klik na prostřední náhled tapetu nastaví, mezerník ji nastaví bez zavření, psaní hledá podle názvu, Esc zavírá. Podsložky se v liště objeví jako filtry. Vybraná tapeta se pamatuje v `~/.local/state/island-panel/wallpaper` a po přihlášení ji odtud načte řádek `exec-once = swaybg …` v `hyprland.conf`. Animované GIFy a videa fungují jen s programem `mpvpaper` (není v repozitářích Fedory, překládá se ze zdrojáků), bez něj se GIF nastaví jako nehybný obrázek.

Nastavení (velikosti, zpoždění, složka s tapetami, město pro počasí) je na začátku `panel.py`, vzhled ve `style.css` (načítá se sám po uložení). Po úpravě `panel.py` je potřeba panel restartovat:

```bash
/usr/bin/python3 ~/.config/island-panel/panel.py --quit; sleep 1
hyprctl dispatch exec "/usr/bin/python3 ~/.config/island-panel/panel.py"
```

Panel potřebuje balíčky `python3-gobject`, `gtk3`, `gtk-layer-shell` a `swaybg`.

## Poznámky k nastavení

**Displej se škálováním 2×.** Aplikace běžící přes XWayland by byly rozmazané, proto je v `hyprland.conf` nastaveno:

```ini
xwayland {
    force_zero_scaling = true
}
```

XWayland aplikace jsou díky tomu ostré, ale v poloviční velikosti, proto se používají verze, které běží nativně:

- **Rofi:** místo balíčku `rofi` je nainstalovaný `rofi-wayland`, který běží nativně a škáluje se sám.
- **Spotify:** verze z Flatpaku (`com.spotify.Client`), škáluje se sama. Funkce `spotify` v `.zshrc` ji spouští na pozadí a bez výpisů do terminálu.

**Externí monitor.** Monitor na HDMI má v `hyprland.conf` vlastní řádek `monitor = HDMI-A-1, 1920x1080@144, auto, 1`. Pro jiný monitor je potřeba ho upravit.

**Vzhled Spotify.** Spotify je upravené přes [Spicetify](https://spicetify.app) s tématem `text` a schématem `Spotify`. Po aktualizaci Spotify se úprava obvykle ztratí a vrací se příkazem `spicetify backup apply` (někdy je potřeba znovu nastavit práva, viz Obnova). Původní vzhled vrátí `spicetify restore`. Průhlednost okna nastavuje pravidlo `windowrulev2 = opacity …` v `hyprland.conf`.

**Česká klávesnice.** Číselná řada bez Shiftu nepíše číslice, takže zkratky typu `Super + 1` nemusí fungovat. Řešením je v `hyprland.conf` použít kódy kláves `code:10` až `code:19` místo `1` až `0`.

**Okno „Authentication required" (klíčenka).** Vyskakuje, když má klíčenka GNOME Keyring jiné heslo než uživatelský účet. Oprava: smazat `~/.local/share/keyrings/login.keyring` a znovu se přihlásit, klíčenka se vytvoří s aktuálním heslem. Aplikace pak jednou vyžádají nové přihlášení.

## Nainstalované programy

Samotné programy v repozitáři nejsou, jen jejich seznamy ve složce `system/`:

| Soubor | Obsah |
|---|---|
| `system/packages.txt` | balíčky ručně nainstalované přes `dnf` |
| `system/copr.txt` | přidané COPR repozitáře (např. pro Hyprland) |
| `system/flatpaks.txt` | aplikace nainstalované přes Flatpak |
| `system/snaps.txt` | aplikace nainstalované přes Snap |

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
- Spicetify (`~/.spicetify`) a jeho témata, viz Obnova
- `mpvpaper` pro animované tapety (volitelné, ze zdrojáků z GitHubu `GhostNaN/mpvpaper`)

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

Pokud v `system/snaps.txt` něco je, instaluje se to jednotlivě přes `sudo snap install název` (vyžaduje balíček `snapd`).

### 3. oh-my-zsh

Instaluje se před propojením konfigurací, protože si vytvoří vlastní `~/.zshrc`, který je potřeba smazat:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
rm ~/.zshrc
```

### 4. Propojení konfigurací

```bash
cd ~/dotfiles
for d in */; do case "$d" in system/|spicetify/) ;; *) stow "$d" ;; esac; done
fc-cache -f
```

Pokud Stow ohlásí konflikt, na daném místě už existuje soubor nebo složka (typicky `~/.config/hypr`, kterou si Hyprland vytvoří při prvním spuštění). Stačí ji smazat nebo přejmenovat a příkaz spustit znovu.

### 5. Vzhled Spotify (Spicetify)

Nejdřív Spotify z Flatpaku jednou spusť a přihlas se, pak ho zavři. Příkaz `sudo -v` pusť samostatně a zadej heslo, teprve potom zbytek:

```bash
sudo -v
```

```bash
curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh | sh
SP=/var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify
sudo chmod a+wr $SP
sudo chmod a+wr -R $SP/Apps
git clone --depth=1 https://github.com/spicetify/spicetify-themes.git ~/src/spicetify-themes
mkdir -p ~/.config/spicetify/Themes
cp -r ~/src/spicetify-themes/text ~/.config/spicetify/Themes/
~/.spicetify/spicetify config spotify_path "$SP"
~/.spicetify/spicetify config prefs_path "$HOME/.var/app/com.spotify.Client/config/spotify/prefs"
~/.spicetify/spicetify config current_theme text color_scheme Spotify
~/.spicetify/spicetify backup apply
```

Kdyby `backup apply` spadlo uprostřed (typicky kvůli právům), Spotify zůstane rozbité. Oprava: přeinstalovat Spotify (`flatpak uninstall` a `flatpak install`), znovu nastavit práva, pustit `spicetify clear` a `spicetify backup apply`. Soubor `spicetify/config-xpui.ini` v repozitáři je kopie nastavení pro porovnání.

### 6. Po obnově

- Neovim si pluginy stáhne sám při prvním spuštění.
- V `hyprland.conf` jsou cesty s `/home/joncl/`. Při jiném uživatelském jménu je potřeba je upravit.
- Zsh jako výchozí shell: `chsh -s $(which zsh)`
- Barvy Dolphinu: `plasma-apply-colorscheme Island`
- Tapeta: `Super + W`, do té doby se použije `~/Pictures/wallpapers/my_name.jpg`.

## Co v repozitáři záměrně není

- SSH a GPG klíče (`~/.ssh`, `~/.gnupg`), zálohují se zvlášť mimo GitHub
- historie shellu, profily prohlížečů, přihlašovací údaje aplikací
- cache a data aplikací (`~/.cache`, `~/.local/share`)
- projekty a databáze z XAMPPu (`/opt/lampp/htdocs`, `/opt/lampp/var/mysql`), projekty mají vlastní repozitáře

## Běžná práce

Konfigurace se upravují na obvyklých místech (např. `~/.config/hypr/hyprland.conf`), díky symlinkům se změny rovnou projeví tady. Uložení změn:

```bash
cd ~/dotfiles
cp ~/.config/spicetify/config-xpui.ini spicetify/
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
