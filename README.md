# Argparse - Manpager

Generate manual pages from executable python modules using argparse.

## Installation

Archlinux users have [a package in the AUR](https://aur.archlinux.org/packages/python-argparse-manpager-git/). To use the [PKGBUILD](PKGBUILD) as it is kept in this repository, [the makepkg-template for git](https://github.com/dffischer/git-makepkg-template) has to be installed.

This project uses [waf](https://code.google.com/p/waf/) to compile and install. If you already have waf installed with your distribution, you can just `waf configure install`. If you do not have waf installed, execute

```bash
wget -O waf https://waf.io/waf-2.1.2
chmod 755 waf
./waf configure install
```

## Usage

For example, this generates the manpage for a module already built into python.

```bash
manpager http.server
```

For more options, consult the manpager manpage.

### With waf

This project also installs a waf tool for use in your own projects. It can be used to install whole python packages, generate starter scripts and manual pages to let it look like an ordinary binary. The [wscript](wscript) of this project itself can be used as a simple example. The docstring of [the tool](waftools/manpyger.py) provides more detailed documentation.
