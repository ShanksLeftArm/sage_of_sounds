# sage_of_sounds

sage_of_sounds is a discord bot written in python that can join a voice channel in multiple discord servers (one chat per server at a time) to stream the audio of any Youtube song or playlist.

## Installation
#### Required Python Packages
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.txt file.

```bash
pip install -r requirements.txt
```

#### FFMPEG Installation
This package ALSO requires a local installation of ffmpeg in order to stream the youtube audio. This needs to be installed separately on your repsective OS. All you need to provide this bot is the location of the ffmpeg executable (see more in Configuration)

## Configuration 

Create a config file at the root level of the project containing AT LEAST the following:
- **ffmpeg_executable_path** - Path to your local ffmpeg executable
- **token** - The secret token for your bot
- **command_prefix** - The command prefix to use for your bot

Example:
```json
{
    "token": "[YOUR TOKEN HERE]",
    "ffmpeg_executable_path": "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
    "command_prefix": "!"
}
```

Optional config variables:
- **LOG_LEVEL** - The Log Level the logger should log at [INFO | CRITICAL | DEBUG | ERROR | WARN ]


## Usage
### Bot Music Commands
```
MusicCommands:
  add     Adds a new song to be performed in the music queue
  clear   Clears the current music queue
  join    Request for me to join your voice channel for a performance
  leave   Request for me stop performing and to leave your voice channel
  next    Stops the current performance and begins the next in the music queue
  now     Displays what song is currently being performed
  pause   Pauses the current performance 
  play    Begins a new performance for the requested song
  queue   Displays what is currently playing and what is in the queue
  remove  Removes a specified song from the music queue by position. 1 is the...
  resume  Resumes play if a performance was paused
  shuffle Shuffles the music queue
  skip    Stops the current performance and begins the next in the music queue
  stop    Pauses the current performance 
  volume  Request to view or adjust the current volume
```

### Simple Tutorial - Command Prefix '!'
1. Join the Voice Channel
2. Play a Song
3. Add to the Queue
4. View the Queue
5. Skip to the next Song
6. Pause
7. Resume
8. Volume adjustment
9. Leave 
```
!join
!play never gonna give you up lyrics video
!add https://www.youtube.com/watch?v=DMATysGZIeA
!add crazy in love beyonce jay z
!queue
!remove 1
!queue
!skip
!pause
!resume
!volume 75
!leave
```

### Further Help
- Use '!help <command>' to get a description of how to use each command in detail.

## License
[MIT](https://choosealicense.com/licenses/mit/)