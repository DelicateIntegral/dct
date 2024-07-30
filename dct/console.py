from rich.console import Console, Group
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn, DownloadColumn
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

console = Console()
prompt = Prompt(console)
int_prompt = IntPrompt(console)


def create_progress_bar(style: int = 0) -> Progress:
    if style == 1:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("Downloading: {task.fields[filename]}"),
            BarColumn(),
            DownloadColumn(),
        )
    elif style == 0:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}", justify="left"),
            BarColumn(bar_width=80),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("{task.percentage:>3.0f}%"),
        )
    return progress


def create_group(progress_bar: Progress, download_bar: Progress) -> Group:
    return Group(progress_bar, download_bar)


def create_panel_layout(renderable: Progress | Group, style: int = 0) -> Panel:
    layout = Layout(renderable)
    if style == 0:
        panel = Panel(layout, border_style="bold blue", width=120, height=12)
    elif style == 1:
        panel = Panel(layout, border_style="bold blue", width=120, height=3)
    return panel


def create_live(panel: Panel) -> Live:
    return Live(panel, vertical_overflow="visible")
