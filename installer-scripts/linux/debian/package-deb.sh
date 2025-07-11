#!/usr/bin/env bash

#
# Debian package creation script for Koncentro
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

# 1. Get the version
echo "1. Version = $KONCENTRO_VERSION"

# Map architecture names from CI to Debian format
if [ "$ARCHITECTURE" = "x86_64" ]; then
    DEB_ARCHITECTURE="amd64"
elif [ "$ARCHITECTURE" = "aarch64" ]; then
    DEB_ARCHITECTURE="arm64"
else
    DEB_ARCHITECTURE="$ARCHITECTURE"
fi
echo "Detected architecture: $ARCHITECTURE, Debian architecture: $DEB_ARCHITECTURE"

# Export DEB_ARCHITECTURE for debian control file substitution
export DEB_ARCHITECTURE="$DEB_ARCHITECTURE"

# 2. Prepare temp folder
mkdir -p build/deb
cd build
rm -rf deb
mkdir deb
echo "2. Prepared temp folder"

# 3. Copy application files
mkdir -p deb/usr/lib/koncentro

# Create directories for icon sizes
mkdir -p deb/usr/share/icons/hicolor/16x16/apps
mkdir -p deb/usr/share/icons/hicolor/24x24/apps
mkdir -p deb/usr/share/icons/hicolor/32x32/apps
mkdir -p deb/usr/share/icons/hicolor/48x48/apps
mkdir -p deb/usr/share/icons/hicolor/64x64/apps
mkdir -p deb/usr/share/icons/hicolor/128x128/apps
mkdir -p deb/usr/share/icons/hicolor/256x256/apps
mkdir -p deb/usr/share/icons/hicolor/512x512/apps
mkdir -p deb/usr/share/icons/hicolor/1024x1024/apps

# Copy the entire build directory content into the package structure
cp -r ../artifacts/* deb/usr/lib/koncentro/
# Make sure the binary is executable
chmod +x deb/usr/lib/koncentro/koncentro
chmod +x deb/usr/lib/koncentro/mitmdump

# Copy icons of all sizes
cp ../assets/logo_16x16.png deb/usr/share/icons/hicolor/16x16/apps/koncentro.png
cp ../assets/logo_24x24.png deb/usr/share/icons/hicolor/24x24/apps/koncentro.png
cp ../assets/logo_32x32.png deb/usr/share/icons/hicolor/32x32/apps/koncentro.png
cp ../assets/logo_48x48.png deb/usr/share/icons/hicolor/48x48/apps/koncentro.png
cp ../assets/logo_64x64.png deb/usr/share/icons/hicolor/64x64/apps/koncentro.png
cp ../assets/logo_128x128.png deb/usr/share/icons/hicolor/128x128/apps/koncentro.png
cp ../assets/logo_256x256.png deb/usr/share/icons/hicolor/256x256/apps/koncentro.png
cp ../assets/logo_512x512.png deb/usr/share/icons/hicolor/512x512/apps/koncentro.png
cp ../assets/logo_1024x1024.png deb/usr/share/icons/hicolor/1024x1024/apps/koncentro.png
echo "3. Copied application files"

# 4. Create a desktop shortcut
mkdir -p deb/usr/share/applications
export KONCENTRO_AUTOSTART_ARGS=""
< ../installer-scripts/linux/common/koncentro.desktop envsubst > deb/usr/share/applications/org.koncentro.Koncentro.desktop
echo "4. Created a desktop shortcut"

# 5. Create a relative symlink in /usr/bin
mkdir -p deb/usr/bin
cd deb/usr/bin
ln -s ../lib/koncentro/koncentro ./koncentro
cd ../../..
echo "5. Created a relative symlink in /usr/bin"

# 6. Create metadata
mkdir -p deb/DEBIAN
< ../installer-scripts/linux/debian/debian-control envsubst > deb/DEBIAN/control
echo "6. Created metadata"
cat deb/DEBIAN/control

# 7. Build DEB file using xz compresing
# not using zstd although it is the standard in ubuntu 22.04+ because of larger file sizes
dpkg-deb --build deb ../dist/koncentro-${KONCENTRO_VERSION}-Linux-${ARCHITECTURE}.deb
echo "7. Built DEB file"
