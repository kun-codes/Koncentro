#!/usr/bin/env bash

#
# rpm package creation script for Koncentro
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

# Check for distro parameter (fedora or opensuse)
DISTRO=${1:-fedora}
echo "Building RPM for distribution: $DISTRO"

# 1. Get the version
echo "1. Version = $KONCENTRO_VERSION"
echo "Architecture: $ARCHITECTURE"

# 2. Prepare temp folder
mkdir -p build/rpm
cd build
rm -rf rpm
mkdir -p rpm
echo "2. Prepared temp folder"

# 3. Copy application files
mkdir -p rpm/usr/lib/koncentro

# Create directories for icon sizes
mkdir -p rpm/usr/share/icons/hicolor/16x16/apps
mkdir -p rpm/usr/share/icons/hicolor/24x24/apps
mkdir -p rpm/usr/share/icons/hicolor/32x32/apps
mkdir -p rpm/usr/share/icons/hicolor/48x48/apps
mkdir -p rpm/usr/share/icons/hicolor/64x64/apps
mkdir -p rpm/usr/share/icons/hicolor/128x128/apps
mkdir -p rpm/usr/share/icons/hicolor/256x256/apps
mkdir -p rpm/usr/share/icons/hicolor/512x512/apps
mkdir -p rpm/usr/share/icons/hicolor/1024x1024/apps

cp -r ../artifacts/* rpm/usr/lib/koncentro/

chmod +x rpm/usr/lib/koncentro/koncentro
chmod +x rpm/usr/lib/koncentro/mitmdump

# Copy icons
cp ../assets/logo_16x16.png rpm/usr/share/icons/hicolor/16x16/apps/koncentro.png
cp ../assets/logo_24x24.png rpm/usr/share/icons/hicolor/24x24/apps/koncentro.png
cp ../assets/logo_32x32.png rpm/usr/share/icons/hicolor/32x32/apps/koncentro.png
cp ../assets/logo_48x48.png rpm/usr/share/icons/hicolor/48x48/apps/koncentro.png
cp ../assets/logo_64x64.png rpm/usr/share/icons/hicolor/64x64/apps/koncentro.png
cp ../assets/logo_128x128.png rpm/usr/share/icons/hicolor/128x128/apps/koncentro.png
cp ../assets/logo_256x256.png rpm/usr/share/icons/hicolor/256x256/apps/koncentro.png
cp ../assets/logo_512x512.png rpm/usr/share/icons/hicolor/512x512/apps/koncentro.png
cp ../assets/logo_1024x1024.png rpm/usr/share/icons/hicolor/1024x1024/apps/koncentro.png
echo "3. Copied application files"

# 4. Create the wrapper script for /usr/bin
mkdir -p rpm/usr/bin
cat > rpm/usr/bin/koncentro << EOF
#!/bin/bash

#
# Koncentro - Focus manager and website blocker
# Copyright (c) 2025 Kunal
#

PYTHONPATH=/usr/lib/koncentro /usr/lib/koncentro/koncentro \$@
EOF
chmod +x rpm/usr/bin/koncentro
echo "4. Created a wrapper script in /usr/bin"

# 5. Create a desktop shortcut
mkdir -p rpm/usr/share/applications
export KONCENTRO_AUTOSTART_ARGS=""
< ../installer-scripts/linux/common/koncentro.desktop envsubst > rpm/usr/share/applications/org.koncentro.Koncentro.desktop
echo "5. Created a desktop shortcut"

# 6. Build RPM file based on distribution using rpmbuild
mkdir -p ../dist
cd ..

# Setup rpmbuild directories
mkdir -p ~/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

case "$DISTRO" in
  fedora)
    echo "Building Fedora RPM package with zstd compression..."

    # Process spec file
    envsubst < installer-scripts/linux/rpm/koncentro-fedora.spec > ~/rpmbuild/SPECS/koncentro.spec

    # Create source tarball
    tar -czf ~/rpmbuild/SOURCES/koncentro-${KONCENTRO_VERSION}.tar.gz -C build/rpm .

    # Build RPM with zstd compression
    rpmbuild -bb ~/rpmbuild/SPECS/koncentro.spec

    # Move and rename the built RPM from default location
    mv ~/rpmbuild/RPMS/${ARCHITECTURE}/koncentro-${KONCENTRO_VERSION}-1*.${ARCHITECTURE}.rpm \
       dist/koncentro-${KONCENTRO_VERSION}-Linux-${ARCHITECTURE}-Fedora.rpm

    echo "Built Fedora RPM package with zstd compression"
    ;;

  opensuse|*)
    echo "Building openSUSE RPM package with zstd compression..."

    # Process spec file
    envsubst < installer-scripts/linux/rpm/koncentro-opensuse.spec > ~/rpmbuild/SPECS/koncentro.spec

    # Create source tarball
    tar -czf ~/rpmbuild/SOURCES/koncentro-${KONCENTRO_VERSION}.tar.gz -C build/rpm .

    # Build RPM with zstd compression
    rpmbuild -bb ~/rpmbuild/SPECS/koncentro.spec

    # Move and rename the built RPM from default location
    mv ~/rpmbuild/RPMS/${ARCHITECTURE}/koncentro-${KONCENTRO_VERSION}-1.${ARCHITECTURE}.rpm \
       dist/koncentro-${KONCENTRO_VERSION}-Linux-${ARCHITECTURE}-openSUSE.rpm

    echo "Built openSUSE RPM package with zstd compression"
    ;;
esac

echo "6. RPM packages built successfully with zstd compression"
