# The track

The header's sound button plays `bmu.mp3` from this folder, looped.

Drop the file in as `audio/bmu.mp3` and it works — nothing else to change.
Until it is there the button appears on hover and does nothing, which is
deliberate: a browser refuses to play audio it cannot fetch, and the button
is written to keep saying "play" rather than to claim something is running.

Keep it small. It is fetched only when somebody presses (`preload="none"`),
but it is still a file every listener downloads.
