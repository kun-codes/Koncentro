#!/usr/bin/env bash

#
# Custom macOS DMG creation script for Koncentro
# Based on original script from Flowkeeper by Constantine Kulak
# https://github.com/kulakowka/flowkeeper
#
# Copyright (c) 2023 Constantine Kulak
# Modifications Copyright (c) 2025 Bishwa Saha
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

set -e

echo "Creating DMG"
mkdir -p ../../dist

create-dmg \
  --volname "Koncentro Installer" \
  --volicon "../../assets/logo.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "Koncentro.app" 200 190 \
  --hide-extension "Koncentro.app" \
  --app-drop-link 600 185 \
  "../../dist/Koncentro.dmg" \
  "../../artifacts/"