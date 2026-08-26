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
        <td>Full sync: pull, Brewfile packages, dev tools, symlinks, OS defaults.
            Options: <code>-f</code>/<code>--force</code>,
            <code>--no-packages</code>, <code>--no-sync</code>.</td>
    </tr>
    <tr>
        <td><code>devtools</code></td>
        <td>Install the pinned dev tools only (one file per tool under
            <code>devtools.d/</code>).</td>
    </tr>
    <tr>
        <td><code>prefs</code></td>
        <td>Symlink application preferences and <code>~/.zshrc</code> into
            place, install oh-my-zsh if missing. Idempotent. With
            <code>-f</code>/<code>--force</code> existing local files are
            replaced (repo wins); without it they are left alone.</td>
    </tr>
    <tr>
        <td><code>osxprops</code></td>
        <td>Apply custom macOS defaults (also offered by <code>dotfiles</code>).</td>
    </tr>
    <tr>
        <td><code>quicklook</code></td>
        <td>Install the QLStephenSwift Quick Look extension (interactive;
            <code>dotfiles</code> runs it when missing).</td>
    </tr>
</table>

## Symlinked vs copied

`bin/dotfiles` symlinks `~/.bashrc`, `~/.bash_profile`, `~/.inputrc`,
`~/.hushlogin`, `~/.gitattributes`, `~/.gitignore` and `~/.devtools` into
this repository. Existing local files are skipped and reported; rerun with
`--force` to let the repo win.

`git/gitconfig` is the exception: it is copied to `~/.gitconfig` so
machine-local `git config --global` writes never end up in the repository.
Per-machine identity (work email, signing key) goes into
`~/.gitconfig.local`, pulled in via `[include]` at the end of gitconfig so
local values win.

## Local overrides

Not under version control, sourced/included if present:

* `~/.bash_profile.local` for private bash configuration.
* `~/.zshrc.local` for private zsh configuration.
* `~/.gitconfig.local` for the per-machine git identity.
* `~/.dotfilesrc` to prepend a custom Homebrew location to the PATH.

## Packages and dev tools

`Brewfile` declares the Homebrew formulae and casks; `dotfiles` applies it
with `brew bundle install`.

Each tool under `devtools.d/` (Maven, MongoDB, mongosh, Redis) pins its
version and defines its install function. The root `devtools` file holds
shared platform variables and sources them all on shell start. Bump a
version in `devtools.d/<tool>` and rerun `devtools`.

## Preferences

`bin/prefs` symlinks application configuration from this repository into
place: Ghostty (`~/.config/ghostty` and its Application Support directory)
and TextMate (`Bundles` and `Global.tmProperties`). TextMate app-level
preferences (`com.macromates.TextMate.plist`) are intentionally not synced;
symlinking plists is unreliable because cfprefsd caches them.

## zsh

`bin/prefs` links `~/.zshrc` and clones [oh-my-zsh](https://github.com/ohmyzsh/ohmyzsh)
if missing. The clone stays pristine so `omz update` always fast-forwards;
customizations live in this repository instead:

* `zsh/zsh_prompt` overrides agnoster theme functions after oh-my-zsh has
  loaded. Add further prompt tweaks there, never patch `~/.oh-my-zsh`.
* Plugins and options are configured in `zsh/zsh_plugins` and `zsh/zsh_options`.

The agnoster prompt needs powerline glyphs; Ghostty covers them with its
built-in Nerd Font fallback, no font install required.

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
