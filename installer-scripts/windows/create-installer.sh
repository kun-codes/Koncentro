#!/usr/bin/env bash

#
# Windows Installer Creator Script for Koncentro
# Based on Flowkeeper's installer script by Constantine Kulak
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

mkdir dist
echo "Made dist directory"

# to include license file in windows build, it needs to be in txt format
# https://jrsoftware.org/ishelp/index.php?topic=setup_licensefile
mv artifacts/LICENSE artifacts/LICENSE.txt
echo "Renamed license file"

"ISCC.exe" installer-scripts/windows/windows-installer.iss
echo "Created installer using Inno Setup"
mv dist/mysetup.exe dist/setup.exe
