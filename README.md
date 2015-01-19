# Argparse - Manpager

Generate manual pages from executable python modules using argparse.

## Installation

This project uses [waf](https://code.google.com/p/waf/) to compile and install. If you already have waf installed with your distribution, you can just `waf configure install`. If you do not have waf installed, execute

```bash
wget -O waf http://ftp.waf.io/pub/release/waf-1.8.6
chmod 755 waf
./waf configure install
```

## Usage

For example, this generates the manpage for a module already built into python.

```bash
manpager http.server
```

For more options, consult the manpager manpage.
