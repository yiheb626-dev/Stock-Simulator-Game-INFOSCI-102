from __future__ import annotations # Optional
import asyncio
import io
import random
from dataclasses import dataclass, field, replace
from typing import List, Optional
import time
import threading # Added for Colab auto-run.
import matplotlib.pyplot as plt

try:
    import ipywidgets as widgets
    from IPython.display import clear_output, display
except ImportError:
    widgets = None
    clear_output = None
    display = None


INITIAL_CASH = 12_000.0
INITIAL_PRICE = 100.0
UPDATE_INTERVAL = 1.0
VISIBLE_WINDOW_SECONDS = 10.0
TRADING_FEE_RATE = 0.001
GAME_TUTORIAL = (
    'How to play:\n'
    '1. Choose a difficulty to start the game.\n'
    '2. The stock price updates automatically over time.\n'
    '3. Enter a share quantity, then use Buy or Sell to trade at the current price.\n'
    '4. Your goal is to grow your assets to the target value without falling below the loss limit.\n'
    '5. Use Pause Auto or Start Auto if you want to control the automatic updates.'
)



@dataclass
class PriceEngine:
    current_price: float = INITIAL_PRICE
    drift: float = 0.0 # The long-term trend of the stock price. For example: if drift>0, price will eventually rise.
    volatility: float = 0.01 # The amplitude of stock price.

    trend_bias: float = 0.0
    trend_t_remaining: int = 0
    trend_change_chance: float = 0.0
    trend_change_point: float = 0.35
    min_trend_interval: int = 3
    max_trend_interval: int = 8
    trend_strength_range: float = 0.02

    def trend(self) -> None:
        # Determine the strength of a trend or whether to start a trend.
        if self.trend_t_remaining > 0:
            return
        else:
            self.trend_bias = 0.0
            temp_rate = random.uniform(0, 0.1)
            temp_chance = self.trend_change_chance + temp_rate

            if temp_chance < self.trend_change_point:
                self.trend_change_chance += temp_rate
            else:
                self.trend_change_chance = 0.0
                direc = random.choice([-1, 1])
                strength = random.uniform(self.trend_strength_range * 0.5, self.trend_strength_range)

                self.trend_bias = direc * strength
                self.trend_t_remaining = random.randint(self.min_trend_interval, self.max_trend_interval)

    def nextPrice(self) -> float:
        # Generate the next stock price using a random update rule.
        # This function should be the only place that controls price movement.
        self.trend()

        noise = random.gauss(0, self.volatility) # First argument: average, Second: amplitude.
        k = self.drift + self.trend_bias + noise
        new_price = self.current_price * (1 + k)
        self.current_price = max(0.01, new_price) # Prevent the price to fall below 0.

        if self.trend_t_remaining > 0:
            self.trend_t_remaining -= 1

        return self.current_price


@dataclass
class Portfolio:
    cash: float = INITIAL_CASH
    shares: int = 0
    avg_cost: float = 0.0
    fee_rate: float = TRADING_FEE_RATE
    trade_log: List[dict] = field(default_factory=list)

    def validateTradeInputs(self, price: float, quantity: int, timestamp: float) -> Optional[str]:
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            return 'Quantity must be an integer.'

        if quantity <= 0:
            return 'Quantity must be greater than 0.'

        if isinstance(price, bool) or not isinstance(price, (int, float)):
            return 'Price must be a number.'

        if price <= 0:
            return 'Price must be greater than 0.'

        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            return 'Timestamp must be a number.'

        if timestamp < 0:
            return 'Timestamp must be non-negative.'

        return None

    def buy(self, price: float, quantity: int, timestamp: float) -> str:
        # Buy shares at the current price and update cash, holdings, and trade history.
        validation_error = self.validateTradeInputs(price, quantity, timestamp)
        if validation_error is not None:
            return validation_error

        stock_cost = price * quantity
        fee = stock_cost * self.fee_rate
        total_cost = stock_cost + fee

        if total_cost > self.cash:
            return 'Not enough cash to complete this purchase.'

        prev_shares = self.shares
        prev_stock_cost = self.avg_cost * prev_shares

        self.cash -= total_cost
        self.shares += quantity
        self.avg_cost = (prev_stock_cost + total_cost) / self.shares

        self.trade_log.append(
            {
                'type': 'buy',
                'price': price,
                'quantity': quantity,
                'fee': fee,
                'timestamp': timestamp,
            }
        )

        return f'Bought {quantity} shares at ${price:.2f}.'

    def sell(self, price: float, quantity: int, timestamp: float) -> str:
        # Sell shares at the current price and update cash, holdings, and trade history.
        validation_error = self.validateTradeInputs(price, quantity, timestamp)
        if validation_error is not None:
            return validation_error

        if self.shares < quantity:
            return 'Not enough shares to sell.'

        stock_rev = price * quantity
        fee = stock_rev * self.fee_rate
        total_rev = stock_rev - fee

        self.cash += total_rev
        self.shares -= quantity

        if self.shares == 0:
            self.avg_cost = 0.0

        self.trade_log.append(
            {
                'type': 'sell',
                'price': price,
                'quantity': quantity,
                'fee': fee,
                'timestamp': timestamp,
            }
        )

        return f'Sold {quantity} shares at ${price:.2f}.'


    def totalAssets(self, current_price: float) -> float:
        # Return the total portfolio value using cash plus the market value of shares.
        return self.cash + self.shares * current_price



class RealtimeStockSimulator:
    def __init__(
        self,
        initial_cash: float = INITIAL_CASH,
        initial_price: float = INITIAL_PRICE,
        update_interval: float = UPDATE_INTERVAL,
        visible_window: float = VISIBLE_WINDOW_SECONDS,
    ):
        # Store the main objects and the data needed for the rolling chart.
        self.engine = PriceEngine(current_price=initial_price)
        self.portfolio = Portfolio(cash=initial_cash)
        self.difficulty: Optional[Difficulty] = None
        self.base_difficulty: Optional[Difficulty] = None
        self.initial_cash = initial_cash
        self.initial_price = initial_price
        self.target_asset = 14000
        self.min_asset = 4000

        self.update_interval = update_interval
        self.visible_window = visible_window
        self.last_difficulty_update = 0.0

        self.start_time: Optional[float] = None
        self.times: List[float] = []
        self.prices: List[float] = []
        self.asset_values: List[float] = []

        self.status_message = ''
        self.is_running = False # Added for Colab auto-run.
        self.game_thread: Optional[threading.Thread] = None # Added for Colab auto-run.
        self.game_task: Optional[asyncio.Task] = None # Added for Jupyter auto-run.
        self.colab_callback_name = f'realtime_stock_simulator_tick_{id(self)}' # Added for Colab auto-run.
        self.colab_timer_name = f'realtimeStockSimulatorTimer{id(self)}' # Added for Colab auto-run.
        self.state_lock = threading.RLock() # Added for Colab auto-run.

    def detectRuntimeEnvironment(self) -> str:
        # Check the current running environment.
        try:
            import google.colab
            return 'colab'
        except ImportError:
            pass

        try:
            from IPython import get_ipython
            shell = get_ipython()
            if shell is None:
                return 'python'

            shell_name = shell.__class__.__name__
            if shell_name == 'ZMQInteractiveShell':
                return 'jupyter'
            if shell_name == 'TerminalInteractiveShell':
                return 'ipython'

            return 'ipython'
        except Exception:
            return 'python'

    def prepareWidgetEnvironment(self) -> None:
        # Enable the Colab widget manager before displaying ipywidgets.
        if self.detectRuntimeEnvironment() != 'colab':
            return

        try:
            from google.colab import output
            output.enable_custom_widget_manager()
        except Exception:
            pass

    def configDifficulty(self, difficulty: Difficulty) -> None:
        self.base_difficulty = replace(difficulty)
        self.difficulty = replace(difficulty)
        self.difficulty.applyDifficulty(self)

    def resetGameState(self) -> None:
        # Reset the gameplay state while keeping the selected difficulty.
        with self.state_lock:
            self.engine = PriceEngine(current_price=self.initial_price)
            self.portfolio = Portfolio(cash=self.initial_cash)
            self.target_asset = 14000
            self.min_asset = 4000
            self.last_difficulty_update = 0.0
            self.start_time = None
            self.times = []
            self.prices = []
            self.asset_values = []

            if self.base_difficulty is not None:
                self.difficulty = replace(self.base_difficulty)
                self.difficulty.applyDifficulty(self)

            self.status_message = 'Game restarted.'

    def cancelAutoLoop(self) -> None:
        # Stop any active auto-run timer before restarting the game.
        self.is_running = False
        if self.detectRuntimeEnvironment() == 'colab':
            self.stopColabLoop()
        if self.game_task is not None and not self.game_task.done():
            self.game_task.cancel()
        self.game_task = None
        if getattr(self, 'python_after_id', None) is not None:
            try:
                self.python_root.after_cancel(self.python_after_id)
            except Exception:
                pass
            self.python_after_id = None
        if hasattr(self, 'python_running'):
            self.python_running = False

    def restartGame(self, auto_start: bool = True) -> None:
        # Restart the game and optionally resume automatic updates.
        self.cancelAutoLoop()
        self.resetGameState()
        if auto_start:
            self.startAutoLoop()

    def resetInitialState(self) -> None:
        # Reset the simulator to the state before any difficulty is selected.
        with self.state_lock:
            self.engine = PriceEngine(current_price=self.initial_price)
            self.portfolio = Portfolio(cash=self.initial_cash)
            self.difficulty = None
            self.base_difficulty = None
            self.target_asset = 14000
            self.min_asset = 4000
            self.last_difficulty_update = 0.0
            self.start_time = None
            self.times = []
            self.prices = []
            self.asset_values = []
            self.status_message = ''

    def returnToMainMenu(self) -> None:
        # Return to the difficulty selection menu from any supported interface.
        self.cancelAutoLoop()
        self.resetInitialState()

        if self.detectRuntimeEnvironment() == 'python':
            self.returnToPythonMainMenu()
        else:
            self.returnToNotebookMainMenu()

    def returnToNotebookMainMenu(self) -> None:
        # Restore the notebook difficulty selection menu.
        if hasattr(self, 'notebook_difficulty_buttons'):
            for button in self.notebook_difficulty_buttons:
                button.disabled = False
        if hasattr(self, 'notebook_game_area'):
            self.notebook_game_area.children = []

    def returnToPythonMainMenu(self) -> None:
        # Restore the Tkinter difficulty selection menu.
        if hasattr(self, 'python_game_frame'):
            self.python_game_frame.destroy()
            del self.python_game_frame
        if hasattr(self, 'python_fig'):
            plt.close(self.python_fig)
        self.buildPythonDifficultyUI(self.python_root, self.python_figure_canvas_class)

    def buildDifficultySelector(self):
        if widgets is None or display is None:
            raise RuntimeError('ipywidgets and IPython are required for notebook mode.')

        self.prepareWidgetEnvironment() # Added for Colab widget display.

        # Create the title for the difficulty selection menu.
        title = widgets.HTML('<h3>Select Difficulty</h3>')
        tutorial = widgets.HTML(f'<pre>{GAME_TUTORIAL}</pre>')
        game_area = widgets.VBox() # Added for Colab/Jupyter widget display.
        self.notebook_game_area = game_area

        # Create the buttons for each difficulty level.
        easy_button = widgets.Button(description='Easy', button_style='success')
        normal_button = widgets.Button(description='Normal', button_style='info')
        hard_button = widgets.Button(description='Hard', button_style='danger')
        self.notebook_difficulty_buttons = [easy_button, normal_button, hard_button]

        def select_difficulty(difficulty: Difficulty, message: str) -> None:
            # Switch from the difficulty menu to the game UI without clearing the whole notebook cell.
            self.configDifficulty(difficulty)
            self.status_message = message
            easy_button.disabled = True
            normal_button.disabled = True
            hard_button.disabled = True
            game_area.children = [self.buildWidgets(display_ui=False)]
            self.startAutoLoop() # Added for Colab auto-run.
            self.redraw()

        # Handle the easy difficulty selection.
        def on_easy_clicked(_):
            select_difficulty(EASY_DIFFICULTY, 'Easy difficulty selected.')

        # Handle the normal difficulty selection.
        def on_normal_clicked(_):
            select_difficulty(NORMAL_DIFFICULTY, 'Normal difficulty selected.')

        # Handle the hard difficulty selection.
        def on_hard_clicked(_):
            select_difficulty(HARD_DIFFICULTY, 'Hard difficulty selected.')

        # Bind the buttons to their callback functions.
        easy_button.on_click(on_easy_clicked)
        normal_button.on_click(on_normal_clicked)
        hard_button.on_click(on_hard_clicked)

        # Arrange the difficulty buttons into one layout.
        buttons = widgets.HBox([easy_button, normal_button, hard_button])
        ui = widgets.VBox([title, tutorial, buttons, game_area])

        # Display the difficulty selection interface.
        display(ui)

        return ui

    def recordPoint(self, elapsed: float, price: float) -> None:
        # Save one new time-price point after each update tick.
        self.times.append(elapsed)
        self.prices.append(price)
        self.asset_values.append(self.portfolio.totalAssets(price))

    def updateOnce(self) -> None:
        # Advance the simulation by one step and record the new price.
        with self.state_lock:
            if self.start_time is None:
                self.start_time = time.time() # Gets the current time. Its value is not important since we only care about the elapsed time.
            elapsed = time.time() - self.start_time # Gets the elapsed time.
            new_price = self.engine.nextPrice()
            self.recordPoint(elapsed, new_price)

    def buy(self, quantity: int) -> None:
        # Execute a buy action using the latest available stock price.
        with self.state_lock:
            price = self.engine.current_price
            if self.start_time is None:
                self.status_message = f'{self.portfolio.buy(price, quantity, 0.0)}'
                return
            self.status_message = f'{self.portfolio.buy(price, quantity, time.time() - self.start_time)}'


    def sell(self, quantity: int) -> None:
        # Execute a sell action using the latest available stock price.
        with self.state_lock:
            price = self.engine.current_price
            if self.start_time is None:
                self.status_message = f'{self.portfolio.sell(price, quantity, 0.0)}'
                return
            self.status_message = f'{self.portfolio.sell(price, quantity, time.time() - self.start_time)}'

            self.checkWinLoss()

    def checkWinLoss(self) -> None:
        total_assets = self.portfolio.totalAssets(self.engine.current_price)
        if total_assets >= self.target_asset:
            self.status_message = f'Congratulations! Your total asset reached ${self.target_asset}.\n You win!'
            self.is_running = False
        elif total_assets <= self.min_asset:
            self.status_message = f'You are losing too much money! Time to flee from the stock market and get a job.\n You lose!'
            self.is_running = False


    def getVisibleData(self) -> tuple[list[float], list[float]]:
        # Return only the recent data points inside the visible time window. (Last 10 seconds.)
        if self.times == [] or self.prices == []:
            return ([], [])

        last_visible_time = self.times[-1] - self.visible_window
        visible_times = []
        visible_prices = []
        for t in range(len(self.times)):
            if self.times[t] >= last_visible_time:
                visible_times.append(self.times[t])
                visible_prices.append(self.prices[t])

        return (visible_times, visible_prices)

    def compute_Y_Limits(self, visible_prices: List[float]) -> tuple[float, float]:
        # Compute dynamic y-axis limits so the recent chart stays readable.
        if not visible_prices:
            return (INITIAL_PRICE - 5, INITIAL_PRICE + 5) # The starting case.

        min_price_visible = min(visible_prices)
        max_price_visible = max(visible_prices)
        gap = abs(max_price_visible - min_price_visible)

        if min_price_visible != max_price_visible:
            return (min_price_visible - gap * 0.1, max_price_visible + gap * 0.1) # Leave a small margin to make the graph look good.

        return (min_price_visible - 5, max_price_visible + 5) # In case the min and max prices are equal.

    def renderChart(self) -> None:
        # Draw the realtime price chart using Matplotlib.
        # Take only data from the last 10 seconds. (Visible window = 10.)
        # This is only used in Colab/Jupyter.
        visible_times, visible_prices = self.getVisibleData() # Get data for x & y axis.
        y_floor, y_ceil = self.compute_Y_Limits(visible_prices) # The upper and lower bound of the graph.

        # Use Matplotlib to draw the graph.
        fig, ax = plt.subplots(figsize=(8, 4)) # Create a new graph.
        ax.plot(visible_times, visible_prices, color='blue', linewidth=2)
        ax.set_title('Recent Stock Price')

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Price ($)')

        if not visible_times or visible_times[-1] < self.visible_window:
            ax.set_xlim(0, self.visible_window)
        else:
            ax.set_xlim(min(visible_times), max(visible_times))
        ax.set_ylim(y_floor, y_ceil)

        ax.grid(True)
        fig.tight_layout()

        if hasattr(self, 'chart_widget'):
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            self.chart_widget.value = buffer.getvalue()
        else:
            plt.show()

        plt.close(fig)

    def renderStatus(self) -> None:
        # Print the current price, cash, shares, and total assets.
        status = self.getStatusText()
        if hasattr(self, 'status_widget'):
            self.status_widget.value = f'<pre>{status}</pre>'
        else:
            print(status)

    def getStatusText(self) -> str:
        # Build the current status text for notebook and Python GUI displays.
        return (f'Current price: ${self.engine.current_price:.2f}\n'
                f'Average cost: ${self.portfolio.avg_cost:.2f}\n'
                f'Cash: ${self.portfolio.cash:.2f}\n'
                f'Shares: {self.portfolio.shares}\n'
                f'Total assets: ${self.portfolio.totalAssets(self.engine.current_price):.2f}\n'
                f'Win & Lose assets: {self.difficulty.target_asset}, {self.difficulty.min_asset}\n'
                f'Last move: {self.status_message}')

    def redraw(self) -> None:
        # Refresh the chart and status output after each update or trade.
        with self.state_lock:
            if hasattr(self, 'chart_widget') and hasattr(self, 'status_widget'):
                self.renderChart()
                self.renderStatus()
            else:
                if clear_output is not None:
                    clear_output(wait=True)
                self.renderChart()
                self.renderStatus()

    def runFor_N_Seconds(self, seconds: int) -> None:
        '''
        This is a method ONLY for testing purposes. It can test whether the graph is displaying correctly.
        :param seconds: How long do I want this program to run?
        :return: None
        '''
        for t in range(seconds):
            self.updateOnce()
            self.redraw()
            time.sleep(self.update_interval)

    def runGameStep(self) -> None:
        # Run one gameplay step using the same win/loss and price update rules.
        if not self.difficulty:
            target_asset = self.target_asset
            min_asset = self.min_asset
        else:
            target_asset = self.difficulty.target_asset
            min_asset = self.difficulty.min_asset


        with self.state_lock:
            total_assets = self.portfolio.totalAssets(self.engine.current_price)
            if self.start_time is None:
                self.start_time = time.time()
            elapsed = time.time() - self.start_time
            new_price = self.engine.nextPrice()
            # Update the dynamic difficulty every 10 seconds.
            if (
                    self.difficulty is not None
                    and self.difficulty.dynamic_enabled
                    and elapsed - self.last_difficulty_update >= 10
            ):
                self.difficulty.dynamicDifficulty(self)
                self.last_difficulty_update = elapsed

            self.recordPoint(elapsed, new_price)

    def gameLoop(self):
        # This is the method that is working in the gameplay.
        while self.is_running:
            self.runGameStep()
            self.redraw()
            if self.is_running:
                time.sleep(self.update_interval)

    async def asyncGameLoop(self):
        # Run the gameplay loop on the notebook event loop for Jupyter widget updates.
        while self.is_running:
            self.runGameStep()
            self.redraw()
            if self.is_running:
                await asyncio.sleep(self.update_interval)

    def colabAutoTick(self) -> None:
        # Run one game tick from the Colab browser timer.
        if not self.is_running:
            return
        self.runGameStep()
        self.redraw()
        if not self.is_running:
            self.stopColabLoop()

    def startColabLoop(self) -> None:
        # Start a Colab browser timer that calls Python once per tick.
        if self.detectRuntimeEnvironment() != 'colab':
            return

        try:
            from google.colab import output
            from IPython.display import Javascript
            output.register_callback(self.colab_callback_name, self.colabAutoTick)
        except Exception:
            self.is_running = False
            self.status_message = 'Colab auto-run could not start.'
            return

        interval_ms = max(250, int(self.update_interval * 1000))
        display(Javascript(f'''
            (function() {{
                const timerName = {self.colab_timer_name!r};
                const busyName = timerName + 'Busy';
                if (window[timerName]) {{
                    clearInterval(window[timerName]);
                }}
                window[busyName] = false;
                window[timerName] = setInterval(async function() {{
                    if (window[busyName]) {{
                        return;
                    }}
                    window[busyName] = true;
                    try {{
                        await google.colab.kernel.invokeFunction({self.colab_callback_name!r}, [], {{}});
                    }} catch (error) {{
                        clearInterval(window[timerName]);
                        window[timerName] = null;
                        console.error(error);
                    }} finally {{
                        window[busyName] = false;
                    }}
                }}, {interval_ms});
            }})();
        '''))

    def stopColabLoop(self) -> None:
        # Stop the Colab browser timer for widget-based autoplay.
        if self.detectRuntimeEnvironment() != 'colab':
            return

        from IPython.display import Javascript

        display(Javascript(f'''
            (function() {{
                const timerName = {self.colab_timer_name!r};
                const busyName = timerName + 'Busy';
                if (window[timerName]) {{
                    clearInterval(window[timerName]);
                    window[timerName] = null;
                }}
                window[busyName] = false;
            }})();
        '''))

    def startAutoLoop(self) -> None: # Method added for Colab auto-run.
        # Start the game loop for widget-based autoplay.
        if self.is_running:
            return
        self.status_message = 'Auto-run started.'
        self.is_running = True

        if self.detectRuntimeEnvironment() == 'colab':
            self.startColabLoop()
            return

        if self.detectRuntimeEnvironment() == 'jupyter':
            try:
                loop = asyncio.get_running_loop()
                self.game_task = loop.create_task(self.asyncGameLoop())
                return
            except RuntimeError:
                pass

        self.game_thread = threading.Thread(target=self.gameLoop, daemon=True)
        self.game_thread.start()

    def stopAutoLoop(self) -> None: # Method added for Colab auto-run.
        # Stop the game loop for widget-based autoplay.
        self.is_running = False
        if self.detectRuntimeEnvironment() == 'colab':
            self.stopColabLoop()
        if self.game_task is not None and not self.game_task.done():
            self.game_task.cancel()
        self.game_task = None
        self.status_message = 'Auto-run paused.'
        self.redraw()

    def buildWidgets(self, display_ui: bool = True):
        if widgets is None or display is None:
            raise RuntimeError('ipywidgets and IPython are required for notebook mode.')

        self.prepareWidgetEnvironment() # Added for Colab widget display.

        # Create the input box for the number of shares to trade.
        quantity_input = widgets.BoundedIntText(
            value=1,
            min=1,
            max=1000,
            step=1,
            description='Shares:'
        )

        # Create the main control buttons for trading and manual ticking.
        buy_button = widgets.Button(description='Buy', button_style='success')
        sell_button = widgets.Button(description='Sell', button_style='danger')
        tick_button = widgets.Button(description='Next Tick') # Only for testing purposes.
        start_button = widgets.Button(description='Start Auto', button_style='info') # Added for Colab auto-run.
        pause_button = widgets.Button(description='Pause Auto', button_style='warning') # Added for Colab auto-run.
        restart_button = widgets.Button(description='Restart', button_style='primary')
        main_menu_button = widgets.Button(description='Main Menu', button_style='')

        # Create separate display widgets for the chart and the status panel.
        self.chart_widget = widgets.Image(format='png')
        self.status_widget = widgets.HTML()

        # Handle the buy action and refresh the display.
        def on_buy_clicked(_):
            self.buy(quantity_input.value)
            self.redraw()

        # Handle the sell action and refresh the display.
        def on_sell_clicked(_):
            self.sell(quantity_input.value)
            self.redraw()

        # Advance the simulation by one step and refresh the display.
        def on_tick_clicked(_):
            self.updateOnce()
            self.redraw()

        # Handle the start-auto action and refresh the display. # Added for Colab auto-run.
        def on_start_clicked(_):
            self.startAutoLoop()
            self.redraw()

        # Handle the pause-auto action and refresh the display. # Added for Colab auto-run.
        def on_pause_clicked(_):
            self.stopAutoLoop()

        # Handle the restart action and refresh the display.
        def on_restart_clicked(_):
            self.restartGame()
            self.redraw()

        # Handle the main-menu action and return to the difficulty menu.
        def on_main_menu_clicked(_):
            self.returnToMainMenu()

        # Bind the buttons to their callback functions.
        buy_button.on_click(on_buy_clicked)
        sell_button.on_click(on_sell_clicked)
        tick_button.on_click(on_tick_clicked)
        start_button.on_click(on_start_clicked)
        pause_button.on_click(on_pause_clicked)
        restart_button.on_click(on_restart_clicked)
        main_menu_button.on_click(on_main_menu_clicked)

        # Arrange the controls and output panels into one widget layout.
        controls = widgets.HBox([quantity_input, buy_button, sell_button, tick_button, start_button, pause_button, restart_button, main_menu_button]) # Added for Colab auto-run.
        ui = widgets.VBox([controls, self.chart_widget, self.status_widget])

        # Display the widget layout and draw the initial state.
        if display_ui:
            display(ui)
        self.redraw()

        # Return the full widget interface.
        return ui

    def buildPythonGUI(self):
        # Build a Tkinter interface for running the simulator as a normal Python program.
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        root = tk.Tk()
        root.title('Realtime Stock Simulator')

        self.python_root = root
        self.python_figure_canvas_class = FigureCanvasTkAgg
        self.python_after_id = None
        self.python_running = False

        self.buildPythonDifficultyUI(root, FigureCanvasTkAgg)

        root.mainloop()

    def buildPythonDifficultyUI(self, root, figure_canvas_class) -> None:
        # Create the difficulty selection screen for normal Python mode.
        import tkinter as tk

        difficulty_frame = tk.Frame(root, padx=16, pady=16)
        difficulty_frame.pack(fill=tk.BOTH, expand=True)
        self.python_difficulty_frame = difficulty_frame

        title_label = tk.Label(difficulty_frame, text='Select Difficulty', font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 12))

        tutorial_label = tk.Label(difficulty_frame, text=GAME_TUTORIAL, justify=tk.LEFT, anchor='w')
        tutorial_label.pack(fill=tk.X, pady=(0, 12))

        button_frame = tk.Frame(difficulty_frame)
        button_frame.pack()

        def start_game(difficulty: Difficulty, message: str) -> None:
            # Switch from the Python difficulty menu to the Python game UI.
            self.configDifficulty(difficulty)
            self.status_message = message
            difficulty_frame.destroy()
            self.buildPythonGameUI(root, figure_canvas_class)

        tk.Button(button_frame, text='Easy', width=12, command=lambda: start_game(EASY_DIFFICULTY, 'Easy difficulty selected.')).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text='Normal', width=12, command=lambda: start_game(NORMAL_DIFFICULTY, 'Normal difficulty selected.')).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text='Hard', width=12, command=lambda: start_game(HARD_DIFFICULTY, 'Hard difficulty selected.')).pack(side=tk.LEFT, padx=4)

    def buildPythonGameUI(self, root, figure_canvas_class) -> None:
        # Build the main Tkinter game interface for normal Python mode.
        import tkinter as tk

        main_frame = tk.Frame(root, padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.python_game_frame = main_frame

        controls = tk.Frame(main_frame)
        controls.pack(fill=tk.X, pady=(0, 8))

        tk.Label(controls, text='Shares:').pack(side=tk.LEFT)
        quantity_var = tk.IntVar(value=1)
        quantity_input = tk.Spinbox(controls, from_=1, to=1000, textvariable=quantity_var, width=8)
        quantity_input.pack(side=tk.LEFT, padx=(4, 10))

        def get_quantity() -> int:
            # Read a valid share quantity from the Python GUI input.
            try:
                return max(1, int(quantity_var.get()))
            except Exception:
                quantity_var.set(1)
                return 1

        def buy_clicked() -> None:
            self.buy(get_quantity())
            self.redrawPythonGUI()

        def sell_clicked() -> None:
            self.sell(get_quantity())
            self.redrawPythonGUI()

        def tick_clicked() -> None:
            self.updateOnce()
            self.redrawPythonGUI()

        def start_clicked() -> None:
            self.startPythonLoop()

        def pause_clicked() -> None:
            self.stopPythonLoop()

        def restart_clicked() -> None:
            # Restart the game using the Tkinter auto-run loop.
            self.restartGame(auto_start=False)
            self.startPythonLoop()
            self.redrawPythonGUI()

        def main_menu_clicked() -> None:
            # Return to the Python difficulty selection menu.
            self.returnToMainMenu()

        tk.Button(controls, text='Buy', width=10, command=buy_clicked).pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text='Sell', width=10, command=sell_clicked).pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text='Next Tick', width=10, command=tick_clicked).pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text='Start Auto', width=10, command=start_clicked).pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text='Pause Auto', width=10, command=pause_clicked).pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text='Restart', width=10, command=restart_clicked).pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text='Main Menu', width=10, command=main_menu_clicked).pack(side=tk.LEFT, padx=3)

        self.python_fig, self.python_ax = plt.subplots(figsize=(8, 4))
        self.python_canvas = figure_canvas_class(self.python_fig, master=main_frame)
        self.python_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.python_status_var = tk.StringVar()
        status_label = tk.Label(main_frame, textvariable=self.python_status_var, justify=tk.LEFT, anchor='w', font=('Courier New', 10))
        status_label.pack(fill=tk.X, pady=(8, 0))

        root.protocol('WM_DELETE_WINDOW', self.closePythonGUI)
        self.redrawPythonGUI()
        self.startPythonLoop() # Added for normal Python auto-run.

    def redrawPythonGUI(self) -> None:
        # Refresh the Tkinter chart and status panel for normal Python mode.
        if not hasattr(self, 'python_ax') or not hasattr(self, 'python_canvas'):
            return

        visible_times, visible_prices = self.getVisibleData()
        y_floor, y_ceil = self.compute_Y_Limits(visible_prices)

        self.python_ax.clear()
        self.python_ax.plot(visible_times, visible_prices, color='blue', linewidth=2)
        self.python_ax.set_title('Recent Stock Price')
        self.python_ax.set_xlabel('Time (s)')
        self.python_ax.set_ylabel('Price ($)')

        if not visible_times or visible_times[-1] < self.visible_window:
            self.python_ax.set_xlim(0, self.visible_window)
        else:
            self.python_ax.set_xlim(min(visible_times), max(visible_times))
        self.python_ax.set_ylim(y_floor, y_ceil)
        self.python_ax.grid(True)
        self.python_fig.tight_layout()
        self.python_canvas.draw_idle()

        if hasattr(self, 'python_status_var'):
            self.python_status_var.set(self.getStatusText())

    def pythonAutoTick(self) -> None:
        # Run one game tick from the Tkinter event loop.
        if not getattr(self, 'python_running', False):
            return

        self.runGameStep()
        self.redrawPythonGUI()

        if self.is_running:
            delay_ms = max(250, int(self.update_interval * 1000))
            self.python_after_id = self.python_root.after(delay_ms, self.pythonAutoTick)
        else:
            self.python_running = False

    def startPythonLoop(self) -> None:
        # Start the normal Python GUI auto-run loop.
        if getattr(self, 'python_running', False):
            return

        self.status_message = 'Auto-run started.'
        self.is_running = True
        self.python_running = True
        delay_ms = max(250, int(self.update_interval * 1000))
        self.python_after_id = self.python_root.after(delay_ms, self.pythonAutoTick)
        self.redrawPythonGUI()

    def stopPythonLoop(self) -> None:
        # Stop the normal Python GUI auto-run loop.
        self.is_running = False
        self.python_running = False
        if getattr(self, 'python_after_id', None) is not None:
            try:
                self.python_root.after_cancel(self.python_after_id)
            except Exception:
                pass
            self.python_after_id = None
        self.status_message = 'Auto-run paused.'
        self.redrawPythonGUI()

    def closePythonGUI(self) -> None:
        # Close the normal Python GUI and stop its timer.
        self.stopPythonLoop()
        if hasattr(self, 'python_fig'):
            plt.close(self.python_fig)
        self.python_root.destroy()


@dataclass
class Difficulty:
    name: str
    initial_cash: int
    fee_rate: float
    target_asset: int
    min_asset: int
    drift: float # The long-term trend of the stock price. For example: if drift>0, price will eventually rise.
    volatility: float
    min_trend_interval: int
    max_trend_interval: int
    trend_strength_range: float
    dynamic_enabled: bool = False

    def applyDifficulty(self, simulator):
        simulator.portfolio.cash = self.initial_cash
        simulator.portfolio.fee_rate = self.fee_rate
        simulator.target_asset = self.target_asset
        simulator.min_asset = self.min_asset
        self.applyMarketDifficulty(simulator)

    def applyMarketDifficulty(self, simulator):
        simulator.engine.volatility = self.volatility
        simulator.engine.trend_strength_range = self.trend_strength_range
        simulator.engine.drift = self.drift
        simulator.engine.min_trend_interval = self.min_trend_interval
        simulator.engine.max_trend_interval = self.max_trend_interval

    def dynamicDifficulty(self, simulator):
        if not self.dynamic_enabled:
            return
        else:
            self.drift -= 0.001
            self.volatility += 0.002
            self.trend_strength_range += 0.005

            self.applyMarketDifficulty(simulator)


# Default settings of difficulties.
EASY_DIFFICULTY = Difficulty(
    name='easy',
    initial_cash=12000,
    fee_rate=0.0,
    drift=0.001,
    volatility=0.008,
    min_trend_interval=5,
    max_trend_interval=10,
    trend_strength_range=0.04,
    target_asset=14000,
    min_asset=10000,
    dynamic_enabled=False,
)

NORMAL_DIFFICULTY = Difficulty(
    name='normal',
    initial_cash=10000,
    fee_rate=0.001,
    drift=0.0,
    volatility=0.015,
    min_trend_interval=3,
    max_trend_interval=8,
    trend_strength_range=0.045,
    target_asset=15000,
    min_asset=9000,
    dynamic_enabled=True,
)

HARD_DIFFICULTY = Difficulty(
    name='hard',
    initial_cash=7500,
    fee_rate=0.002,
    drift=-0.001,
    volatility=0.02,
    min_trend_interval=4,
    max_trend_interval=10,
    trend_strength_range=0.05,
    target_asset=15000,
    min_asset=7000,
    dynamic_enabled=True,
)


def create_simulator() -> RealtimeStockSimulator:
    # Create and return a simulator instance with default settings.
    simulator = RealtimeStockSimulator()

    if simulator.detectRuntimeEnvironment() == 'python':
        simulator.buildPythonGUI()
    else:
        simulator.buildDifficultySelector()

    return simulator

if __name__ == '__main__':
    # Start the simulator in the best interface for the current environment.
    game = create_simulator()
