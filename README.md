<h1 align="center">Koncentro</h1>

<p align="center">A powerful productivity app combining Pomodoro technique, task management, and website blocking.</p>

<p align="center">
  <img src="screenshots/banner.png" alt="Koncentro Banner" />
</p>

> [!IMPORTANT]
> Koncentro assumes that you aren't using a proxy server already since it runs a local proxy server to block websites.

## Features

- **Cross Platform:** Koncentro works on Windows, macOS and Linux without using heavy frameworks like Electron.
- **Timeboxing:** Allocate a fixed duration to each task and aim to complete it within the time limit.
- **Website Blocker:** Koncentro includes an integrated website blocker that lets you choose to block distractions by either a blocklist or an allowlist.
- **Workspaces:** Each Workspace has its own set of Pomodoro timer settings, website blocker settings and task list, allowing you to separate work and personal projects.
- **Fluent Design:** Koncentro follows Microsoft's Fluent Design principles. It supports the Mica effect on Windows 11.


## Installation

### Installer

Installers for Koncentro are available for Windows, macOS and Linux. You can download the latest install from the [releases page](https://github.com/kun-codes/Koncentro/releases/latest)

<details>
<summary><strong>From Source (Advanced)</strong></summary>

#### From Source

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
</details>

## Usage

1. Install Koncentro from the releases above or from source as described above.
2. Add your tasks in **tasks list** to get started.
3. Use the Pomodoro timer from **timer screen** to start a Pomodoro session
4. Configure website blocking in the **website blocker screen** by adding websites to the blocklist or allowlist.
5. Switch and create different workspaces using the **workspace manager** to manage separate sets of tasks and settings.

## Screenshots

### Task Lists
![To Do Task List](screenshots/win_tasks_list.png)

### Pomodoro Timer
![Pomodoro Timer](screenshots/win_pomodoro_timer.png)

### Website Blocker
![Website Blocker](screenshots/win_website_blocker.png)

### Workspace Manager
![Workspace Manager](screenshots/win_workspace_manager.png)

### Settings
![Settings](screenshots/win_settings.png)

## Known Bugs

- App doesn't change theme correctly without restarting when OS theme is changed.

## License
This project is licensed under the [GPL-3.0-or-later license](LICENSE).

## Credits

- [Super Productivity](https://github.com/johannesjo/super-productivity): The app is inspired by Super Productivity.
- [chomper](https://github.com/aniketpanjwani/chomper): The website blocker has some functionality inspired by chomper.
- [Flowkeeper](https://github.com/flowkeeper-org/fk-desktop): Installer creation scripts have been adapted from Flowkeeper.
- [Flathub Banner Preview](https://docs.flathub.org/banner-preview): For the banner image used in the README.
