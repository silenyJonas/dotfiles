-- Hyprland config (Lua, Hyprland 0.56+). Převedeno 1:1 z hyprland.conf, chování je stejné.
-- Wiki: https://wiki.hypr.land/Configuring/Start/
-- Starý config zůstává jako hyprland.conf; když tenhle soubor smažeš (nebo přejmenuješ),
-- Hyprland po novém přihlášení použije zase ten starý.

------------------
---- MONITORS ----
------------------
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
hl.monitor({ output = "HDMI-A-1", mode = "1920x1080@144", position = "auto", scale = "1" })


---------------------
---- MY PROGRAMS ----
---------------------
local terminal    = "kitty"
local fileManager = "thunar"
local menu        = "wofi --show drun"   -- (nepoužívá se, Super+R je rofi)
local mainMod     = "SUPER"


---------------------
---- SCREENSHOTS ----
---------------------
-- Výběr oblasti a otevření v editoru Swappy (podobně jako Win + Štěpátko)
hl.bind(mainMod .. " + S",             hl.dsp.exec_cmd('grim -g "$(slurp)" - | swappy -f -'))
-- Celá obrazovka a otevření v editoru Swappy
hl.bind(mainMod .. " + Print",         hl.dsp.exec_cmd("grim - | swappy -f -"))
-- Výběr oblasti zkopírovaný rovnou do schránky (bez editoru, ihned do Ctrl + V)
hl.bind(mainMod .. " + SHIFT + S",     hl.dsp.exec_cmd('grim -g "$(slurp)" - | wl-copy'))
-- Celá obrazovka zkopírovaná rovnou do schránky
hl.bind(mainMod .. " + SHIFT + Print", hl.dsp.exec_cmd("grim - | wl-copy"))


---------------------------
---- PRAVIDLA PRO OKNA ----
---------------------------
-- Codium: průhlednost (aktivní / neaktivní)
hl.window_rule({ match = { class = "^(codium|VSCodium|com\\.visualstudio\\.CodeOSS)$" }, opacity = "0.88 override 0.82 override" })
hl.window_rule({ match = { class = "^(org.kde.dolphin)$" }, opacity = "0.82 override 0.82" })
-- Semi-transparentní okno pro Yazi
hl.window_rule({ match = { class = "^(Alacritty)$", title = "^Yazi:.*" }, opacity = "0.9 override 0.9" })
-- discord velikost
hl.window_rule({ match = { class = "^(discord)$" }, size = "1280 720" })


-------------------
---- AUTOSTART ----
-------------------
hl.on("hyprland.start", function()
    -- tapeta (vybraná v přepínači tapet, jinak výchozí)
    hl.exec_cmd('swaybg -i "$(cat ~/.local/state/island-panel/wallpaper 2>/dev/null || echo ~/Pictures/wallpapers/my_name.jpg)" -m fill')
    hl.exec_cmd("/usr/libexec/lxqt-policykit-agent")
    -- Island panel a lišta
    hl.exec_cmd("/usr/bin/python3 ~/.config/island-panel/panel.py")
    -- zamykání a zhasínání (hypridle)
    hl.exec_cmd("hypridle")
    -- plochy bez děr uprostřed (zavřené okno -> další plochy se posunou)
    hl.exec_cmd("python3 ~/.config/hypr/scripts/workspaces.py daemon")
end)


-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Kitty")


-----------------------
---- LOOK AND FEEL ----
-----------------------
hl.config({
    general = {
        gaps_in  = 5,
        gaps_out = 10,
        border_size = 1,
        no_focus_fallback = true,
        col = {
            active_border   = "rgba(ffffff59)",
            inactive_border = "rgba(ffffff14)",
        },
        resize_on_border = false,
        allow_tearing    = false,
        layout = "dwindle",
    },

    decoration = {
        rounding       = 10,
        rounding_power = 2,
        active_opacity   = 1.0,
        inactive_opacity = 1.0,
        shadow = {
            enabled      = true,
            range        = 4,
            render_power = 3,
            color        = "rgba(1a1a1aee)",
        },
        blur = {
            enabled  = true,
            size     = 5,
            passes   = 2,
            vibrancy = 0.1696,
        },
    },

    animations = {
        enabled = true,
    },

    dwindle = {
        preserve_split = true,
    },

    master = {
        new_status = "master",
    },

    misc = {
        force_default_wallpaper = -1,
        disable_hyprland_logo   = false,
        allow_session_lock_restore = true,
    },

    xwayland = {
        force_zero_scaling = true,
    },

    input = {
        kb_layout  = "cz",
        kb_variant = "",
        kb_model   = "",
        kb_options = "",
        kb_rules   = "",
        follow_mouse = 1,
        sensitivity  = 0,
        touchpad = {
            natural_scroll = true,
        },
    },

    -- Super + šipky zůstávají na svém monitoru, fokus nepřeskakuje na vedlejší
    binds = {
        window_direction_monitor_fallback = false,
    },
})

-- křivky a animace (stejné jako dřív)
hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1}  } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1}  } })
hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1}     } })
hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1}  } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}   } })

hl.animation({ leaf = "global",        enabled = true, speed = 10,   bezier = "default" })
hl.animation({ leaf = "border",        enabled = true, speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows",       enabled = true, speed = 4.79, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn",     enabled = true, speed = 4.1,  bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut",    enabled = true, speed = 1.49, bezier = "linear",       style = "popin 87%" })
hl.animation({ leaf = "fadeIn",        enabled = true, speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut",       enabled = true, speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade",          enabled = true, speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers",        enabled = true, speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn",      enabled = true, speed = 2.5,  bezier = "easeOutQuint", style = "popin 85%" })
hl.animation({ leaf = "layersOut",     enabled = true, speed = 1.5,  bezier = "linear",       style = "popin 90%" })
hl.animation({ leaf = "fadeLayersIn",  enabled = true, speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces",    enabled = true, speed = 3,    bezier = "easeOutQuint", style = "slide" })
hl.animation({ leaf = "zoomFactor",    enabled = true, speed = 7,    bezier = "quick" })


---------------
---- INPUT ----
---------------
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

hl.device({ name = "epic-mouse-v1", sensitivity = -0.5 })


---------------------
---- KEYBINDINGS ----
---------------------
-- Terminál a základní akce
hl.bind(mainMod .. " + Q",         hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exit())
hl.bind(mainMod .. " + C",         hl.dsp.window.close())
hl.bind(mainMod .. " + E",         hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + F",         hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + P",         hl.dsp.window.pseudo())          -- dwindle
hl.bind(mainMod .. " + J",         hl.dsp.layout("togglesplit"))    -- dwindle
hl.bind(mainMod .. " + T",         hl.dsp.exec_cmd(terminal))

-- Launchery a Rofi
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd("$HOME/.config/rofi/launchers/type-2/launcher.sh"))
hl.bind(mainMod .. " + X", hl.dsp.exec_cmd("$HOME/.config/rofi/powermenu/type-2/powermenu.sh"))
hl.bind(mainMod .. " + O", hl.dsp.exec_cmd("$HOME/.config/rofi/powermenu/type-1/powermenu.sh"))

-- Applets (vše type-2)
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd("~/.config/rofi/applets/bin/battery.sh"))
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("~/.config/rofi/applets/bin/brightness.sh"))
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("~/.config/rofi/applets/bin/mpd.sh"))
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("~/.config/rofi/applets/bin/volume.sh"))

-- Fokus: vlevo/vpravo okno vedle, na kraji sousední plocha (workspaces.py); nahoru/dolů okno
hl.bind(mainMod .. " + left",  hl.dsp.exec_cmd("~/.config/hypr/scripts/focus-or-workspace.sh l"))
hl.bind(mainMod .. " + right", hl.dsp.exec_cmd("~/.config/hypr/scripts/focus-or-workspace.sh r"))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- Plochy: Super + 1..0, okno na plochu: Super + Shift + 1..0
for i = 1, 10 do
    local key = i % 10   -- 10 = klávesa 0
    hl.bind(mainMod .. " + " .. key,             hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + SHIFT + " .. key,     hl.dsp.window.move({ workspace = i }))
end

-- Super + kolečko myši: další / předchozí plocha
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Super + levé / pravé tlačítko myši: přesun / změna velikosti okna
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Multimediální klávesy notebooku (fungují i na zamčené obrazovce, při držení se opakují)
hl.bind("XF86AudioRaiseVolume",  hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume",  hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { locked = true, repeating = true })
hl.bind("XF86AudioMute",         hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { locked = true, repeating = true })
hl.bind("XF86AudioMicMute",      hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"),                  { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"),                  { locked = true, repeating = true })

-- Přehrávání (playerctl)
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- Island panel
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd("/usr/bin/python3 ~/.config/island-panel/panel.py --toggle"))
hl.bind(mainMod .. " + A", hl.dsp.exec_cmd("/usr/bin/python3 ~/.config/island-panel/panel.py --apps"))
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd("/usr/bin/python3 ~/.config/island-panel/panel.py --wallpapers"))

-- Zamknout obrazovku
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("loginctl lock-session"))


--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------
-- Ignorovat požadavky aplikací na maximalizaci
hl.window_rule({ match = { class = ".*" }, suppress_event = "maximize" })

-- Oprava přetahování u XWayland oken
hl.window_rule({
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})

hl.layer_rule({ match = { namespace = "waybar" }, blur = true })
hl.layer_rule({ match = { namespace = "waybar" }, ignore_alpha = 0 })
hl.layer_rule({ match = { namespace = "rofi" },   blur = true })
hl.layer_rule({ match = { namespace = "rofi" },   ignore_alpha = 0 })

-- Island panel: animace vysouvacích oken
hl.layer_rule({ match = { namespace = "island-panel-trigger" }, no_anim = true })
hl.layer_rule({ match = { namespace = "island-side" },          animation = "slide right" })
hl.layer_rule({ match = { namespace = "island-side-trigger" },  no_anim = true })
hl.layer_rule({ match = { namespace = "island-center" },        animation = "slide right" })
hl.layer_rule({ match = { namespace = "island-toast" },         animation = "slide right" })

-- Island panel: přepínač tapet
hl.layer_rule({ match = { namespace = "island-wall" }, animation = "fade" })
hl.layer_rule({ match = { namespace = "wallpaper" },   animation = "fade" })
hl.window_rule({ match = { class = "^([Ss]potify)$" }, opacity = "0.9 override 0.9" })
hl.window_rule({ match = { class = "^([Vv]esktop|dev\\.vencord\\.[Vv]esktop)$" }, opacity = "0.9 override 0.9" })
hl.layer_rule({ match = { namespace = "island-wallfx" }, no_anim = true })

hl.window_rule({ match = { class = "^(com\\.obsproject\\.Studio)$" }, opacity = "0.92 override 0.92" })

-- Island lišta: okna z ní vyrůstají, Hyprland do toho nemá přidávat vlastní animace
hl.layer_rule({ match = { namespace = "^(island-bar|island-panel|island-net)$" }, no_anim = true })
hl.layer_rule({ match = { namespace = "^(island-bar|island-panel|island-net)$" }, blur = true })
hl.layer_rule({ match = { namespace = "^(island-bar|island-panel|island-net)$" }, ignore_alpha = 0 })

-- Dialogy (Uložit / Otevřít soubor, potvrzení) plovoucí uprostřed, ne přes celou plochu
local dialogTitle = "^(Save File|Open File|Save As|Open Files?|Open Folder|Select (File|Folder).*|Uložit.*|Otevřít.*|Vybrat.*)$"
hl.window_rule({ match = { modal = true }, float = true })
hl.window_rule({ match = { modal = true }, center = true })
hl.window_rule({ match = { class = "^(xdg-desktop-portal-gtk|xdg-desktop-portal-kde|org.freedesktop.impl.portal.desktop.kde)$" }, float = true })
hl.window_rule({ match = { title = dialogTitle }, float = true })
hl.window_rule({ match = { title = dialogTitle }, size = "(monitor_w*0.55) (monitor_h*0.6)" })
hl.window_rule({ match = { title = dialogTitle }, center = true })
