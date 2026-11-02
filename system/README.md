# Nový počítač (Arch)

Na čerstvém Arch Linuxu s Hyprlandem, přihlášený jako svůj uživatel, s internetem:

```bash
curl -fsSLo ~/arch-restore.sh https://raw.githubusercontent.com/silenyJonas/dotfiles/main/system/arch-restore.sh
bash ~/arch-restore.sh
```

Obnoví všechno: balíčky (pacman, AUR, Flatpak), propojení konfigurací (stow), přihlašovací obrazovku,
systémové drobnosti, optimalizace a nakonec Caelestia shell (`caelestia/caelestia-mix.sh`).
Volitelně potom `bash ~/dotfiles/system/arch-extras.sh` (virt-manager, ArtCraft). Přehled zkratek: `help`.

# Systémové soubory (kopie)

Nejsou napojené odkazem, jen uložené pro přehled a obnovu na novém počítači:

| soubor | kam patří | k čemu |
|---|---|---|
| `etc/sddm.conf.d/zz-island.conf` | `/etc/sddm.conf.d/` | téma přihlašovací obrazovky, pamatuje poslední prostředí |
| `etc/pam.d/hyprlock` | `/etc/pam.d/` | odemykání zamykací obrazovky heslem |
| `etc/sudoers.d/island-drop-caches` | `/etc/sudoers.d/` (práva 440) | uvolnění mezipaměti bez hesla |
| `usr-local-bin/island-drop-caches` | `/usr/local/bin/` (práva 755) | uvolnění mezipaměti |
| `usr-local-bin/island-gaming` | `/usr/local/bin/` (práva 755, sudoers bez hesla) | Gaming režim (Super+G): procesor a grafika |

Přihlašovací obrazovku nainstaluje celou `bash ~/dotfiles/login/install.sh`.
