#!/bin/sh
# usage: render.sh <outdir> <command...>   (command renders one url: "$@" <url> -o <out>)
out=$1; shift
while read name url; do
  for theme in ${THEMES:-RenderOceanBlueColor RenderXReference}; do
    "$@" "$url" --sessionType guest --simpleLog --limit 2 --theme $theme --ffmpegAdditonalOption "-preset ultrafast" -o "$out/${name}_${theme}_{count}.{if-type:png:mp4:json:}" >> "$out/log.txt" 2>&1 || echo "FAIL $name $theme" >> "$out/log.txt"
  done
done < "${URLS:-/root/workspace/tools/og_compare/urls.txt}"
echo done >> "$out/log.txt"
