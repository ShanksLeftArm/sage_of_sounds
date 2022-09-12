# sage_of_sounds

sage_of_sounds is a Python library written as a discord bot that can join a voice channel in multiple discord servers (one chat per server at a time) to stream the audio of any Youtube song or playlist.

## Installation

This application requires the following python packages:
```bash
asyncio
discord.py
requests
youtube-dl
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.txt file.

```bash
pip install requirements.txt
```

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
TODO: Add How to Use section

```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```


## License
[MIT](https://choosealicense.com/licenses/mit/)