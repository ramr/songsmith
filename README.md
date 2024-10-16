
# songsmith

Mac OSX command line music player ... loads and play local music from an
exported `Music.app` library (metadata).

## tldr

1. ```make``` installs the python3 virtual environment and dependencies.

1. Export metadata about your music using Music.app via
   `File -> Library -> Export Library`

1. Build the database.

   ```./bin/songsmith -b -x /path/to/Library.xml```

1. Search and play your songs - the example below uses 2 album titles to
   filter songs (`|` is an or-operator).
   ```./bin/songsmith -a 'communique|alchemy' -p```

## Setup

To install the python3 virtual environment and dependencies, you just
need to run:

```shell
make
```

## Build Database

The pre-requisite to building the songsmith database (fancy term for a
pickled pandas datafile!) is that you will need to manually export
your music library using Music.app (only for Mac OSX).

Use `File -> Library -> Export Library` in Music.app and save it somewhere.

This example uses your default `Downloads` directory, so the file location
would be `~/Downloads/Library.xml`

To build the songsmith database, load the above exported `Library.xml`
metadata file.

```shell
./bin/songsmith -b -x ~/Downloads/Library.xml
```

Alternatively, you can copy the `Library.xml` file over to the `data`
directory and skip specifying the file location ala:

```shell
cp ~/Downloads/Library.xml data/
./bin/songsmith -b    #  the default is same as adding -x data/Library.xml
```

## Search Functions

The songsmith utility provides 3 different ways to filter songs. This can
be done by searching for song title, album titles or artist/band names.
These filters are just text that matches up in the title - one or more words
contained in the title (and in the same order) or a more complicated set
as containing multiple choices.

For example, a filter `La Vie Rose` will match `La Vie En Rose` as the
words are in the same order in the title.
But `La Rose Vie` will not match `La Vie En Rose` as the order is different.

And a filter `La|Vie|Rose` will match any of those words in any order.

You can combine filters (this is the equivalent of an AND operation) ala:
a filter for songs `La|Vie|Rose` and a filter for artists `Piaf`.

### Song Search

To filter songs by a part of their title, use the `-s` or `--song[s]`
options.
You can sorta filter an exact match by using all words in the title.

Examples:

```shell

./bin/songsmith -s "industrial"  # filters by a word in the title.

./bin/songsmith -s "La Vie En Rose"    # filters by many words in the title.
./bin/songsmith --songs "La Vie Rose"  #  similar to above dropped `En`.

# And hopefully, that should allow you to see life through rose-colored
# glasses ...

# In a similar vein 'once time west' will match a song titled
# `Once Upon A Time In The West`
./bin/songsmith --song "once time west"   # == regex once.*time.*west

```

Check how many songs in your music collection match `you` and `i`
in the title ...

```shell
./bin/songsmith -s 'you|i'
```

### Album Search

To filter songs by an album title, use the `-a` or `--album[s]` options.

Examples:

```shell

./bin/songsmith --albums 'love over gold'  #  by a full album title

./bin/songsmith --album 'The Real Royal Albert Hall 1966 Concert (Live)'
./bin/songsmith -a 'Real Albert Hall 1966 Concert Live'  # by ordered words
```

### Artist Search

To filter songs by an artist or band name, use the `-r` or `--artists`
option.

Examples:

```shell

./bin/songsmith -a 'champion jack dupree'

./bin/songsmith -artist 'traffic|winwood|dave mason|blind faith'

./bin/songsmith --artists 'dire|knopfler|beatles|king'  # by many artists

```

### Combo Search

You can use a combination of the `-a`, `-r`, `-s` options (or their
full option variants ala `--albums`) to reduce the search results.

As an example, using a song filter `'telegraph|norwegian wood|help'` will
filter songs containing the words `telegraph` or then `norwegian` followed
by the word `wood` or generically a word `help` would return back a lot of
results ... and if you were expecting like a dozen odd songs but get back
like a couple of hundred odd, you can further filter those by attaching
a filter for the artists `"dire straits|beatles"`. That should trim the
results down a handful (or maybe a dozen odd).

Examples:

```shell
./bin/songsmith -s 'telegraph|norwegian wood|help' -r 'dire straits|beatles'


# filter down song[s] from a specific albums
./bin/songsmith -s 'telegraph|industrial' -a 'love over gold'

./bin/songsmith -s satisfaction --album forty  # no licks!

# filter down song[s] from a specific artist.
/bin/songsmith  --artist traffic -s 'john barleycorn|mr. fantasy|glad'

# filter down specific song[s] by artist and album.
./bin/songsmith  -s 'hey joe' --artist hendrix -a 'bbc sessions'

```

## Play Music

To play the music for the results, just add the `-p` option to the songsmith
command line.

Examples:

```shell
./bin/songsmith -s 'telegraph|norwegian|help' -r 'dire straits|beatles' -p

./bin/songsmith  -s 'hey joe' --artist hendrix -a 'bbc sessions' -p

./bin/songsmith  -s 'industrial|telegraph' -p

```

The default player configured is `mpv` in you path. You can change this
by editing the `config/songsmith.conf` file and use your favorite
command line player (or even a script wrapper around your player).
The examples in the `config/songsmith.conf` will allow you to
customize your player and there's a few examples shown in that file.

## Other Play Related Options

The `-m` or `--mix` option allows you to shuffle the songs that get
played when you specify the `-p` options.

And the `-n` or `--nsamples` option allows you to restrict the size
of your filtered playlist (play only `n` songs).
