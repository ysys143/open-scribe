"""Simple Transcribe Screen for Testing"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Static, Label
from textual.widget import Widget

class SimpleTranscribeScreen(Widget):
    """Simplified transcribe screen focusing on URL input"""
    
    def compose(self) -> ComposeResult:
        """Build the UI"""
        with Vertical():
            yield Static("YouTube Transcriber", classes="screen-title")
            yield Static("─" * 50)
            
            # Simple URL input
            yield Label("Enter YouTube URL:")
            yield Input(
                placeholder="Paste or type URL here...",
                id="url_input",
            )
            
            # Buttons
            with Horizontal():
                yield Button("Start", id="start_btn", variant="primary")
                yield Button("Clear", id="clear_btn")
                yield Button("Back", id="back_btn")
            
            # Output
            yield Static("─" * 50)
            yield Static("Output will appear here", id="output")
    
    def on_mount(self) -> None:
        """When screen loads"""
        # Get the input widget and focus it
        url_input = self.query_one("#url_input", Input)
        url_input.focus()
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "start_btn":
            url_input = self.query_one("#url_input", Input)
            url = url_input.value
            output = self.query_one("#output", Static)
            
            if url:
                output.update(f"Processing: {url}")
                self.app.notify(f"Starting transcription for: {url}")
            else:
                output.update("Please enter a URL first")
                self.app.notify("No URL provided", severity="warning")
                
        elif event.button.id == "clear_btn":
            url_input = self.query_one("#url_input", Input)
            url_input.value = ""
            url_input.focus()
            
        elif event.button.id == "back_btn":
            if hasattr(self.app, 'show_main_menu'):
                self.app.show_main_menu()