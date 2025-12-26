import io
import time
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color as KivyColor
from kivy.app import App

# Imports for all WCA puzzles
from pyTwistyScrambler import (
    scrambler222, scrambler333, scrambler444, scrambler555,
    scrambler666, scrambler777, pyraminxScrambler,
    megaminxScrambler, squareOneScrambler,
    skewbScrambler, clockScrambler
)

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Configuration for WCA Scramblers
PUZZLE_CONFIG = {
    "2x2x2": {"module": scrambler222, "func": "get_WCA_scramble", "args": {}},
    "3x3x3": {"module": scrambler333, "func": "get_WCA_scramble", "args": {}},
    # RESTORED n=40 for 4x4x4
    "4x4x4": {"module": scrambler444, "func": "get_WCA_scramble", "args": {"n": 40}},
    "5x5x5": {"module": scrambler555, "func": "get_WCA_scramble", "args": {"n": 60}},
    "6x6x6": {"module": scrambler666, "func": "get_WCA_scramble", "args": {"n": 80}},
    "7x7x7": {"module": scrambler777, "func": "get_WCA_scramble", "args": {"n": 100}},
    "Pyraminx": {"module": pyraminxScrambler, "func": "get_WCA_scramble", "args": {}},
    "Megaminx": {"module": megaminxScrambler, "func": "get_WCA_scramble", "args": {"n": 70}},
    "Square-1": {"module": squareOneScrambler, "func": "get_WCA_scramble", "args": {}},
    "Skewb": {"module": skewbScrambler, "func": "get_WCA_scramble", "args": {}},
    "Clock": {"module": clockScrambler, "func": "get_WCA_scramble", "args": {}},
}

# Configuration for Trainer Modes
TRAINER_CONFIG = {
    # 3x3x3 Trainer Modes (scrambler333)
    "3x3x3 3BLD": {"module": scrambler333, "func": "get_3BLD_scramble", "args": {}},
    "3x3x3 Edges": {"module": scrambler333, "func": "get_edges_scramble", "args": {}},
    "3x3x3 Corners": {"module": scrambler333, "func": "get_corners_scramble", "args": {}},
    "3x3x3 LL": {"module": scrambler333, "func": "get_LL_scramble", "args": {}},
    "3x3x3 F2L": {"module": scrambler333, "func": "get_F2L_scramble", "args": {}},
    "3x3x3 Cross (Easy)": {"module": scrambler333, "func": "get_easy_cross_scramble", "args": {"n": 4}},
    "3x3x3 Cross (Difficult)": {"module": scrambler333, "func": "get_easy_cross_scramble", "args": {"n": 8}},
    "3x3x3 LSLL": {"module": scrambler333, "func": "get_LSLL_scramble", "args": {}},
    "3x3x3 ZBLL": {"module": scrambler333, "func": "get_ZBLL_scramble", "args": {}},
    "3x3x3 ZZLL": {"module": scrambler333, "func": "get_ZZLL_scramble", "args": {}},
    "3x3x3 ZBLS": {"module": scrambler333, "func": "get_ZBLS_scramble", "args": {}},
    "3x3x3 LSE": {"module": scrambler333, "func": "get_LSE_scramble", "args": {}},
    "3x3x3 CMLL": {"module": scrambler333, "func": "get_CMLL_scramble", "args": {}},
    "3x3x3 CLL": {"module": scrambler333, "func": "get_CLL_scramble", "args": {}},
    "3x3x3 ELL": {"module": scrambler333, "func": "get_ELL_scramble", "args": {}},
    "3x3x3 EO Line": {"module": scrambler333, "func": "get_EOLine_scramble", "args": {}},

    # NxNxN Trainer Modes (Edges)
    "4x4x4 Edges": {"module": scrambler444, "func": "get_edges_scramble", "args": {"n": 8}},
    "5x5x5 Edges": {"module": scrambler555, "func": "get_edges_scramble", "args": {"n": 8}},
    "6x6x6 Edges": {"module": scrambler666, "func": "get_edges_scramble", "args": {"n": 8}},
    "7x7x7 Edges": {"module": scrambler777, "func": "get_edges_scramble", "args": {"n": 8}},

    # Square-1 Trainer Modes
    "Square-1 Face Turn Metric": {"module": squareOneScrambler, "func": "get_face_turn_metric_scramble",
                                  "args": {"n": 40}},
    "Square-1 Twist Metric": {"module": squareOneScrambler, "func": "get_twist_metric_scramble", "args": {"n": 20}},
}


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super(SplashScreen, self).__init__(**kwargs)
        self.main_sm = None

    def on_enter(self):
        Clock.schedule_once(self.check_first_run, 0.1)

    def check_first_run(self, dt):
        store = App.get_running_app().store

        if not store.exists('all_data'):
            # First Run
            self.ids.splash_status.text = "First Run: Generating Scrambles..."
            self.ids.splash_detail.text = "Please wait, this only happens once."
            Clock.schedule_once(self.run_first_time_setup, 0.1)
        else:
            self.go_to_timer()

    def run_first_time_setup(self, dt):
        timer_screen = self.main_sm.get_screen('timer')
        timer_screen._generate_initial_batch(None)

        self.ids.splash_status.text = "Setup Complete!"
        # HELPER METHOD TO FIX SYNTAX ERROR
        Clock.schedule_once(self.go_to_timer, 0.5)

    def go_to_timer(self, dt):
        self.main_sm.current = 'timer'


class TimerScreen(Screen):
    def __init__(self, **kwargs):
        super(TimerScreen, self).__init__(**kwargs)

        # State variables
        self.running = False
        self.start_time = 0
        self.timer_event = None
        self.holding = False
        self.ready_to_start = False
        self.hold_start_time = 0
        self.hold_event = None

        # Data & Puzzle State
        self.solve_data = {}
        self.current_puzzle = "3x3x3"
        self.current_scramble = ""
        self.scramble_queue = []

        # Load Data on Init
        Clock.schedule_once(self._load_data, 0)

        # Keyboard binding
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard.unbind(on_key_up=self._on_keyboard_up)
        self._keyboard = None

    def _load_data(self, dt):
        store = App.get_running_app().store

        # Load Solve Data
        try:
            loaded_data = store.get('all_data')['value']
            self.solve_data = loaded_data
            self.current_puzzle = store.get('current_puzzle')['value']
        except KeyError:
            # Initialize for both WCA and Trainer configs
            for puz in PUZZLE_CONFIG.keys():
                self.solve_data[puz] = {'times': [], 'scrambles': []}
            for puz in TRAINER_CONFIG.keys():
                self.solve_data[puz] = {'times': [], 'scrambles': []}

        if self.current_puzzle not in self.solve_data:
            self.current_puzzle = "3x3x3"

        # Load Scramble Queue
        try:
            queues = store.get('scramble_queues')['value']
            self.scramble_queue = queues.get(self.current_puzzle, [])
        except KeyError:
            self.scramble_queue = []

        # Initialize UI
        self._update_titles()

        if not self.scramble_queue:
            self.ids.scramble_label.text = "Generating Scrambles..."
            Clock.schedule_once(lambda dt: self._fill_scramble_queue(50), 0)
        else:
            self.generate_new_scramble()

        self.update_stats_label()
        self.update_recent_times()
        self.update_graph()
        self.set_led_color(0.5, 0.5, 0.5)

    def _generate_initial_batch(self, dt):
        print("First Run: Generating scramble queues for WCA and Trainer puzzles...")
        store = App.get_running_app().store
        all_queues = {}

        # Combine WCA and Trainer Configs
        all_configs = {**PUZZLE_CONFIG, **TRAINER_CONFIG}

        for puz_name, config in all_configs.items():
            module = config['module']
            func_name = config['func']
            args = config['args']
            func = getattr(module, func_name)

            all_queues[puz_name] = [func(**args) for _ in range(50)]

        store.put('all_data', value=self.solve_data)
        store.put('current_puzzle', value=self.current_puzzle)
        store.put('scramble_queues', value=all_queues)
        print("Setup Complete.")

    def _save_data(self):
        store = App.get_running_app().store
        store.put('all_data', value=self.solve_data)
        store.put('current_puzzle', value=self.current_puzzle)

    def _save_queue(self):
        store = App.get_running_app().store
        try:
            queues = store.get('scramble_queues')['value']
        except KeyError:
            queues = {}

        queues[self.current_puzzle] = self.scramble_queue
        store.put('scramble_queues', value=queues)

    def switch_puzzle(self, puzzle_name):
        if self.running:
            return

        # SAFETY CHECK: Initialize data if this puzzle key doesn't exist yet
        if puzzle_name not in self.solve_data:
            self.solve_data[puzzle_name] = {'times': [], 'scrambles': []}

        self.current_puzzle = puzzle_name
        self.current_scramble = ""

        store = App.get_running_app().store
        try:
            queues = store.get('scramble_queues')['value']
            self.scramble_queue = queues.get(self.current_puzzle, [])
        except KeyError:
            self.scramble_queue = []

        self._update_titles()

        if not self.scramble_queue:
            self.ids.scramble_label.text = "Generating Scrambles..."
            Clock.schedule_once(lambda dt: self._fill_scramble_queue(50), 0)
        else:
            self.generate_new_scramble()

        self.update_stats_label()
        self.update_recent_times()
        self.update_graph()
        self._save_data()
        self.manager.current = 'timer'

    def _update_titles(self):
        self.manager.get_screen('stats').ids.stats_title.text = f"Statistics ({self.current_puzzle})"

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.manager.current != 'timer':
            return
        if keycode[1] == 'spacebar':
            if self.running:
                self.stop_timer()
            elif not self.holding and not self.ready_to_start:
                self.holding = True
                self.ready_to_start = False
                self.hold_start_time = time.time()
                self.ids.status_label.text = "Holding..."
                self.set_led_color(1, 0, 0)
                self.hold_event = Clock.schedule_interval(self.check_hold, 0.01)
        return True

    def _on_keyboard_up(self, keyboard, keycode):
        if self.manager.current != 'timer':
            return
        if keycode[1] == 'spacebar':
            if self.ready_to_start:
                self.holding = False
                self.ready_to_start = False
                self.start_timer()
            elif self.holding:
                self.cancel_hold()

    def check_hold(self, dt):
        elapsed = time.time() - self.hold_start_time
        if (0.5 - elapsed) <= 0:
            Clock.unschedule(self.hold_event)
            self.hold_event = None
            self.ready_to_start = True
            self.ids.time_label.text = "READY"
            self.ids.status_label.text = "Release to Start"
            self.set_led_color(1, 1, 0)

    def cancel_hold(self):
        if self.hold_event:
            Clock.unschedule(self.hold_event)
            self.hold_event = None
        self.holding = False
        self.ready_to_start = False
        self.ids.time_label.text = "Ready"
        self.ids.status_label.text = "Hold Spacebar"
        self.set_led_color(0.5, 0.5, 0.5)

    def set_led_color(self, r, g, b):
        led_canvas = self.ids.led.canvas.before
        for child in led_canvas.children:
            if isinstance(child, KivyColor):
                child.rgba = (r, g, b, 1)
                return

    def _fill_scramble_queue(self, num=50):
        # Check both WCA and Trainer configs
        all_configs = {**PUZZLE_CONFIG, **TRAINER_CONFIG}

        if self.current_puzzle not in all_configs:
            print(f"Error: Puzzle {self.current_puzzle} not found in configs.")
            return

        config = all_configs[self.current_puzzle]
        module = config['module']
        func_name = config['func']
        args = config['args']

        func = getattr(module, func_name)
        new_scrambles = [func(**args) for _ in range(num)]

        self.scramble_queue.extend(new_scrambles)

        self._save_queue()

        if self.ids.scramble_label.text == "Generating Scrambles...":
            self.generate_new_scramble()

    def generate_new_scramble(self):
        if not self.scramble_queue:
            self._fill_scramble_queue(10)

        self.current_scramble = self.scramble_queue.pop()
        self.ids.scramble_label.text = self.current_scramble

        if len(self.scramble_queue) < 10:
            Clock.schedule_once(lambda dt: self._fill_scramble_queue(50), 0.1)

    def start_timer(self):
        self.running = True
        self.start_time = time.time()
        self.ids.status_label.text = "Running"
        self.set_led_color(0, 1, 0)
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.016)

    def stop_timer(self):
        self.running = False
        Clock.unschedule(self.timer_event)

        final_time = time.time() - self.start_time

        self.solve_data[self.current_puzzle]['times'].append(final_time)
        self.solve_data[self.current_puzzle]['scrambles'].append(self.current_scramble)

        times = self.solve_data[self.current_puzzle]['times']
        if len(times) > 50:
            self.solve_data[self.current_puzzle]['times'] = times[-50:]
            self.solve_data[self.current_puzzle]['scrambles'] = self.solve_data[self.current_puzzle]['scrambles'][-50:]

        formatted_time = self.format_time(final_time)
        self.ids.time_label.text = formatted_time

        self.ids.status_label.text = "Solve Finished"
        self.set_led_color(0, 1, 0)
        self.ids.delete_btn.disabled = False

        self.update_stats_label()
        self.update_recent_times()
        self.generate_new_scramble()
        Clock.schedule_once(lambda dt: self.update_graph(), 0.05)

        self._save_data()

    def delete_last_solve(self):
        data = self.solve_data[self.current_puzzle]
        if data['times']:
            data['times'].pop()
            data['scrambles'].pop()

            if data['times']:
                latest_time = data['times'][-1]
                self.ids.time_label.text = self.format_time(latest_time)
            else:
                self.ids.time_label.text = "Ready"

            self.update_stats_label()
            self.update_recent_times()
            Clock.schedule_once(lambda dt: self.update_graph(), 0.05)
            self.ids.delete_btn.disabled = True

            self._save_data()

    def reset_all_stats(self):
        # Reset WCA and Trainer configs
        for puz in PUZZLE_CONFIG.keys():
            self.solve_data[puz] = {'times': [], 'scrambles': []}
        for puz in TRAINER_CONFIG.keys():
            self.solve_data[puz] = {'times': [], 'scrambles': []}

        self.ids.time_label.text = "Ready"
        self.ids.status_label.text = "Hold Spacebar"
        self.ids.delete_btn.disabled = True
        self.set_led_color(0.5, 0.5, 0.5)
        self.generate_new_scramble()
        self.update_stats_label()
        self.update_recent_times()
        self.update_graph()
        self._save_data()
        self.manager.current = 'timer'

    def update_timer(self, dt):
        current_time = time.time() - self.start_time
        self.ids.time_label.text = self.format_time(current_time)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        centis = int((seconds * 100) % 100)
        return f"{mins}:{secs:02}.{centis:02}"

    def update_stats_label(self):
        times = self.solve_data[self.current_puzzle]['times']
        count = len(times)

        quick_text = f"Solves: {count}"
        full_text = f"Solves: {count}"

        if count == 0:
            self.ids.quick_stats_label.text = quick_text
            self.manager.get_screen('stats').ids.stats_label.text = full_text
            return

        avg = sum(times) / count
        best = min(times)

        quick_text += f"\nAvg: {self.format_time(avg)}\nBest: {self.format_time(best)}"
        full_text += f"\nAvg: {self.format_time(avg)}\nBest: {self.format_time(best)}"

        ao5_text = ""
        if count >= 5:
            last_five = times[-5:]
            last_five.sort()
            ao5 = sum(last_five[1:4]) / 3
            ao5_text = f"\nAo5: {self.format_time(ao5)}"
            quick_text += ao5_text
            full_text += ao5_text

        ao12_text = ""
        if count >= 12:
            last_twelve = times[-12:]
            last_twelve.sort()
            ao12 = sum(last_twelve[1:11]) / 10
            ao12_text = f"\nAo12: {self.format_time(ao12)}"
            quick_text += ao12_text
            full_text += ao12_text

        self.ids.quick_stats_label.text = quick_text
        self.manager.get_screen('stats').ids.stats_label.text = full_text

    def update_recent_times(self):
        times = self.solve_data[self.current_puzzle]['times']
        recent = times[-13:]
        recent.reverse()

        text = ""
        for t in recent:
            text += f"{self.format_time(t)}\n"
        self.ids.recent_times_label.text = text

    def update_graph(self):
        times = self.solve_data[self.current_puzzle]['times']
        plt.figure(figsize=(6, 4), dpi=100)
        plt.style.use('bmh')

        x_data = range(1, len(times) + 1)
        y_data = times

        plt.plot(x_data, y_data, marker='o', linestyle='-', color='cyan')
        plt.title(f"{self.current_puzzle} Solve History", color='white')
        plt.xlabel("Solve #", color='white')
        plt.ylabel("Time (s)", color='white')
        plt.tick_params(axis='x', colors='white')
        plt.tick_params(axis='y', colors='white')

        plt.gcf().set_facecolor('#111111')
        plt.gca().set_facecolor('#111111')
        plt.tight_layout()

        canvas = FigureCanvasAgg(plt.gcf())
        canvas.draw()
        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)

        img_texture = CoreImage(io.BytesIO(buf.read()), ext='png').texture
        buf.close()
        plt.close()

        self.manager.get_screen('stats').ids.graph_image.texture = img_texture


class StatsScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class PuzzleSelectorScreen(Screen):
    pass


class TrainerSelectorScreen(Screen):
    pass