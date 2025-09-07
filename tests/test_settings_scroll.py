#!/usr/bin/env python
"""Test script to check settings screen scrolling"""

from textual.app import App
from src.tui.screens.settings import SettingsScreen

class TestSettingsApp(App):
    def on_mount(self):
        self.push_screen(SettingsScreen())

if __name__ == "__main__":
    app = TestSettingsApp()
    app.run()