# dotfiles

Záloha mého nastavení pro Fedoru s Hyprlandem. Konfigurace jsou rozdělené do složek („balíčků") a do domovského adresáře se propojují symlinky pomocí [GNU Stow](https://www.gnu.org/software/stow/).

Celé prostředí má jeden vzhled „Island": tmavě modré ostrůvky se zaoblenými rohy, písmo Nunito, ikony z JetBrains Mono Nerd Font a barvy

| Barva | Hodnota | Použití |
|---|---|---|
| pozadí | `#0a1e2c` | panely, lišta, zámek |
| text | `#dbe7ee` | běžný text |
| tlumený text | `#7f97a5` | popisky |
| akcent | `#7dbedc` | vybrané položky, ikony, zapnuté stavy |
| pilulka | `#e6eef2` | světlá tlačítka (tlačítko vypnutí, Play) |
| chyba | `#bf616a` | varování, plný disk |

## Co v repozitáři je

Každá složka kopíruje strukturu domovského adresáře. Například `hypr/.config/hypr/` se po propojení objeví jako `~/.config/hypr/`.

| Složka | Kam se propojí | Obsah |
|---|---|---|
| `hypr` | `~/.config/hypr` | Hyprland (`hyprland.conf`), `hypridle.conf`, zámek obrazovky `lock/`, skripty `scripts/` |
| `waybar` | `~/.config/waybar` | horní lišta, skripty `scripts/netspeed.py` (rychlost sítě) a `scripts/vpn-status.py` (štít VPN) |
| `island-panel` | `~/.config/island-panel` | vlastní panel (`panel.py`, `style.css`), viz Island panel |
| `rofi` | `~/.config/rofi` | launcher, powermenu, applety (vyžaduje balíček `rofi-wayland`) |
| `kitty` | `~/.config/kitty` | terminál Kitty (kurzor se šmouhou `cursor_trail`) |
| `yazi` | `~/.config/yazi` | správce souborů v terminálu, vzhled Island |
| `zsh` | `~/.zshrc` | shell (oh-my-zsh), příkazy `y`, `ys`, `detach`, `spotify`, `discord` |
| `local` | `~/.local` | spouštěč Spotify `bin/spotify-launch`, přejmenované aplikace v `share/applications` |
| `git` | `~/.gitconfig` | jméno, e-mail, přihlašování přes `gh` |
| `nvim` | `~/.config/nvim` | Neovim (AstroNvim) |
| `vscodium` | `~/.config/VSCodium/User` | `settings.json`, `keybindings.json` |
| `fastfetch` | `~/.config/fastfetch` | výpis informací o systému |
| `btop` | `~/.config/btop` | monitor systému |
| `cava` | `~/.config/cava` | vizualizér zvuku (panel ho už nepoužívá) |
| `swaylock` | `~/.config/swaylock` | starý zámek, nahrazený hyprlockem (záloha) |
| `hyprpaper` | `~/.config/hyprpaper` | nepoužívá se, tapetu nastavuje `swaybg` přes přepínač tapet |
| `superfile` | `~/.config/superfile` | starší správce souborů v terminálu |
| `bin` | `~/bin` | vlastní skripty |
| `apps` | `~/Apps/pipes.sh` | skript pipes.sh |
| `wallpapers` | `~/Pictures/wallpapers` | tapety |
| `fonts` | `~/.local/share/fonts` | Nunito, Iosevka Nerd Font, JetBrains Mono Nerd Font, Icomoon Feather, Grape Nuts |
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
| `Super + D` | Island panel (přehled, média, výkon, aplikace) |
| `Super + A` | Island panel na seznamu aplikací s hledáním |
| `Super + W` | přepínač tapet |
| `Super + L` | zamknout obrazovku |
| `Super + O`, `Super + X` | powermenu (rofi) |
| `Super + Q`, `Super + T` | terminál |
| `Super + C` | zavřít okno |
| `Super + S` | screenshot oblasti do editoru Swappy |

Přepínání `Super + ←/→` mezi plochami zajišťuje skript `focus-or-workspace.sh` spolu s volbou `no_focus_fallback = true` v bloku `general`. Při více monitorech zůstává fokus na tom, kde zrovna jsi.

## Horní lišta (Waybar)

Vlevo plochy, uprostřed hodiny, vpravo ostrůvek se stavem systému:

| Prvek | Klik |
|---|---|
| `↓ 768 B/s ↑ 2.2 kB/s` rychlost sítě (`scripts/netspeed.py`) | okno Wi-Fi |
| síla Wi-Fi | okno Wi-Fi |
| disk | |
| Bluetooth | okno Bluetooth |
| štít VPN (`scripts/vpn-status.py`), šedý = vypnuto, modrý = IP skrytá | okno VPN |
| tlačítko vypnutí | powermenu |

Odkazy na aplikace v liště nejsou, jsou v Island panelu v sekci Quick apps.

## Island panel

Jeden program v Pythonu (GTK 3 + gtk-layer-shell), který po přihlášení spouští `hyprland.conf`. Všechna jeho okna vypadají jako ostrůvky ve Waybaru.

| Kde | Co se stane |
|---|---|
| kurzor na horním okraji uprostřed, nebo `Super + D` | vyjede panel se záložkami Dashboard, Media, Performance, Apps |
| kurzor krátce na pravém okraji | posuvníky hlasitosti a jasu (klik na kolečko = ztlumit) |
| kurzor asi vteřinu na pravém okraji | ovládací centrum: oznámení, otevřená okna, rychlé přepínače, zamknutí, uspání, odhlášení, restart, vypnutí |
| klik na Wi-Fi / Bluetooth / štít v liště | okno Wi-Fi, Bluetooth a VPN |
| `Super + W` | přepínač tapet ze složky `~/Pictures/wallpapers` |

Když je obrazovka zamčená, žádné okno panelu se nevysune.

**Záložky panelu:**

- **Dashboard:** počasí (wttr.in), uživatel a doba běhu, hodiny, kalendář, ukazatele CPU / RAM / disk s procenty, právě hrající skladba (obal alba se točí jako deska).
- **Media:** velký přehrávač pro to, co právě hraje (Spotify, video v prohlížeči… přes MPRIS): točící se deska, průběh s posunem kliknutím, shuffle, předchozí, play, další, repeat. Ostatní přehrávače jsou malé dole pod „Also open", klik na ně je prohodí (aktuální se pozastaví, kliknutý začne hrát).
- **Performance:** karty CPU a GPU (název, teplota, vytížení), baterie, úložiště (klik na název disku přepíná disky), síť s grafem a celkovým přenosem, paměť.
- **Apps:** Quick apps nahoře (pravý klik na aplikaci v seznamu ji přidá nebo odebere), pod tím všechny aplikace s hledáním. Jména a ikony Quick apps se dají změnit v `QUICK_APP_LOOK` na začátku `panel.py` (ikony bere i z balíčku `papirus-icon-theme`).

**Okno Wi-Fi / Bluetooth / VPN:** seznam sítí a zařízení, připojení, heslo, zapomenutí sítě, párování. Okno neblokuje klávesnici, psát se do něj dá až po kliknutí. Záložka VPN je popsaná níže.

**Přepínač tapet:** šipky vybírají, Enter nebo klik na prostřední náhled tapetu nastaví, mezerník ji nastaví bez zavření, psaní hledá podle názvu, Esc zavírá. Podsložky se v liště objeví jako filtry. Nová tapeta se rozroste v kruhu z pravého horního rohu. Vybraná tapeta se pamatuje v `~/.local/state/island-panel/wallpaper` a po přihlášení ji odtud načte řádek `exec-once = swaybg …` v `hyprland.conf`. Animované GIFy a videa fungují jen s programem `mpvpaper` (ze zdrojáků), bez něj se GIF nastaví jako nehybný obrázek.

**Nastavení** (velikosti, zpoždění, složka s tapetami, město pro počasí, Quick apps, rychlost točení desky `SPIN_SECONDS`) je na začátku `panel.py`, vzhled ve `style.css` (načítá se sám po uložení). Po úpravě `panel.py` je potřeba panel restartovat:

```bash
/usr/bin/python3 ~/.config/island-panel/panel.py --quit; sleep 1
hyprctl dispatch exec "/usr/bin/python3 ~/.config/island-panel/panel.py"
```

Další přepínače programu: `--toggle`, `--apps`, `--wifi`, `--bluetooth`, `--vpn`, `--wallpapers`, `--wallpaper-next`, `--wallpaper-prev`, `--wallpaper-random`, `--side`, `--center`.

Panel potřebuje balíčky `python3-gobject`, `gtk3`, `gtk-layer-shell`, `swaybg`, `NetworkManager` (`nmcli`) a `bluez` (`bluetoothctl`).

## VPN (Proton VPN Free)

VPN běží přes NetworkManager jako WireGuard profily, takže nepotřebuje aplikaci Proton. Ovládá se v okně VPN (klik na štít v liště):

- přepínač nahoře zapne nebo vypne VPN (připojí server s automatickým startem, jinak ten s nejlepší odezvou),
- karta ukazuje aktuální veřejnou IP a město, během připojování „Connecting…" s kolečkem,
- servery jsou seskupené podle zemí v rozbalovacích skupinách s odezvou v ms,
- **Fastest** připojí server s nejlepší odezvou, **Auto-start** připojí server sám po přihlášení.

Free plán: data bez omezení, servery v Nizozemsku, Polsku, Rumunsku, Norsku, Kanadě, Japonsku, Singapuru a USA, jedno připojení najednou.

**Přidání serverů:** na `account.protonvpn.com` → Downloads → WireGuard configuration → platforma GNU/Linux → „Konfigurace bezplatného serveru" → u serveru Vytvořit a stáhnout. Soubory `wg-NL-FREE-103.conf` z `~/Downloads` se naimportují takto (jméno se zkrátí na `proton-nl103`, Linux dovolí nejvýš 15 znaků):

```bash
mkdir -p ~/.local/share/island-vpn && chmod 700 ~/.local/share/island-vpn
cd ~/Downloads
for f in wg-*-FREE-*.conf; do
  [[ "$f" =~ ^wg-([A-Za-z]{2})-FREE-([0-9]+)\.conf$ ]] || continue
  n="proton-${BASH_REMATCH[1],,}${BASH_REMATCH[2]}"
  cp "$f" "/tmp/$n.conf" && nmcli connection import type wireguard file "/tmp/$n.conf" && rm "/tmp/$n.conf"
  nmcli connection down "$n"; nmcli connection modify "$n" connection.autoconnect no
  mv "$f" ~/.local/share/island-vpn/"$n".conf && chmod 600 ~/.local/share/island-vpn/"$n".conf
done
```

Soubory `.conf` obsahují soukromý klíč. Patří jen do `~/.local/share/island-vpn` (panel z nich čte adresu serveru pro měření odezvy), **nikdy ne do tohoto repozitáře**.

## Zamykací obrazovka (hyprlock + hypridle)

`hypr/.config/hypr/lock/lock.py` vygeneruje pro každý monitor nastavení hyprlocku (velikosti podle rozlišení a škálování) a hyprlock spustí. Vlevo počasí pro Prahu a výpis systému, uprostřed hodiny, datum, fotka uživatele a heslo, vpravo poslední oznámení (jen aplikace a nadpis, ne text zpráv). Při zamknutí se pozastaví všechno přehrávání.

- Zamyká `Super + L`, tlačítko Lock v ovládacím centru, `hypridle` po 10 minutách nečinnosti a před uspáním. Po 15 minutách se vypne obrazovka. Časy jsou v `hypridle.conf`.
- Město pro počasí: `WEATHER_CITY` a `WEATHER_LABEL` v `lock/lockinfo.py`.
- Otisk prstu: když je nahraný (`fprintd-enroll`), zámek jde odemknout heslem i prstem.
- Ověřování hesla jde přes `/etc/pam.d/hyprlock` (jen heslo, otisk řeší hyprlock sám):

```
#%PAM-1.0
auth       include      password-auth
account    include      password-auth
```

- Kdyby se zámek zasekl: `Ctrl + Alt + F3`, přihlásit se, `pkill -USR1 hyprlock` a zpět `Ctrl + Alt + F1` (nebo F2).

Na Fedoře 43 a novější: `sudo dnf install hyprlock hypridle`. Fedora 42 už podporu nemá a COPR balíčky pro ni nejsou, tam se hyprlock 0.9.2 a hypridle 0.1.7 sestavují ze zdrojáků (`github.com/hyprwm`) do `/opt/island-hypr`.

Do `hyprland.conf` patří:

```ini
exec-once = hypridle
bind = $mainMod, L, exec, loginctl lock-session
misc:allow_session_lock_restore = true
```

## Správce souborů v terminálu (Yazi)

[Yazi](https://yazi-rs.github.io) se třemi sloupci, náhledy obrázků, videí a PDF přímo v kitty a vzhledem Island (zaoblené pilulky, barvy podle druhu souboru).

- `y`: spustí Yazi; po ukončení zůstane terminál ve složce, kde jsi skončil
- `ys`: Yazi jako root se stejným vzhledem, pro složky s „Permission denied" (opatrně, smí mazat i systémové soubory)

| Klávesa | Akce |
|---|---|
| `h j k l` / šipky, `Enter` | pohyb, otevřít |
| `Space` | označit |
| `y` / `x` / `p` | kopírovat / vyjmout / vložit |
| `d` / `D` | do koše / smazat natrvalo |
| `a` / `r` | nový soubor (složka končí `/`) / přejmenovat |
| `/`, `s`, `S` | hledat ve složce, hledat soubory (fd), hledat v obsahu (ripgrep) |
| `z` | skok do často používané složky (zoxide) |
| `.` / `~` / `q` | skryté soubory / nápověda / konec |

Na Fedoře 42 se Yazi stahuje jako hotový program z `github.com/sxyazi/yazi/releases` do `~/.local/bin`, jinak `sudo dnf copr enable lihaohong/yazi && sudo dnf install yazi`. Pomocníci pro náhledy: `ffmpeg-free 7zip jq poppler-utils fd-find ripgrep fzf zoxide ImageMagick wl-clipboard`.

## Poznámky k nastavení

**Displej se škálováním 2×.** Aplikace běžící přes XWayland by byly rozmazané, proto je v `hyprland.conf` nastaveno:

```ini
xwayland {
    force_zero_scaling = true
}
```

XWayland aplikace jsou díky tomu ostré, ale v poloviční velikosti, proto se používají verze, které běží nativně: `rofi-wayland` místo `rofi`, Spotify z Flatpaku, VSCodium s `--ozone-platform=wayland` (nastavené v `APP_COMMANDS` v `panel.py`).

**Externí monitor.** Monitor na HDMI má v `hyprland.conf` vlastní řádek `monitor = HDMI-A-1, 1920x1080@144, auto, 1`. Pro jiný monitor je potřeba ho upravit.

**Spotify.** Flatpak `com.spotify.Client` upravený přes [Spicetify](https://spicetify.app) (téma `text`, schéma `Spotify`), průhlednost okna nastavuje `windowrulev2 = opacity …` v `hyprland.conf`. Spouští se přes `~/.local/bin/spotify-launch` (příkaz `spotify`, Quick apps i rofi), který:

- smaže zaseknuté zámky `Singleton*`, když Spotify po pádu nejde spustit,
- po aktualizaci Spotify znovu použije Spicetify; když nová verze potřebuje práva, otevře kitty a požádá o heslo.

Ručně: `spicetify restore backup apply`. Původní vzhled vrátí `spicetify restore`.

**Discord.** Vesktop (`dev.vencord.Vesktop`) s tématem [system24](https://refact0r.github.io/system24/build/system24.css), průhledný přes `windowrulev2` v `hyprland.conf`. Všude se jmenuje „Discord" s ikonou Discordu díky souboru v `local/.local/share/applications`.

**Přejmenované aplikace.** `local/.local/share/applications` obsahuje vlastní kopie `.desktop` souborů (Brave → „Brave", Vesktop → „Discord", ikona Spotify). Mají přednost před systémovými, takže platí v rofi, panelu i Quick apps.

**Programy z terminálu.** Grafické programy (`kwrite`, `kate`, `dolphin`, `okular`, `gwenview`, `ark`, `codium`…) se z terminálu spouštějí odpojené, takže zavření terminálu je neukončí. Cokoliv jiného: `detach program`.

**Kurzor v kitty.** `cursor_trail` v `kitty.conf` dělá při skoku kurzoru šmouhu (od kitty 0.37).

**Česká klávesnice.** Číselná řada bez Shiftu nepíše číslice, takže zkratky typu `Super + 1` nemusí fungovat. Řešením je v `hyprland.conf` použít kódy kláves `code:10` až `code:19` místo `1` až `0`.

**Okno „Authentication required" (klíčenka).** Vyskakuje, když má klíčenka GNOME Keyring jiné heslo než uživatelský účet. Oprava: smazat `~/.local/share/keyrings/login.keyring` a znovu se přihlásit.

**Fedora 42.** Podpora skončila a repozitář `solopasha/hyprland` (zdroj Hyprlandu) už neexistuje. Před přechodem na Fedoru 44 je potřeba zapnout `sdegler/hyprland` a vypnout mrtvé COPR repozitáře.

## Nainstalované programy

Samotné programy v repozitáři nejsou, jen jejich seznamy ve složce `system/`:

| Soubor | Obsah |
|---|---|
| `system/packages.txt` | balíčky ručně nainstalované přes `dnf` |
| `system/copr.txt` | přidané COPR repozitáře |
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
- XAMPP (`/opt/lampp`), Mailpit, Postman (`~/Apps/Postman`)
- nástroje z `pip` (`~/.local/bin`) a `cargo` (`~/.cargo/bin`)
- Spicetify (`~/.spicetify`) a jeho témata, viz Obnova
- Yazi (`cargo install --locked yazi-fm yazi-cli`)
- hyprlock a hypridle: z COPR `lionheartp/Hyprland` (`sudo dnf install hyprlock hypridle`)
- `mpvpaper` pro animované tapety (volitelné, ze zdrojáků `GhostNaN/mpvpaper`)
- VPN profily (naimportovat znovu ze záloh v `~/.local/share/island-vpn`, ty nejsou v repozitáři)

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
sudo dnf install papirus-icon-theme hyprlock hypridle
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
for d in */; do case "$d" in system/|spicetify/) ;; *) stow "$d" ;; esac; done
fc-cache -f
update-desktop-database ~/.local/share/applications
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

Kdyby `backup apply` spadlo uprostřed (typicky kvůli právům), Spotify zůstane rozbité. Oprava: přeinstalovat Spotify (`flatpak uninstall` a `flatpak install`), znovu nastavit práva, pustit `spicetify clear` a `spicetify backup apply`.

### 6. Zámek a Discord

- `/etc/pam.d/hyprlock` podle sekce Zamykací obrazovka.
- Vesktop: v nastavení Vencordu → Themes → Online Themes vložit `https://refact0r.github.io/system24/build/system24.css`.

### 7. Po obnově

- Neovim si pluginy stáhne sám při prvním spuštění.
- V `hyprland.conf` jsou cesty s `/home/joncl/`. Při jiném uživatelském jménu je potřeba je upravit.
- Zsh jako výchozí shell: `chsh -s $(which zsh)`
- Barvy Dolphinu: `plasma-apply-colorscheme Island`
- Tapeta: `Super + W`, do té doby se použije `~/Pictures/wallpapers/my_name.jpg`.

## Co v repozitáři záměrně není

- SSH a GPG klíče (`~/.ssh`, `~/.gnupg`), zálohují se zvlášť mimo GitHub
- VPN klíče (`~/.local/share/island-vpn`, profily v `/etc/NetworkManager/system-connections`)
- historie shellu, profily prohlížečů, přihlašovací údaje aplikací
- cache a data aplikací (`~/.cache`, zbytek `~/.local/share`)
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

Před každým přidáním je dobré zkontrolovat, že soubory neobsahují hesla, tokeny ani klíče:

```bash
grep -rniE "token|password|passwd|secret|api_key|privatekey" ~/dotfiles --exclude-dir=.git
```

## Přihlašovací obrazovka (SDDM)

Vlastní téma SDDM `island` ve složce `login/`:

- po zapnutí jen velké hodiny na tapetě, datum vlevo nahoře, uspat / restart / vypnout vpravo nahoře
- po stisku klávesy nebo kliknutí rozmazané pozadí, fotka účtu, jméno, heslo
- vpravo dole výběr prostředí (Hyprland, GNOME…); SDDM si pamatuje poslední volbu
- pozadí je vždy aktuální tapeta z plochy: `island-sddm-bg` ji při každé změně tapety (systemd `island-sddm-bg.path`) zkopíruje a připraví i rozmazanou verzi

Instalace (zeptá se na heslo kvůli sudo, na konci nabídne přepnutí z GDM na SDDM):

```bash
bash ~/dotfiles/login/install.sh
```

Návrat ke GDM: `sudo systemctl disable sddm && sudo systemctl enable gdm`

Pozor: SDDM čte `/etc/sddm.conf.d/*.conf` podle abecedy a poslední vyhrává, proto je nastavení tématu v `zz-island.conf`
(jinak ho přepíše `kde_settings.conf` od KDE).
