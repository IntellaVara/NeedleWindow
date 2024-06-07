<div align="center">
    <img src="images/needle_window.jpg" width="512" height="512" alt="Needle Window">
</div>


# NeedleWindow

If you suffer from tabitis then suffer no longer. 
Combining Langchain + Huggingface Embeddings + Firefox/Chrome extensions finally gives us relief from the vexing self-inflicted self-doubt. 'What is wrong with us?' we will wonder no longer!

By pressing a shortcut key combination a prompt window appears, and after entering a query, the appropriate tab is moved to top of your cluttered desktop as the active window.

FeelsLikeMagic™ straight fresh out of the oven.

Works with PDFs. Other convenience features also planned.

# Installation
## Ubuntu

### Step 1: Ensure Conda is installed on your system
```bash
conda --version
```
If Conda is not installed, follow the installation instructions for your OS from the official Conda documentation.

### Step 2: Clone the GitHub repository to your local machine
```bash
git clone https://github.com/IntellaVara/NeedleWindow.git
cd NeedleWindow
```
### Step 3: Create a Conda environment using the provided environment.yml file
```bash
conda env create -f environment.yml
```

### Step 4: Activate the newly created environment
```bash
conda activate needle_window
```

### Step 4a: Get Firefox Extension & or Chrome
[https://addons.mozilla.org/en-US/firefox/addon/needlewindow-tab-focuser/](https://addons.mozilla.org/en-US/firefox/addon/needlewindow-tab-focuser/)

(Chrome Coming soon!)


### Step 5: Set executable permissions for the launch script
```bash
cd Ubuntu/flask
chmod +x launch.sh
```

### Step 6: Run the launch script
```bash
./launch.sh
```

### Step 7:
- Choose GPU (y/n) (you have to type this)
- Choose gui vs hotkeys (hotkeys use pynput keylogger)

<div align="leftr">
    <img src="images/GUI.png" alt="Needle Window GUI">
</div>

If using the GUI:
N = 1 will automatically choose the most relevant page. If N > 1 the top N relevant results will be clickable.

If using hotkeys it is always N = 1.

## Windows
Coming soon!

## Mac
Contributions welcome!

# Security Concerns
Oh my there are so many! (Detailed and paranoid doc incoming)


## To-Do List
- [X] Ubuntu Firefox
- [ ] Ubuntu Chrome
- [ ] Windows Firefox
- [ ] Windows Chrome
- [ ] Compose readme on security risks


