"""This script is designed to help with the installation of the FOLIO Fee/Fine system.
It is not designed to be run on the server.
"""
import time
from simple_term_menu import TerminalMenu
from src.utilities.microsoft_auth import Auth360Account

def main():
    """
    Main function to display the menu and handle user input.
    """
    main_menu_title = """  
    -------------------------------------------------
                Fee Fine Utilities
    -------------------------------------------------

    These scripts are designed to help with the
    installation of the FOLIO Fee/Fine system.
    They where created to be ran client side and are not
    designed to be ran on the server.
    Press Q or Esc to quit.
    """
    main_menu_items = ["Microsoft 365 Authenticate", "Quit"]
    main_menu_exit = False

    main_menu = TerminalMenu(
        menu_entries=main_menu_items,
        title=main_menu_title,
        cycle_cursor=True,
        clear_screen=True,
    )

    while not main_menu_exit:
        main_sel = main_menu.show()

        if main_sel == 0:
            print("Stratify Authentication Script >>>>>>>")
            Auth360Account.authenticate_account()
            print("<<<<<<< Process Complete >>>>>>>")
            time.sleep(5)
        elif main_sel == 1 or main_sel == None:
            main_menu_exit = True
            print("Quit Selected")


if __name__ == "__main__":
    main()