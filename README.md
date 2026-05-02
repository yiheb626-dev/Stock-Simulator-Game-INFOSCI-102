# Realtime Stock Simulator

A simple realtime stock trading simulator for Google Colab, Jupyter Notebook, and normal Python GUI.

## Features

- Difficulty selection: Easy, Normal, and Hard.
- Realtime stock price simulation.
- Buy and sell shares at the current market price.
- Portfolio display with cash, shares, average cost, and total assets.
- Supports Google Colab, Jupyter Notebook, and normal Python desktop execution.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

`tkinter` is used for normal Python GUI mode and is usually included with standard Python installations.

## Run In Google Colab Or Jupyter

```python
from realtime_stock_simulator_skeleton import create_simulator

game = create_simulator()
```

## Run As Normal Python

```bash
python realtime_stock_simulator_skeleton.py
```

## Files

- `realtime_stock_simulator_skeleton.py`: Main simulator source code.
- `requirements.txt`: Python dependencies.
- `.gitignore`: Files ignored by Git.
