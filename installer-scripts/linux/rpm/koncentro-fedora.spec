Name:           koncentro
Version:        ${KONCENTRO_VERSION}
Release:        1
Summary:        A productivity app with Pomodoro, tasks, and website blocking

License:        GPL-3.0
URL:            https://github.com/kun-codes/Koncentro
Source0:        %{name}-%{version}.tar.gz

BuildArch:      ${ARCHITECTURE}
Requires:       xcb-util-cursor xcb-util-keysyms xcb-util-wm

%global _binary_payload w7.zstdio
%global _source_payload w7.zstdio

%description
Koncentro - A productivity app with Pomodoro, tasks, and website blocking

%prep
%setup -q -c

%build
# No build needed - pre-built application

%install
mkdir -p %{buildroot}/usr/lib/koncentro
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/16x16/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/24x24/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/32x32/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/48x48/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/64x64/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/128x128/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/512x512/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/1024x1024/apps

cp -r usr/lib/koncentro/* %{buildroot}/usr/lib/koncentro/
cp usr/bin/koncentro %{buildroot}/usr/bin/koncentro
cp usr/share/applications/org.koncentro.Koncentro.desktop %{buildroot}/usr/share/applications/
cp usr/share/icons/hicolor/16x16/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/16x16/apps/
cp usr/share/icons/hicolor/24x24/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/24x24/apps/
cp usr/share/icons/hicolor/32x32/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/32x32/apps/
cp usr/share/icons/hicolor/48x48/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/48x48/apps/
cp usr/share/icons/hicolor/64x64/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/64x64/apps/
cp usr/share/icons/hicolor/128x128/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/
cp usr/share/icons/hicolor/256x256/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/
cp usr/share/icons/hicolor/512x512/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/512x512/apps/
cp usr/share/icons/hicolor/1024x1024/apps/koncentro.png %{buildroot}/usr/share/icons/hicolor/1024x1024/apps/

%files
%defattr(644,root,root,755)
%attr(755,root,root) /usr/lib/koncentro/koncentro
%attr(755,root,root) /usr/lib/koncentro/mitmdump
%attr(755,root,root) /usr/bin/koncentro
/usr/lib/koncentro/*
/usr/share/applications/org.koncentro.Koncentro.desktop
/usr/share/icons/hicolor/*/apps/koncentro.png
