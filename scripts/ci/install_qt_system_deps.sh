#!/usr/bin/env bash
# Install native libraries required to import/build PySide6 on headless Linux CI runners.
set -euo pipefail

sudo apt-get update -qq
sudo apt-get install -y -qq \
  libegl1 \
  libgl1 \
  libxkbcommon-x11-0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-randr0 \
  libxcb-render-util0 \
  libxcb-shape0 \
  libxcb-xfixes0
