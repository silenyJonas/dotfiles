-- Caelestia shell v tvém Hyprlandu. Načítá se jen v režimu Caelestia (shell-switch).
-- Tvoje zkratky z hyprland.lua platí dál; tady jsou jen ty, které ovládají Caelestii.
local g = hl.dsp.global

hl.on("hyprland.start", function()
    hl.exec_cmd("caelestia shell -d")
    hl.exec_cmd("wl-paste --type text --watch cliphist store")    -- historie schránky (Super+Shift+V)
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
end)

-- tvoje klávesy, které dřív otevíraly Island panel
hl.bind("SUPER + D", g("caelestia:dashboard"))              -- přehled: kalendář, počasí, média, výkon
hl.bind("SUPER + A", g("caelestia:launcher"))               -- aplikace (oblíbené nahoře)
hl.bind("SUPER + W", g("caelestia:nexus"))                  -- nastavení Caelestie a tapety
hl.bind("SUPER + X", g("caelestia:session"))                -- vypnout / restart / odhlásit
hl.bind("SUPER + O", g("caelestia:session"))
hl.bind("SUPER + L", g("caelestia:lock"))                   -- zámek obrazovky Caelestie
hl.bind("XF86MonBrightnessUp",   g("caelestia:brightnessUp"),   { locked = true })
hl.bind("XF86MonBrightnessDown", g("caelestia:brightnessDown"), { locked = true })

-- navíc z Caelestie (klávesy, které jsi nepoužíval)
hl.bind("SUPER + SUPER_L", g("caelestia:launcher"), { release = true })  -- jen Super = aplikace
hl.bind("SUPER + K", g("caelestia:showall"))                -- všechny panely najednou
hl.bind("SUPER + U", g("caelestia:utilities"))              -- rychlé přepínače (Wi-Fi, BT, Game mode, VPN…)
hl.bind("SUPER + SHIFT + N", g("caelestia:sidebar"))        -- oznámení
hl.bind("CTRL + ALT + C", g("caelestia:clearNotifs"), { locked = true })
hl.bind("CTRL + ALT + Delete", g("caelestia:session"))
hl.bind("SUPER + SHIFT + V", hl.dsp.exec_cmd("pkill fuzzel || caelestia clipboard"))      -- historie schránky
hl.bind("SUPER + Period", hl.dsp.exec_cmd("pkill fuzzel || caelestia emoji -p"))          -- emoji
hl.bind("SUPER + SHIFT + ALT + S", g("caelestia:screenshotFreeze"))                       -- snímek se zmrazením
hl.bind("CTRL + ALT + R", hl.dsp.exec_cmd("caelestia record"))                            -- nahrávání obrazovky
hl.bind("SUPER + SHIFT + ALT + R", hl.dsp.exec_cmd("caelestia record -r"))                -- nahrávání výřezu
-- tvůj Gaming (procesor + grafika přes island-gaming), zapnout/vypnout
hl.bind("SUPER + G", hl.dsp.exec_cmd(
    "if [ -f /run/island-gaming ]; then sudo -n /usr/local/bin/island-gaming off && notify-send -a Gaming 'Gaming vypnuto'; " ..
    "else sudo -n /usr/local/bin/island-gaming on && notify-send -a Gaming 'Gaming zapnuto' 'procesor bez horkých turbo stupňů, grafika drží takt'; fi"))

-- animace panelů Caelestie
hl.layer_rule({ match = { namespace = "caelestia-(border-exclusion|area-picker)" }, no_anim = true })
hl.layer_rule({ match = { namespace = "caelestia-(drawers|background)" }, animation = "fade" })
