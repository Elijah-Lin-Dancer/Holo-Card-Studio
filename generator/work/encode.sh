#!/bin/bash
set -e
cd /home/user/Doubao/chats/38444574205007618/holo-lab/generator
for id in messi-demo mj-demo; do
  dir=work/preview-frames/${id%-demo}
  out=/home/user/Doubao/chats/38444574205007618/holo-lab/gallery/cards/$id/preview.webm
  ffmpeg -y -framerate 24 -i "$dir/frame_%04d.png" -c:v libvpx-vp9 -b:v 0 -crf 42 -pix_fmt yuv420p -an "$out" 2>/dev/null
  sz=$(du -k "$out" | cut -f1)
  echo "$id → $out (${sz}KB)"
done
