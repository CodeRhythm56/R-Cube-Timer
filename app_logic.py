import io
import time
import threading
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color as KivyColor
from kivy.app import App
from kivy.animation import Animation

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
    "4x4x4 Edges": {"module": scrambler444, "func": "get_edges_scramble", "args": {"n": 8}},
    "5x5x5 Edges": {"module": scrambler555, "func": "get_edges_scramble", "args": {"n": 8}},
    "6x6x6 Edges": {"module": scrambler666, "func": "get_edges_scramble", "args": {"n": 8}},
    "7x7x7 Edges": {"module": scrambler777, "func": "get_edges_scramble", "args": {"n": 8}},
    "Square-1 Face Turn Metric": {"module": squareOneScrambler, "func": "get_face_turn_metric_scramble",
                                  "args": {"n": 40}},
    "Square-1 Twist Metric": {"module": squareOneScrambler, "func": "get_twist_metric_scramble", "args": {"n": 20}},
}


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super(SplashScreen, self).__init__(**kwargs)
        self.main_sm = None

    def on_enter(self):
        Clock.schedule_once(self.start_fade_out, 1.0)

    def start_fade_out(self, dt):
        anim = Animation(opacity=0, duration=0.5)
        anim.bind(on_complete=self.switch_to_timer)
        anim.start(self)

    def switch_to_timer(self, *args):
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

        # FIX: Flag to prevent multiple generation threads running at once
        self.is_generating = False

        # Data & Puzzle State
        self.solve_data = {}
        self.current_puzzle = "3x3x3"
        self.current_scramble = ""
        self.scramble_queue = []

        # Performance: Cache the LED color instruction
        self.led_color_instruction = None

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

    def show_loading(self):
        overlay = self.ids.loading_overlay
        if overlay.parent != self:
            self.add_widget(overlay)

        overlay.opacity = 1
        overlay.disabled = False

    def hide_loading(self):
        overlay = self.ids.loading_overlay
        # Animate out then remove
        anim = Animation(opacity=0, duration=0.2)

        def on_anim_finish(*args):
            if overlay.parent == self:
                self.remove_widget(overlay)

        anim.bind(on_complete=on_anim_finish)
        anim.start(overlay)

    def _load_data(self, dt):
        store = App.get_running_app().store

        # Initialize empty data structures if they don't exist
        if not store.exists('all_data'):
            for puz in PUZZLE_CONFIG.keys():
                self.solve_data[puz] = {'times': [], 'scrambles': []}
            for puz in TRAINER_CONFIG.keys():
                self.solve_data[puz] = {'times': [], 'scrambles': []}
        else:
            self.solve_data = store.get('all_data')['value']

            if store.exists('current_puzzle'):
                self.current_puzzle = store.get('current_puzzle')['value']
            else:
                self.current_puzzle = "3x3x3"

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

        # Cache LED Reference
        led_canvas = self.ids.led.canvas.before
        for child in led_canvas.children:
            if isinstance(child, KivyColor):
                self.led_color_instruction = child
                break

        self.update_stats_label()
        self.update_recent_times()
        self.update_graph()
        self.set_led_color(0.5, 0.5, 0.5)

        # Ensure Loading Overlay is NOT visible on startup
        self.hide_loading()

        # CHECK IF FIRST RUN (Data Generation Needed)
        if not store.exists('all_data'):
            self.show_loading()
            # Start thread for generation
            threading.Thread(target=self._run_generation_thread).start()
        else:
            # Normal load, just get a scramble if queue is empty
            if not self.scramble_queue:
                self.ids.scramble_label.text = "Generating Scrambles..."
                # Use threaded generation
                self._fill_scramble_queue(50)
            else:
                self.generate_new_scramble()

    def _run_generation_thread(self):
        """Generates scramble data in a background thread for First Run."""
        all_queues = {}
        all_configs = {**PUZZLE_CONFIG, **TRAINER_CONFIG}

        for puz_name, config in all_configs.items():
            module = config['module']
            func_name = config['func']
            args = config['args']
            func = getattr(module, func_name)
            all_queues[puz_name] = [func(**args) for _ in range(50)]

        # Schedule the UI update on the main thread
        Clock.schedule_once(lambda dt: self._finish_setup(all_queues), 0)

    def _finish_setup(self, all_queues):
        """Called after thread finishes."""
        store = App.get_running_app().store
        store.put('all_data', value=self.solve_data)
        store.put('current_puzzle', value=self.current_puzzle)
        store.put('scramble_queues', value=all_queues)

        # Load the queue for the current puzzle
        self.scramble_queue = all_queues.get(self.current_puzzle, [])
        self.generate_new_scramble()

        # Hide the loading screen
        self.hide_loading()
        self.is_generating = False

    def _fill_scramble_queue(self, num=50):
        """
        Generates scrambles for current puzzle in a background thread.
        Uses a flag to prevent duplicate threads.
        """
        # Safety check: If we are already generating, don't start another one
        if self.is_generating:
            return

        # Set flag and show UI immediately
        self.is_generating = True
        self.show_loading()

        # Start the generation in a separate thread
        threading.Thread(target=self._run_single_generation_thread, args=(num,)).start()

    def _run_single_generation_thread(self, num):
        """
        The actual heavy lifting. Runs in background.
        """
        all_configs = {**PUZZLE_CONFIG, **TRAINER_CONFIG}

        if self.current_puzzle not in all_configs:
            return

        config = all_configs[self.current_puzzle]
        module = config['module']
        func_name = config['func']
        args = config['args']

        func = getattr(module, func_name)
        new_scrambles = [func(**args) for _ in range(num)]

        # Return to main thread to update UI
        Clock.schedule_once(lambda dt: self._finish_single_generation(new_scrambles), 0)

    def _finish_single_generation(self, new_scrambles):
        """
        Called on Main Thread after generation is done.
        """
        self.scramble_queue.extend(new_scrambles)
        self._save_queue()

        self.is_generating = False
        self.hide_loading()

        if self.ids.scramble_label.text == "Generating Scrambles...":
            self.generate_new_scramble()

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
            # This will now show loading screen properly
            self._fill_scramble_queue(50)
        else:
            self.generate_new_scramble()

        self.update_stats_label()
        self.update_recent_times()
        if self.manager.current == 'stats':
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
        if self.led_color_instruction:
            self.led_color_instruction.rgba = (r, g, b, 1)

    def generate_new_scramble(self):
        if not self.scramble_queue:
            self._fill_scramble_queue(10)

        self.current_scramble = self.scramble_queue.pop()
        self.ids.scramble_label.text = self.current_scramble

        if len(self.scramble_queue) < 10:
            # This will now show loading screen properly
            self._fill_scramble_queue(50)

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

        if self.manager.current == 'stats':
            self.update_graph()

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

            if self.manager.current == 'stats':
                self.update_graph()

            self.ids.delete_btn.disabled = True
            self._save_data()

    def reset_all_stats(self):
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
    def on_enter(self, *args):
        timer_screen = self.manager.get_screen('timer')
        timer_screen.update_graph()


class SettingsScreen(Screen):
    pass


class PuzzleSelectorScreen(Screen):
    pass


class TrainerSelectorScreen(Screen):
    pass
