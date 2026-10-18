# Systémové soubory (kopie)

Nejsou napojené odkazem, jen uložené pro přehled a obnovu na novém počítači:

| soubor | kam patří | k čemu |
|---|---|---|
| `etc/sddm.conf.d/zz-island.conf` | `/etc/sddm.conf.d/` | téma přihlašovací obrazovky, pamatuje poslední prostředí |
| `etc/pam.d/hyprlock` | `/etc/pam.d/` | odemykání zamykací obrazovky heslem |
| `etc/sudoers.d/island-drop-caches` | `/etc/sudoers.d/` (práva 440) | tlačítko Clear u Cache v panelu bez hesla |
| `usr-local-bin/island-drop-caches` | `/usr/local/bin/` (práva 755) | uvolnění mezipaměti |

Přihlašovací obrazovku nainstaluje celou `bash ~/dotfiles/login/install.sh`.
