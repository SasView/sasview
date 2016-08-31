Summary: sasview
Name: sasview
Version: 4.0.0
Release: 8
Group: Applications/Engineering
prefix: /opt/sasview
BuildRoot: %{_tmppath}/%{name}
License: Open
Source: sasview.tgz

%define debug_package %{nil}
%define site_packages %(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")

%description
SasView analysis application for small-angle scattering

%prep
%setup -q -n %{name}

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{site_packages}

export PYTHONPATH=$PYTHONPATH:%{buildroot}%{site_packages}
easy_install -s %{buildroot}%{_bindir} -d %{buildroot}%{site_packages} sasview*.egg
easy_install -d %{buildroot}%{site_packages} sasmodels*.egg
%post

%files
/usr/lib/python2.7
/usr/bin/sasview
/usr/bin/bumps




