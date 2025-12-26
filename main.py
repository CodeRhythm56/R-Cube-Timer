from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore

from app_logic import (
    TimerScreen, StatsScreen, SettingsScreen,
    PuzzleSelectorScreen, SplashScreen, TrainerSelectorScreen
)

Builder.load_file('styles.kv')


class RubiksTimerApp(App):
    def build(self):
        self.store = JsonStore('cube_timer_data.json')

        sm = ScreenManager()

        # Add Screens
        sm.add_widget(TimerScreen(name='timer'))
        sm.add_widget(StatsScreen(name='stats'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(PuzzleSelectorScreen(name='puzzle_selector'))
        sm.add_widget(TrainerSelectorScreen(name='trainer_selector'))

        # Initialize and Show Splash Screen First
        splash = SplashScreen(name='splash')
        splash.main_sm = sm
        sm.add_widget(splash)

        return sm


if __name__ == '__main__':
    RubiksTimerApp().run()