#!/usr/bin/env bash

# Display the 16 named ANSI colors and the complete xterm 256-color palette.

set -u

RESET=$'\033[0m'

print_named_color() {
  local palette_number="$1"
  local foreground_code="$2"
  local background_code="$3"
  local name="$4"

  printf '  \033[48;5;%dm    %s  %3d      %3d  %3d  %s\n' \
    "$palette_number" "$RESET" "$palette_number" "$foreground_code" \
    "$background_code" "$name"
}

print_named_colors() {
  printf '%s\n' 'Predefined ANSI colors'
  printf '%s\n' '  Swatch  Palette   FG   BG   Name'

  printf '\n%s\n' 'Neutral'
  print_named_color 0  30  40  'Black'
  print_named_color 8  90 100  'Bright Black (Gray)'
  print_named_color 7  37  47  'White (Light Gray)'
  print_named_color 15 97 107  'Bright White'

  printf '\n%s\n' 'Red family'
  print_named_color 1  31  41  'Red'
  print_named_color 9  91 101  'Bright Red'

  printf '\n%s\n' 'Green family'
  print_named_color 2  32  42  'Green'
  print_named_color 10 92 102  'Bright Green'

  printf '\n%s\n' 'Yellow family'
  print_named_color 3  33  43  'Yellow'
  print_named_color 11 93 103  'Bright Yellow'

  printf '\n%s\n' 'Blue family'
  print_named_color 4  34  44  'Blue'
  print_named_color 12 94 104  'Bright Blue'

  printf '\n%s\n' 'Magenta family'
  print_named_color 5  35  45  'Magenta'
  print_named_color 13 95 105  'Bright Magenta'

  printf '\n%s\n' 'Cyan family'
  print_named_color 6  36  46  'Cyan'
  print_named_color 14 96 106  'Bright Cyan'
}

# Set REPLY to a family number for an xterm palette index.
classify_color() {
  local number="$1"
  local red green blue maximum minimum delta hue
  local component levels=(0 95 135 175 215 255)

  case "$number" in
    0|7|8|15|16|231|23[2-9]|24[0-9]|25[0-5]) REPLY=0; return ;;
    1|9)   REPLY=1; return ;;
    3|11)  REPLY=3; return ;;
    2|10)  REPLY=4; return ;;
    6|14)  REPLY=5; return ;;
    4|12)  REPLY=6; return ;;
    5)     REPLY=7; return ;;
    13)    REPLY=8; return ;;
  esac

  component=$((number - 16))
  red=${levels[$((component / 36))]}
  green=${levels[$(((component / 6) % 6))]}
  blue=${levels[$((component % 6))]}

  maximum=$red
  (( green > maximum )) && maximum=$green
  (( blue > maximum )) && maximum=$blue
  minimum=$red
  (( green < minimum )) && minimum=$green
  (( blue < minimum )) && minimum=$blue
  delta=$((maximum - minimum))

  if (( delta == 0 )); then
    REPLY=0
    return
  fi

  if (( maximum == red )); then
    hue=$((60 * (green - blue) / delta))
  elif (( maximum == green )); then
    hue=$((120 + 60 * (blue - red) / delta))
  else
    hue=$((240 + 60 * (red - green) / delta))
  fi
  (( hue < 0 )) && hue=$((hue + 360))

  if (( hue < 15 || hue >= 345 )); then
    REPLY=1
  elif (( hue < 45 )); then
    REPLY=2
  elif (( hue < 70 )); then
    REPLY=3
  elif (( hue < 165 )); then
    REPLY=4
  elif (( hue < 195 )); then
    REPLY=5
  elif (( hue < 255 )); then
    REPLY=6
  elif (( hue < 285 )); then
    REPLY=7
  else
    REPLY=8
  fi
}

print_palette_entry() {
  local number="$1"
  printf '\033[48;5;%dm    %s %3d  ' "$number" "$RESET" "$number"
}

print_256_color_palette() {
  local family number count
  local family_names=(
    'Grayscale and neutral'
    'Red'
    'Orange and brown'
    'Yellow and gold'
    'Green'
    'Cyan and teal'
    'Blue'
    'Purple and violet'
    'Magenta and pink'
  )
  local palette_families=()

  for ((number = 0; number < 256; number++)); do
    classify_color "$number"
    palette_families[$number]=$REPLY
  done

  printf '\n\n%s\n' 'xterm 256-color palette'
  printf '%s\n' 'Each swatch is followed by its palette number (0-255).'

  for ((family = 0; family < ${#family_names[@]}; family++)); do
    printf '\n%s\n' "${family_names[$family]}"
    count=0
    for ((number = 0; number < 256; number++)); do
      if (( palette_families[number] == family )); then
        print_palette_entry "$number"
        count=$((count + 1))
        if (( count % 8 == 0 )); then
          printf '\n'
        fi
      fi
    done
    if (( count % 8 != 0 )); then
      printf '\n'
    fi
  done
}

print_named_colors
print_256_color_palette
printf '%s' "$RESET"
