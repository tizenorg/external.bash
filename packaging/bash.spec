Version: 4.1
Name: bash
Summary: The GNU Bourne Again shell
Release: 1
Group: System/Shells
License: GPLv2+
Url: http://www.gnu.org/software/bash
Source0: ftp://ftp.gnu.org/gnu/bash/%{name}-%{version}.tar.gz

# SLP patches
Patch0: bash41-001.patch
Patch1: bash41-002.patch
Patch2: bash41-003.patch
Patch3: bash41-004.patch
Patch4: bash41-005.patch
Patch5: deb-bash-config.patch
Patch6: privmode.patch
Patch7: bash-default-editor.patch
Patch8: bash-subst-param-length.patch
Patch9: pgrp-pipe.patch
Patch10: input-err.patch
Patch11: bash-aliases-repeat.patch
Patch12: builtins-declare-fix.patch

Requires(post): ncurses-libs

BuildRequires: bison
#BuildRequires: ncurses-devel
BuildRequires: autoconf

%description
The GNU Bourne Again shell (Bash) is a shell or command language
interpreter that is compatible with the Bourne shell (sh). Bash
incorporates useful features from the Korn shell (ksh) and the C shell
(csh). Most sh scripts can be run by bash without modification.

%package doc
Summary: Documentation files for %{name}
Group: Development/Languages
Requires: %{name} = %{version}-%{release}

%description doc
This package contains documentation files for %{name}.

%define pkgdocdir %{_datadir}/doc/%{name}-%{version}

%prep
%setup -q

%patch0 -p1 -b .bash41-001
%patch1 -p1 -b .bash41-002
%patch2 -p1 -b .bash41-003
%patch3 -p1 -b .bash41-004
%patch4 -p1 -b .bash41-005
%patch5 -p1 -b .deb-bash-config
%patch6 -p1 -b .privmode
%patch7 -p1 -b .bash-default-editor
%patch8 -p0 -b .bash-subst-param-length
%patch9 -p0 -b .pgrp-pipe
%patch10 -p0 -b .input-err
%patch11 -p0 -b .bash-aliases-repeat
%patch12 -p1 -b .builtins-declare-fix

%build
autoconf
%configure --enable-largefile --without-bash-malloc --disable-nls

# Recycles pids is neccessary. When bash's last fork's pid was X
# and new fork's pid is also X, bash has to wait for this same pid.
# Without Recycles pids bash will not wait.
make "CPPFLAGS=-D_GNU_SOURCE -DRECYCLES_PIDS `getconf LFS_CFLAGS`"
%check
make check

%install
rm -rf $RPM_BUILD_ROOT

if [ -e autoconf ]; then
  # Yuck. We're using autoconf 2.1x.
  export PATH=.:$PATH
fi

# Fix bug #83776
perl -pi -e 's,bashref\.info,bash.info,' doc/bashref.info

make DESTDIR=$RPM_BUILD_ROOT install

mkdir -p $RPM_BUILD_ROOT/etc

# make manpages for bash builtins as per suggestion in DOC/README
pushd doc
sed -e '
/^\.SH NAME/, /\\- bash built-in commands, see \\fBbash\\fR(1)$/{
/^\.SH NAME/d
s/^bash, //
s/\\- bash built-in commands, see \\fBbash\\fR(1)$//
s/,//g
b
}
d
' builtins.1 > man.pages
for i in echo pwd test kill; do
  perl -pi -e "s,$i,,g" man.pages
  perl -pi -e "s,  , ,g" man.pages
done

install -c -m 644 builtins.1 ${RPM_BUILD_ROOT}%{_mandir}/man1/builtins.1

for i in `cat man.pages` ; do
  echo .so man1/builtins.1 > ${RPM_BUILD_ROOT}%{_mandir}/man1/$i.1
  chmod 0644 ${RPM_BUILD_ROOT}%{_mandir}/man1/$i.1
done
popd

# Link bash man page to sh so that man sh works.
ln -s bash.1 ${RPM_BUILD_ROOT}%{_mandir}/man1/sh.1

# Not for printf, true and false (conflict with coreutils)
rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/printf.1
rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/true.1
rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/false.1

pushd $RPM_BUILD_ROOT
mkdir ./bin
mv ./usr/bin/bash ./bin
ln -sf bash ./bin/sh
rm -f .%{_infodir}/dir
popd
mkdir -p $RPM_BUILD_ROOT/etc/skel
#install -c -m644 %SOURCE1 $RPM_BUILD_ROOT/etc/skel/.bashrc
#install -c -m644 %SOURCE2 $RPM_BUILD_ROOT/etc/skel/.bash_profile
#install -c -m644 %SOURCE3 $RPM_BUILD_ROOT/etc/skel/.bash_logout
LONG_BIT=$(getconf LONG_BIT)
mv $RPM_BUILD_ROOT%{_bindir}/bashbug \
   $RPM_BUILD_ROOT%{_bindir}/bashbug-"${LONG_BIT}"

# Fix missing sh-bangs in example scripts (bug #225609).
for script in \
  examples/scripts/krand.bash \
  examples/scripts/bcsh.sh \
  examples/scripts/precedence \
  examples/scripts/shprompt
do
  cp "$script" "$script"-orig
  echo '#!/bin/bash' > "$script"
  cat "$script"-orig >> "$script"
  rm -f "$script"-orig
done

rm -rf %{buildroot}%{_bindir}/bashbug-*
chmod a-x doc/*.sh

%clean
rm -rf $RPM_BUILD_ROOT

# ***** bash doesn't use install-info. It's always listed in %{_infodir}/dir
# to prevent prereq loops

# post is in lua so that we can run it without any external deps.  Helps
# for bootstrapping a new install.
# Jesse Keating 2009-01-29 (code from Ignacio Vazquez-Abrams)
%post -p <lua>
bashfound = false;
shfound = false;
 
f = io.open("/etc/shells", "r");
if f == nil
then
  f = io.open("/etc/shells", "w");
else
  repeat
    t = f:read();
    if t == "/bin/bash"
    then
      bashfound = true;
    end
    if t == "/bin/sh"
    then
      shfound = true;
    end
  until t == nil;
end
f:close()
 
f = io.open("/etc/shells", "a");
if not bashfound
then
  f:write("/bin/bash\n")
end
if not shfound
then
  f:write("/bin/sh\n")
end
f:close()

%postun
if [ "$1" = 0 ]; then
    /bin/grep -v '^/bin/bash$' < /etc/shells | \
      /bin/grep -v '^/bin/sh$' > /etc/shells.new
    /bin/mv /etc/shells.new /etc/shells
fi


%docs_package

%files 
/bin/sh
/bin/bash

