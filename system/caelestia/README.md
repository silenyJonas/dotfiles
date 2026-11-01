# Caelestia shell (místo Island panelu)

Lišta, panely, spouštěč aplikací, oznámení a zámek obrazovky jsou z
[Caelestia shell](https://github.com/caelestia-dots/shell). Hyprland config (zkratky, okna, plochy) je vlastní,
Caelestia v něm jen běží.

* `caelestia/.config/caelestia/shell.json`: nastavení shellu (stow balíček `caelestia`)
* `caelestia/.config/caelestia/cli.json`: Caelestia nemění barvy GTK, terminálu, Vesktopu, Spotify…
* `hypr/.config/hypr/caelestia.lua`: zkratky pro Caelestii a její spuštění (načítá hyprland.lua)
* `system/caelestia/caelestia-mix.sh`: instalace na novém počítači + úpravy shellu
  (tlačítko disku, karta GPU pro Intel, panel vpravo, vypínací menu)
* `system/caelestia/Files.qml`: tlačítko disku v liště (otevře Thunar)

Nový počítač (po `arch-restore.sh`):  `bash ~/dotfiles/system/caelestia/caelestia-mix.sh`
Po aktualizaci Caelestie (paru) stejný příkaz znovu: obnoví úpravy shellu.
