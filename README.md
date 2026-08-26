# dotfiles

Personal macOS setup: shell configuration, Homebrew packages, dev tools
and application preferences.

## Install

Requires the [XCode Command Line Tools](https://developer.apple.com/downloads).
May overwrite existing dotfiles in your HOME directory.

```bash
$ bash -c "$(curl -fsSL https://raw.githubusercontent.com/mp911de/dotfiles/main/bin/dotfiles)"
```

If you fork this project, substitute your username in the command above and
in the two variables at the top of `bin/dotfiles`.

## Commands

<table>
    <tr>
        <td><code>dotfiles</code></td>
        <td>Full sync: pull, Homebrew packages, dev tools, symlinks, OS defaults.
            Options: <code>--no-packages</code>, <code>--no-sync</code>.</td>
    </tr>
    <tr>
        <td><code>devtools</code></td>
        <td>Install the pinned dev tools only (Maven, MongoDB, mongosh, Redis).</td>
    </tr>
    <tr>
        <td><code>prefs</code></td>
        <td>Symlink application preferences into place. Idempotent. With
            <code>-f</code>/<code>--force</code> existing local files are
            replaced (repo wins); without it they are left alone.</td>
    </tr>
    <tr>
        <td><code>osxprops</code></td>
        <td>Apply custom macOS defaults (also offered by <code>dotfiles</code>).</td>
    </tr>
</table>

## Symlinked vs copied

`bin/dotfiles` symlinks `~/.bashrc`, `~/.bash_profile`, `~/.inputrc`,
`~/.hushlogin`, `~/.gitattributes`, `~/.gitignore` and `~/.devtools` into
this repository.

`git/gitconfig` is the exception: it is copied to `~/.gitconfig` so
machine-local git configuration (e.g. credentials) never ends up in the
repository.

## Local overrides

Not under version control, sourced if present:

* `~/.bash_profile.local` for private bash configuration and git credentials.
* `~/.zshrc.local` for private zsh configuration.
* `~/.dotfilesrc` to prepend a custom Homebrew location to the PATH.

## Devtools version pins

The root `devtools` file pins the tool versions (`MAVEN_VERSION`,
`MONGODB_VERSION`, `MONGODB_TOOLS_VERSION`, `REDIS_VERSION`) and is sourced
on every shell start. Bump a version there and rerun `devtools`.

## Preferences

`bin/prefs` symlinks application configuration from this repository into
place: Ghostty (`~/.config/ghostty` and its Application Support directory)
and TextMate (`Bundles` and `Global.tmProperties`). TextMate app-level
preferences (`com.macromates.TextMate.plist`) are intentionally not synced;
symlinking plists is unreliable because cfprefsd caches them.

## Acknowledgements

Inspiration and code was taken from many sources, including:

* [@necolas](https://github.com/necolas) (Nicolas Gallagher)
  [https://github.com/necolas/dotfiles](https://github.com/necolas/dotfiles)
* [@mathiasbynens](https://github.com/mathiasbynens) (Mathias Bynens)
  [https://github.com/mathiasbynens/dotfiles](https://github.com/mathiasbynens/dotfiles)
* [@tejr](https://github.com/tejr) (Tom Ryder)
  [https://github.com/tejr/dotfiles](https://github.com/tejr/dotfiles)
* [@gf3](https://github.com/gf3) (Gianni Chiappetta)
  [https://github.com/gf3/dotfiles](https://github.com/gf3/dotfiles)
* [@cowboy](https://github.com/cowboy) (Ben Alman)
  [https://github.com/cowboy/dotfiles](https://github.com/cowboy/dotfiles)
* [@alrra](https://github.com/alrra) (Cãtãlin Mariş)
  [https://github.com/alrra/dotfiles](https://github.com/alrra/dotfiles)
