# Replication And AI Usage Document

## Project

**Project title:** Realtime Stock Simulator  
**Student:** Yi He  
**Course:** INFOSCI 102 Final Project

This document explains how to reproduce the project from scratch and discloses AI tools, prompts, external resources, and AI-assisted contributions. It is written to satisfy the final project requirement that another person should be able to rerun the project and understand how it was built.

## 1. Replication Instructions

### 1.1 Tested Environment

The project was tested locally on:

- Operating system: Microsoft Windows 11 Home Chinese Edition
- OS version: 10.0.26200
- System type: x64-based PC
- Python: 3.14.0
- matplotlib: 3.10.7
- IPython: 9.7.0
- ipywidgets: 8.1.8

The project was also designed to support:

- Google Colab
- Jupyter Notebook / JupyterLab
- Normal Python desktop execution with Tkinter

### 1.2 Required Software

Install Python 3.11 or newer. The local tested version was Python 3.14.0.

Install dependencies from the repository root:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file includes:

```text
matplotlib
ipywidgets
ipython
```

For normal Python GUI mode, the program uses `tkinter`. Tkinter is usually included with standard Python installations. If it is missing, install a Python distribution that includes Tk support.

### 1.3 Required Data Or Model Weights

No external dataset, API key, model weight, account, or paid service is required. The stock price data is generated inside the program by a random price simulation engine.

### 1.4 Repository Files

Important files:

- `realtime_stock_simulator_skeleton.py`: main project source code.
- `requirements.txt`: Python dependencies.
- `README.md`: short project overview and usage examples.
- `REPLICATION_AND_AI_USAGE.md`: this replication and AI disclosure document.

### 1.5 How To Run In Normal Python

From the repository root, run:

```bash
python realtime_stock_simulator_skeleton.py
```

Expected behavior:

1. A Tkinter window opens.
2. The window shows the tutorial and difficulty buttons: Easy, Normal, and Hard.
3. After choosing a difficulty, the game interface opens with trading buttons, a realtime chart, and portfolio status.
4. The stock price updates automatically.
5. The player can buy and sell shares, pause/resume the auto update, restart the current difficulty, or return to the main menu.
6. When the game ends, the terminal prints collected game-end data and the trade log.

### 1.6 How To Run In Jupyter Notebook

Open a Jupyter Notebook in the repository folder and run:

```python
from realtime_stock_simulator_skeleton import create_simulator

game = create_simulator()
```

Expected behavior:

1. The notebook displays the tutorial and difficulty buttons.
2. After choosing a difficulty, the widget-based game interface appears.
3. The price chart and status panel update in the notebook.
4. The player can use Buy, Sell, Next Tick, Start Auto, Pause Auto, Restart, and Main Menu.

### 1.7 How To Run In Google Colab

Upload `realtime_stock_simulator_skeleton.py` to the Colab runtime or clone/download the repository into Colab. Then run:

```python
from realtime_stock_simulator_skeleton import create_simulator

game = create_simulator()
```

Expected behavior:

1. The notebook displays the tutorial and difficulty buttons.
2. After choosing a difficulty, the widget-based game interface appears.
3. The Colab version uses Colab's widget manager and a browser-side timer callback to support automatic updates.
4. The player can trade and control the game through the displayed buttons.

If Colab widgets do not render correctly, restart the Colab runtime and rerun the setup cell. Colab's frontend can keep old callbacks from previous runs, so restarting the runtime is the safest way to test a fresh copy.

### 1.8 How To Verify Success

The project is working if:

- A difficulty menu appears.
- Selecting a difficulty starts a playable stock simulator.
- The chart updates over time.
- Buying and selling shares changes cash, shares, average cost, and total assets.
- Restart resets the current difficulty.
- Main Menu returns to the tutorial and difficulty selection screen.
- In normal Python mode, the terminal prints game-end data and the trade log when the game ends.

## 2. AI Use And External Resources Disclosure

### 2.1 AI Tools Used

AI tools used:

- OpenAI ChatGPT / Codex in the Codex desktop environment.
- Model family shown by the environment: GPT-5-based Codex.

The AI assistant was used as a programming and documentation collaborator. I remained responsible for the project idea, design decisions, testing decisions, and final submitted code.

### 2.2 Consolidated Prompt Documentation

The following are consolidated versions of the non-trivial prompts used during development. Some prompts were written in Chinese and are paraphrased here so the workflow can be reproduced.

1. Debug notebook behavior:

```text
Inspect realtime_stock_simulator_skeleton.py. The game is intended to run in Google Colab or Jupyter Notebook, but after selecting difficulty nothing happens and the chart does not update automatically. Do not modify code yet; identify the problem.
```

2. Fix notebook/Colab display:

```text
Modify the current issue without changing the underlying game logic. Fix the difficulty-selection display and automatic chart updating for Colab/Jupyter. Comments should match the existing style and Colab-specific parts should be marked.
```

3. Separate environment-specific behavior:

```text
Use the existing runtime-detection method so Colab-specific changes only run in Google Colab. The same code should also work in Jupyter.
```

4. Add normal Python GUI:

```text
Add a graphical interface for normal Python execution. Widgets are not suitable for normal Python, so use another visualization method while preserving the game logic.
```

5. Explain and validate backend logic:

```text
Check whether all three graphical interfaces are driven by the same game loop or shared game-step logic. I want to fix a win/loss bug without breaking the frontend.
```

6. Add restart and main-menu controls:

```text
Add a Restart button that works in all three environments, even after win/loss. Then add a Main Menu button for all three environments that returns to the initial tutorial and difficulty selection screen.
```

7. Debug total asset jumps:

```text
Re-check the total assets calculation. During gameplay, total assets sometimes jumps from around 7000 to 13000. Identify whether the formula is wrong or another part of the code is resetting state.
```

8. Add data collection:

```text
Add a Python-environment interface to collect raw status data like render_status and print it when the game ends. Also include the full trade log at the end.
```

9. Prepare GitHub files:

```text
Create a GitHub-ready project folder without modifying the original source code. Add README.md, requirements.txt, .gitignore, initialize Git, and help prepare the repository for upload.
```

10. Write replication and AI usage document:

```text
Read the INFOSCI 102 final project PDF. Generate a replication and AI usage document in Markdown in the Git repository path, making sure the requirements are fully understood before writing.
```

### 2.3 What AI Contributed

AI assistance contributed to:

- Diagnosing why widget updates worked differently in Jupyter and Google Colab.
- Suggesting the separation of Colab, Jupyter, and normal Python execution paths.
- Helping implement Colab-specific callback logic for automatic updates.
- Helping implement a Tkinter + Matplotlib GUI for normal Python execution.
- Refactoring shared gameplay update logic so multiple frontends could call the same backend step.
- Adding Restart and Main Menu controls across all supported environments.
- Identifying the dynamic difficulty bug where `applyDifficulty()` reset player cash during gameplay.
- Adding normal Python end-game status-data collection and trade-log output.
- Creating README, `.gitignore`, `requirements.txt`, and this replication/AI usage document.
- Providing Git and GitHub workflow guidance, including Git proxy configuration troubleshooting.

### 2.4 Student-Authored Contributions

The student-authored parts include:

- The original project idea: a realtime stock trading simulator game.
- The initial source code structure, including portfolio logic, price engine, difficulty design, and trading rules.
- Design choices for Easy, Normal, and Hard difficulty settings.
- Decisions about the win/loss rule, including moving win/loss checks away from automatic price ticks.
- Iterative testing feedback, including reporting Colab-specific failures and total asset jumps.
- Final acceptance or rejection of code-design suggestions.
- Repository ownership and submission preparation.

### 2.5 External Resources Used

External resources and libraries:

- Python standard library: `asyncio`, `io`, `random`, `dataclasses`, `typing`, `time`, `threading`, and `tkinter`.
- Matplotlib: used for plotting the stock price chart.
- ipywidgets: used for notebook and Colab buttons, inputs, images, and status display.
- IPython display tools: used for notebook display and Colab JavaScript callback integration.
- Google Colab output callback mechanism: used conceptually for Colab auto-update behavior through `google.colab.output.register_callback()` and `google.colab.kernel.invokeFunction()`.
- INFOSCI 102 final project PDF: used to identify the required submission and documentation components.

No external dataset, copied repository, tutorial project, API, or pretrained model was used as the basis for the simulator.

### 2.6 Accountability Statement

I reviewed and tested the code behavior during development. I understand the core project logic: the price engine generates simulated stock prices, the portfolio tracks cash and shares, difficulty settings configure starting conditions and market behavior, and separate frontends call shared backend update methods for Colab, Jupyter, and normal Python execution.
