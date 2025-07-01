<p align="center" style="display: flex; align-items: center; justify-content: center;">
  <img src="assets/logo_64x64.png" width="64" style="vertical-align: middle; margin-right: 12px;" />
  <span style="display: inline-block; vertical-align: middle; font-size:2.5em;"><b>Koncentro</b></span>
</p>
<p align="center">A powerful productivity app combining Pomodoro technique, task management, and website blocking.</p>

> [!IMPORTANT]
> Koncentro assumes that you aren't using a proxy server already since it runs a local proxy server to block websites.

## Features

- **Cross Platform:** Koncentro works on Windows, macOS and Linux without using heavy frameworks like Electron.
- **Timeboxing:** Allocate a fixed duration to each task and aim to complete it within the time limit.
- **Website Blocker:** Koncentro includes an integrated website blocker that lets you choose to block distractions by either a blocklist or an allowlist.
- **Workspaces:** Each Workspace has its own set of Pomodoro timer settings, website blocker settings and task list, allowing you to separate work and personal projects.
- **Fluent Design:** Koncentro follows Microsoft's Fluent Design principles. It supports the Mica effect on Windows 11.


## Installation


- Install [Python 3.12](https://www.python.org/downloads/) if you haven't already.
- Install [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
- Clone the repository using the command
```sh
git clone https://github.com/kun-codes/Koncentro.git
```
- Change the directory to the repository
```sh
cd Koncentro
```
- Install the dependencies using poetry
```sh
poetry install
```
- Run the app using the command
```sh
poetry run python src
```

## Usage
> [!IMPORTANT]
> On your first run of the application, start the timer and then go to [mitm.it](http://mitm.it) on a chromium based browser and install the certificate as per your OS and browser choice. This is required for the website blocker to work. After installing the certificate, restart the application.

- Start the app using the command mentioned above.

There are four main screens in the app:
1. **Task View:** This is where you can add, delete and view tasks.
 
![image](https://i.ibb.co/6m17JRr/image.png)

2. **Timer View:** This is where you can start the timer and view the time left.

![image](https://i.ibb.co/bmMdB3m/image.png)

3. **Website Filter View:** This is where you can add, delete and view websites to block and choose between a blocklist and a whitelist. Please enter the website without the protocol (http/https) as shown in the image.

![image](https://i.ibb.co/9N0DK9h/image.png)

4. **Workspace Selector View:** This is where you can select the workspace you want to work in. Each workspace has its own adjustable timer and website filter settings. Each workspace also has its own tasks.

![image](https://i.ibb.co/72WN7bP/image.png)

## Known Bugs

- App doesn't change theme correctly without restarting when OS theme is changed.

## Credits

- [Super Productivity](https://github.com/johannesjo/super-productivity): The app is inspired by Super Productivity.
- [chomper](https://github.com/aniketpanjwani/chomper): The website blocker has some functionality inspired by chomper.
- [Flowkeeper](https://github.com/flowkeeper-org/fk-desktop): Installer creation scripts have been adapted from Flowkeeper.
