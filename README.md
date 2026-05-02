# Realtime Stock Simulator

By Yi He.

This project is a realtime stock trading simulator game built for INFOSCI 102. The player chooses a difficulty level, watches a simulated stock price change over time, buys and sells shares, and tries to reach the target asset value without falling below the loss limit.

## What I Built

I built a Python stock simulator that can run in Google Colab, Jupyter Notebook, or as a normal Python GUI. It includes difficulty settings, automatic price updates, trading controls, portfolio tracking, restart/main-menu controls, and win/loss conditions.

## Inputs And Outputs

- Inputs: difficulty level, share quantity, Buy/Sell/Next Tick/Start Auto/Pause Auto/Restart/Main Menu button actions.
- Outputs: realtime stock price chart, current cash, shares, average cost, total assets, target/loss values, and status messages.
- Example notebook usage:

```python
from realtime_stock_simulator_skeleton import create_simulator

game = create_simulator()
```

- Example normal Python usage:

```bash
python realtime_stock_simulator_skeleton.py
```

## Replication Document

See the replication document for setup details, environment notes, and steps to reproduce the project behavior.
