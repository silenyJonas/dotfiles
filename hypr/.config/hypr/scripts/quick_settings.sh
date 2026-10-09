#!/bin/bash

# Rychlé volby pro Rofi/Wofi
OPTIONS="Jas nahoru\nJas dolu\nHlasitost nahoru\nHlasitost dolu\nPřepnout Bluetooth\nSpráva Sítě"

# Spuštění Wofi s volbami
CHOICE=$(echo -e "$OPTIONS" | wofi --show dmenu -p "Rychlé volby")

# Reakce na výběr
case "$CHOICE" in
    "Jas nahoru")
        # ZDE POUŽIJTE SVŮJ PŘÍKAZ PRO ZVÝŠENÍ JASU (např. 'brightnessctl')
        brightnessctl set +5% 
        ;;
    "Jas dolu")
        brightnessctl set 5%-
        ;;
    "Hlasitost nahoru")
        pactl set-sink-volume @DEFAULT_SINK@ +5%
        ;;
    "Hlasitost dolu")
        pactl set-sink-volume @DEFAULT_SINK@ -5%
        ;;
    "Přepnout Bluetooth")
        # Zapne/vypne Bluetooth (vyžaduje 'bluetoothctl')
        STATUS=$(bluetoothctl show | grep "Powered" | cut -d ' ' -f 2)
        if [[ $STATUS == "yes" ]]; then
            bluetoothctl power off
        else
            bluetoothctl power on
        fi
        ;;
    "Správa Sítě")
        nm-connection-editor &
        ;;
    *)
        # Nedělat nic
        ;;
esac
