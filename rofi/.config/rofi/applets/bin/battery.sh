#!/usr/bin/env bash

## Author  : Aditya Shakya (adi1090x)
## Github  : @adi1090x
#
## Applets : Battery

# Import Current Theme
source "$HOME"/.config/rofi/applets/shared/theme.bash
theme="$type/$style"

# Battery Info
# Cte se primo ze systemu (/sys), program acpi neni potreba.
bat="$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -n1)"
battery="Battery ${bat##*BAT}"
status="$(cat "$bat/status" 2>/dev/null)"
percentage="$(cat "$bat/capacity" 2>/dev/null)"

time=""
now="$(cat "$bat/energy_now" 2>/dev/null || cat "$bat/charge_now" 2>/dev/null)"
full="$(cat "$bat/energy_full" 2>/dev/null || cat "$bat/charge_full" 2>/dev/null)"
rate="$(cat "$bat/power_now" 2>/dev/null || cat "$bat/current_now" 2>/dev/null)"
rate="${rate#-}"
if [[ "${rate:-0}" -gt 0 && -n "$now" && -n "$full" ]]; then
    if [[ "$status" == "Discharging" ]]; then
        mins=$(( now * 60 / rate ))
        time=" $(( mins / 60 ))h $(( mins % 60 ))min remaining"
    elif [[ "$status" == "Charging" ]]; then
        mins=$(( (full - now) * 60 / rate ))
        time=" $(( mins / 60 ))h $(( mins % 60 ))min until charged"
    fi
fi
if [[ -z "$time" ]]; then
    time=" ${status:-Unknown}"
fi

# Theme Elements
prompt="$status"
mesg="${battery}: ${percentage}%,${time}"

if [[ "$theme" == *'type-1'* ]]; then
	list_col='1'
	list_row='4'
	win_width='400px'
elif [[ "$theme" == *'type-3'* ]]; then
	list_col='1'
	list_row='4'
	win_width='120px'
elif [[ "$theme" == *'type-5'* ]]; then
	list_col='1'
	list_row='4'
	win_width='500px'
elif [[ ( "$theme" == *'type-2'* ) || ( "$theme" == *'type-4'* ) ]]; then
	list_col='4'
	list_row='1'
	win_width='550px'
fi

# Charging Status
active=""
urgent=""
if [[ $status = *"Charging"* ]]; then
    active="-a 1"
    ICON_CHRG=""
elif [[ $status = *"Full"* || $status = *"Not charging"* ]]; then
    active="-a 1"
    ICON_CHRG=""
else
    [[ "${percentage:-100}" -lt 20 ]] && urgent="-u 1"
    ICON_CHRG=""
fi

# Discharging
ICON_DISCHRG=""
if [[ $percentage -ge 5 ]] && [[ $percentage -le 19 ]]; then
    ICON_DISCHRG=""
elif [[ $percentage -ge 20 ]] && [[ $percentage -le 39 ]]; then
    ICON_DISCHRG=""
elif [[ $percentage -ge 40 ]] && [[ $percentage -le 59 ]]; then
    ICON_DISCHRG=""
elif [[ $percentage -ge 60 ]] && [[ $percentage -le 79 ]]; then
    ICON_DISCHRG=""
elif [[ $percentage -ge 80 ]] && [[ $percentage -le 100 ]]; then
    ICON_DISCHRG=""
fi

# Options
layout=`cat ${theme} | grep 'USE_ICON' | cut -d'=' -f2`
if [[ "$layout" == 'NO' ]]; then
	option_1=" Remaining ${percentage}%"
	option_2=" $status"
	option_3=" Power Manager"
	option_4=" Diagnose"
else
	option_1="$ICON_DISCHRG"
	option_2="$ICON_CHRG"
	option_3=""
	option_4=""
fi

# Rofi CMD
rofi_cmd() {
	rofi -theme-str "window {width: $win_width;}" \
		-theme-str "listview {columns: $list_col; lines: $list_row;}" \
		-theme-str "textbox-prompt-colon {str: \"$ICON_DISCHRG\";}" \
		-dmenu \
		-p "$prompt" \
		-mesg "$mesg" \
		${active} ${urgent} \
		-markup-rows \
		-theme ${theme}
}

# Pass variables to rofi dmenu
run_rofi() {
	echo -e "$option_1\n$option_2\n$option_3\n$option_4" | rofi_cmd
}

# Execute Command
run_cmd() {
	polkit_cmd="pkexec env PATH=$PATH DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY"
	if [[ "$1" == '--opt1' ]]; then
		notify-send -u low " Remaining : ${percentage}%"
	elif [[ "$1" == '--opt2' ]]; then
		notify-send -u low "$ICON_CHRG Status : $status"
	elif [[ "$1" == '--opt3' ]]; then
		xfce4-power-manager-settings
	elif [[ "$1" == '--opt4' ]]; then
		${polkit_cmd} alacritty -e powertop
	fi
}

# Actions
chosen="$(run_rofi)"
case ${chosen} in
    $option_1)
		run_cmd --opt1
        ;;
    $option_2)
		run_cmd --opt2
        ;;
    $option_3)
		run_cmd --opt3
        ;;
    $option_4)
		run_cmd --opt4
        ;;
esac


