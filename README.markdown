# go-gedit-plugin

go-gedit-plugin is a Go programming language plugin for gedit editor.

## Current features

* Code completion (gocode)
* Autoformatting (gofmt)
* Shortcuts for toggling comments

Code completion activates with shortcut `ctrl-space`.

## Prerequisites for installation

Before actual installation perform these steps:

1. Set environmental variable `$GOBIN` to the correct path and preferably add it into your `$PATH` 
as instructed in [http://golang.org/doc/install.html](http://golang.org/doc/install.html).
go-gedit-plugin will need to know this path. If you do not set it, then you have to set it in 
gedit: Preferences->Plugins->Go plugin: GOBIN Path.

2. Install [gocode](https://github.com/nsf/gocode) for code completion support.

3. Make sure you have a go.lang Go syntax coloring file on your system, 
if you want syntax coloring.
The file should be located in `/usr/share/gtksourceview-2.0/language-specs`.
If you don't have it, get it from here, 
[http://git.gnome.org/browse/gtksourceview/plain/data/language-specs/go.lang](http://git.gnome.org/browse/gtksourceview/plain/data/language-specs/go.lang). 
Just copy it to the said folder.

## Installation

To perform the actual installation you can just copy `GoPlugin.gedit-plugin` file and `GoPlugin` 
directory to `~/.gnome2/gedit/plugins` in your home folder to install the plugin for yourself 
or to folder `/usr/lib/gedit-2/plugins` to install it for everyone. 

If you don't want to recopy the files with every new release, 
it's recommended to clone the project and make symbolic links of the files to one of the plugin folders.

Example installation in home folder:

	cd
	hg clone -b release https://bitbucket.org/fzzbt/go-gedit-plugin
	ln -s ~/go-gedit-plugin/go-gedit-plugin.gedit-plugin ~/.gnome2/gedit/plugins/
	ln -s ~/go-gedit-plugin/go-gedit-plugin ~/.gnome2/gedit/plugins/

To update to a newer release just perform the following:

	cd ~/go-gedit-plugin
	hg pull -u -b release

## Known issues

###Issues caused by gtksourceview

* Pointless "Go code completion" header is displayed in code completion to avoid crashing 
(see [bug](https://bugzilla.gnome.org/show_bug.cgi?id=629055))
* Code completion dialog forgets "Details..." setting after exiting gedit.
