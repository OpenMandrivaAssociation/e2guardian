Name:		e2guardian
Version:	5.3.4
Release:	3
Summary:	Open Source web content filter
License:	GPLv2+
Group:		System/Servers
URL:		https://e2guardian.org/cms/
Source0:	https://github.com/e2guardian/e2guardian/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:	e2guardian.service
Patch0:		e2guardian-mga_conf.patch
BuildRequires:	pkgconfig(zlib)
BuildRequires:	pkgconfig(libpcreposix)
BuildRequires:	pkgconfig(openssl)
BuildRequires:	libesmtp-devel
Provides:	dansguardian

Requires(post):	rpm-helper
Requires(pre):	rpm-helper
Requires(preun): rpm-helper
Requires(postun): rpm-helper

Recommends:	webproxy

%description
e2guardian is an Open Source web content filter, It filters the actual
content of pages based on many methods including phrase matching, request
header and URL filtering, etc. It does not purely filter based on a banned
list of sites.
e2guardian is a content filtering proxy that works in conjunction with
another caching proxy such as Squid or Oops.
e2guardian is a fork of DansGuardian and the maintainers fully acknowledge
the work carried out by and the copyright of Daniel Baron and other
contributors to the Dansguardian project.

%prep
%setup -q
%autopatch -p1

# fix permission
chmod 0644 doc/* AUTHORS ChangeLog COPYING

%build
NOCONFIGURE=1 ./autogen.sh

%configure \
	--localstatedir=%{_var}/lib \
	--disable-silent-rules \
	--enable-pcre=yes \
	--enable-clamd=yes \
	--enable-icap=yes \
	--enable-kavd=no \
	--enable-commandline=yes \
	--enable-ntlm=yes \
	--enable-email=yes \
	--enable-orig-ip=yes \
	--enable-sslmitm=yes \
	--with-proxyuser=%{name} \
	--with-proxygroup=%{name} \
	--with-logdir=%{_var}/log/%{name} \
	--with-piddir=/run \
	--with-sysconfsubdir=%{name}

%make_build

%install
%make_install

# systemd service
install -Dpm 644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service

# access log file
install -d %{buildroot}%{_var}/log/%{name}
touch %{buildroot}%{_var}/log/%{name}/access.log

install -d %{buildroot}%{_var}/lib/%{name}/tmp

# cgi-script
install -d %{buildroot}%{_var}/www/cgi-bin
install -m 0755 data/e2guardian.pl %{buildroot}%{_var}/www/cgi-bin/

# make sure this file is present
echo "localhost" >> %{buildroot}%{_sysconfdir}/%{name}/lists/exceptionfileurllist

# construct file lists
find %{buildroot}%{_sysconfdir}/%{name} -type d | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0755,root,root) %dir /' > %{name}.filelist

find %{buildroot}%{_sysconfdir}/%{name} -type f | grep -v "\.orig" | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0644,root,root) %config(noreplace) /' >> %{name}.filelist

# logrotate file
install -d %{buildroot}%{_sysconfdir}/logrotate.d
cat << EOF > %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
/var/log/%{name}/access.log {
    create 644 %{name} %{name}
    rotate 5
    weekly
    sharedscripts
    prerotate
	service %{name} stop
    endscript
    postrotate
	service %{name} start
    endscript
}
EOF

# README.urpmi Mageia file
cat > README.urpmi << EOF
Make sure to change your /etc/%{name}/%{name}.conf to reflect your own settings.
Special attention must be given to the port that the proxy server is listening to,
the port that %{name} will listen to and to the web url to the %{name}.pl cgi-script.

Author: Daniel Barron
daniel@jadeb.com
EOF

# cleanup
rm -rf %{buildroot}%{_datadir}/%{name}/scripts
rm -rf %{buildroot}%{_datadir}/doc/e2guardian*

%pre
%_pre_useradd %{name} /var/lib/%{name} /bin/false

%preun
%_preun_service %{name}
if [ $1 = 0 ] ; then
    rm -f /var/log/%{name}/*
fi

%post
%create_ghostfile /var/log/%{name}/access.log %{name} %{name} 644
%_post_service %{name}

%postun
%_postun_userdel %{name}

%files -f %{name}.filelist
%doc AUTHORS ChangeLog README.md README.urpmi
%doc doc/{AuthPlugins,ContentScanners,DownloadManagers}
%doc doc/{FAQ,FAQ.html,Plugins}
%license COPYING
%{_sbindir}/%{name}
%{_datadir}/%{name}/
%{_unitdir}/%{name}.service
%{_mandir}/man8/%{name}.8*
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0755,root,root) %{_var}/www/cgi-bin/%{name}.pl
%dir %attr(0755,%{name},%{name}) %{_var}/log/%{name}
%dir %attr(0755,%{name},%{name}) %{_var}/lib/%{name}
%dir %attr(0755,%{name},%{name}) %{_var}/lib/%{name}/tmp
%ghost %attr(0644,%{name},%{name}) %{_var}/log/%{name}/access.log
