# Converter

A lightweight and flexible tool that allows users to add various file conversion types and options themselves. The program adapts to the settings in the configuration file and generates the necessary context menu entries.

---

## Features

- Easily integrates into the Windows context menu.
- Automatically adjusts based on the `config.txt` settings.
- Supports multiple tools and formats defined by the user.

---

## How to Use

### Step 1: Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/DenchicPts/Converter.git
```

### Step 2: Build the Executable

Use tools like `PyInstaller` to build an executable file from the provided Python script. Once built, you can place the `.exe` file anywhere on your system. Ensure that the `config.txt` file is placed in the same directory as the executable.

### Step 3: Run with Administrator Privileges

Run the generated executable with administrator privileges. This is necessary to add the required entries to the Windows registry. Once done, the options will appear in the context menu for the specified file types.

---

## Configuration

The program relies on a `config.txt` file located in the same directory as the executable. This file defines the tools, formats, and conversion options. Below is an example of how the configuration is structured:

```ini
[General]
app_name = Converter
command_template = "{app} {tool} {input_file} {output_format}"

[Tools]
ffmpeg = path/to/ffmpeg.exe

[Formats]
image = png, jpg, webp, bmp
audio = mp3, m4a, wav, aac
video = mp4, avi, mkv, mov

[ToolOptions]
# Example options for ffmpeg
ffmpeg_image_to_png = -q:v 2
ffmpeg_audio_to_mp3 = -acodec libmp3lame -b:a 192k
```

You can customize this file to add new tools or define additional formats and options.

---

Created by DenchicPts❤️

