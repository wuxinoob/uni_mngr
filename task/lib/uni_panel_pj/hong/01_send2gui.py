import os
import sys
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.join(current_dir, '..')
sys.path.append(parent_dir)
from uni_panel_pj.process_manager import msg_handler
def process(current_data:str, msg_handler:msg_handler):
    msg_handler.linked_process_mngr.ui_dict["gost"].write_cli(current_data)
#    print(current_data)
#    input()
    return current_data