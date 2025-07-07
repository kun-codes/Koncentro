from qfluentwidgets import FluentWindow

from constants import NavPanelButtonPosition


def setNavButtonEnabled(
    main_window: FluentWindow, interface_position: NavPanelButtonPosition, is_enabled: bool
) -> None:
    layout, position_in_layout = interface_position.value

    # Now you can use these variables to access the specific button
    if layout == 0:
        panel_layout = main_window.navigationInterface.panel.topLayout
    elif layout == 1:
        panel_layout = main_window.navigationInterface.panel.scrollLayout
    elif layout == 2:
        panel_layout = main_window.navigationInterface.panel.bottomLayout

    # Get the widget at the specified position
    if panel_layout.count() > position_in_layout:
        item = panel_layout.itemAt(position_in_layout)
        if item and item.widget():
            item.widget().setEnabled(is_enabled)
