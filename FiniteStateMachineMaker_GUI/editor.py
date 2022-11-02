
import numpy as np
import os
from os.path import dirname
import sys
from threading import Thread
from pathlib import Path
from functools import reduce
sys.path.insert(0, dirname(dirname(dirname(os.path.realpath(__file__)))))
heron_path = Path(os.path.dirname(os.path.realpath(__file__)))
from state_node import State
from transition import Transition
import dearpygui.dearpygui as dpg

dict_of_states = {}
python_file_of_state_machine: str
abort_transition_creation = False
input_variables_text = ''
state_variables = []
state_variable_constructor = []

# Variable generation functions


# File Menu Callbacks
def new_state_machine():
    global input_variables_text
    global state_variables
    global state_variable_constructor

    state_class_name = None
    number_of_input_var_widgets = 0
    number_of_state_var_widgets = 0

    def get_name_of_class(sender, app_data, user_data):
        nonlocal state_class_name
        state_class_name = app_data

    def add_input_variable_widget(sender, app_data, user_data):
        nonlocal number_of_input_var_widgets
        number_of_input_var_widgets += 1
        dpg.add_input_text(tag='input_widget_{}'.format(number_of_input_var_widgets),
                           label='Input Widget {}'.format(number_of_input_var_widgets),
                           parent='modal_input_widget_id', before='input_line')

    def add_state_variable_widget(sender, app_data, user_data):
        nonlocal number_of_state_var_widgets
        number_of_state_var_widgets += 1
        with dpg.group(horizontal=True, tag='state_widget_group_{}'.format(number_of_state_var_widgets),
                       parent='modal_input_widget_id', before='state_line'):
            dpg.add_checkbox(label='Constructor Var?',
                             tag='constructor_var_widget_{}'.format(number_of_state_var_widgets))
            dpg.add_input_text(tag='state_widget_{}'.format(number_of_state_var_widgets), width=200,
                               label='State Widget {}'.format(number_of_state_var_widgets))

    def add_to_input_and_state_variables_and_close(sender, app_data, user_data):
        global input_variables_text
        global state_variables
        global state_variable_constructor

        nonlocal number_of_input_var_widgets
        nonlocal number_of_state_var_widgets

        for i in range(number_of_input_var_widgets + 1):
            input_var = dpg.get_value('input_widget_{}'.format(i))
            input_variables_text = input_variables_text + ', {}'.format(input_var)
        for i in range(number_of_state_var_widgets + 1):
            state_variable_constructor.append(dpg.get_value('constructor_var_widget_{}'.format(i)))
            state_variables.append(dpg.get_value('state_widget_{}'.format(i)))

        dpg.delete_item('modal_input_widget_id')

    with dpg.window(width=500, height=500, pos=[300, 300], tag="modal_input_widget_id", modal=True):
        dpg.add_text('What is the Class of the Finite State Machine going to be called?')
        dpg.add_input_text(callback=get_name_of_class)
        dpg.add_text('__________________________________________')
        dpg.add_text('Input Variables that will drive the FSM state changes:')
        dpg.add_button(label='Add Input Variable', callback=add_input_variable_widget)
        dpg.add_input_text(tag='input_widget_0', label='Input Widget 0')
        dpg.add_text('__________________________________________', tag='input_line')
        dpg.add_text('State Variables that will define each State:')
        dpg.add_button(label='Add State Variable', callback=add_state_variable_widget)
        with dpg.group(horizontal=True, tag='state_widget_group_0'):
            dpg.add_checkbox(label='Constructor Var?', tag='constructor_var_widget_0')
            dpg.add_input_text(tag='state_widget_0', label='State Widget 0', width=200)
        dpg.add_text('__________________________________________', tag='state_line')
        with dpg.group(horizontal=True, horizontal_spacing=30):
            dpg.add_button(label="OK", callback=add_to_input_and_state_variables_and_close, width=60, height=30)
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item('modal_input_widget_id'),
                           width=60, height=30)

    def on_file_set(sender, app_data, user_data):
        global python_file_of_state_machine
        global state_variables
        global state_variable_constructor
        nonlocal state_class_name
        python_file_of_state_machine = app_data['file_path_name']

        # Create the state variables that go in the __init__
        state_variable_constructor_text = ''
        state_variables_text = ''
        for i, sv in enumerate(state_variables):
            if state_variable_constructor[i]:
                state_variables_text = state_variables_text + \
                                       'self.{} = {}\n        '.format(sv, sv)
                state_variable_constructor_text = state_variable_constructor_text + ', {}'.format(sv)
            else:
                if '=' in sv:
                    state_variables_text = state_variables_text + 'self.{}\n        '.format(sv)
                else:
                    state_variables_text = state_variables_text + 'self.{} = None\n        '.format(sv)

        with open(python_file_of_state_machine, 'w') as f:
            f.write('\n'
                    'import numpy as np\n'
                    'from statemachine import StateMachine, State\n\n\n'
                    'class {st_name}(StateMachine):\n\n'
                    '    # Start States\n'
                    '    # End States\n\n'
                    '    # Start Transitions\n'
                    '    # End Transitions\n'
                    '    def __init__(self{constr_vars}):\n'
                    '        super().__init__(StateMachine)\n'
                    '        # Start State Variables\n'
                    '        {st_vars}'
                    '# End State Variables\n\n\n'
                    '    def step(self{inp_vars}):\n'
                    '        if False:\n'
                    '            pass\n\n'
                    '        # Start conditionals\n'
                    '        # End conditionals\n\n'
                    '    # Start transition callbacks\n'
                    '    # End transition callbacks\n'
                    .format(st_name=state_class_name, inp_vars=input_variables_text,
                            st_vars=state_variables_text, constr_vars=state_variable_constructor_text))
        dpg.delete_item('file dialog')

    with dpg.file_dialog(default_filename='.py', callback=on_file_set, height=500, tag='file dialog'):
        dpg.add_file_extension(".py", color=[255, 255, 255, 255])


def save_state_machine():
    pass


def load_state_machine():
    pass


# Mouse controls Callbacks
def get_state_under_position(position):
    global dict_of_states
    for k in dict_of_states:
        state = dict_of_states[k]
        if position[0] - 100 < state.pos_x < position[0] + 100 \
           and position[1] - 50 < state.pos_y < position[1] + 50:
            return state
    return None


def get_transitions_center_point_under_position(position):
    global dict_of_states
    for k in dict_of_states:
        state = dict_of_states[k]
        dict_of_transitions = state.transitions_from_here
        for i in dict_of_transitions:
            transition = dict_of_transitions[i]
            center = dpg.get_item_configuration(transition.circle)['center']
            if position[0]-30 < center[0] < position[0] + 30 and position[1]-30 < center[1] < position[1] + 30:
                return state, transition
    return None, None


def on_mouse_click(sender, app_data, user_data):
    if app_data == 1:
        on_right_mouse_click()

    if app_data == 0:
        on_left_mouse_click()


def on_mouse_release(sender, app_data, user_data):
    if app_data == 0:
        on_left_mouse_release()


def on_left_mouse_click():
    global dict_of_states
    position = dpg.get_mouse_pos(local=True)
    state = get_state_under_position(position)
    if state:
        state.selected = True


def on_left_mouse_release():
    global dict_of_states
    position = dpg.get_mouse_pos(local=True)
    state = get_state_under_position(position)
    if state:
        state.selected = False


def on_right_mouse_click():
    global dict_of_states
    position = dpg.get_mouse_pos(local=True)
    state = get_state_under_position(position)
    if state:
        create_new_transition(state)
    else:
        create_new_state()


def on_mouse_double_click(sender, app_data, user_data):
    global dict_of_states
    position = dpg.get_mouse_pos()
    state = get_state_under_position(position)
    if state:
        delete_state(state)
    state, transition = get_transitions_center_point_under_position(position)
    if state and transition:
        delete_transition(state, transition)


def on_drag(sender, app_data, user_data):
    global dict_of_states
    position = dpg.get_mouse_pos()
    state = get_state_under_position(position)
    if state and state.selected:
        state.redraw_at(position)
    state, transition = get_transitions_center_point_under_position(position)
    if state and transition:
        transition.move_center_point(position)


def on_key_pressed(sender, app_data, user_data):
    global abort_transition_creation
    if app_data == 27:
        abort_transition_creation = True


# Creation and deletion functions
def create_new_state():
    global python_file_of_state_machine

    # Get the state's name and if it is an initial state:
    state_name = None
    is_initial = False
    pos = dpg.get_mouse_pos()

    def get_name_of_state(sender, app_data, user_data):
        nonlocal state_name
        state_name = app_data

    def get_if_it_is_initial(sender, app_data, user_data):
        nonlocal is_initial
        is_initial = app_data

    def add_state_to_python_script(sender, app_data, user_data):
        nonlocal state_name
        nonlocal is_initial
        nonlocal pos
        #state_name = user_data[0]
        #is_initial = user_data[1]
        #pos = user_data[2]

        # Write the state in the python file if there is one specified
        try:
            with open(python_file_of_state_machine, 'r') as f:
                lines = f.readlines()

            # Add the state definition line
            for line in lines:

                if line.find('    # End States') != -1:
                    lines.insert(lines.index(line),
                                 '    state_{} = State("{}", initial={})\n'.format(str(state_name), state_name, is_initial))
                    break

            # Add the state conditional in the step function
            for line in lines:

                if line.find('        # End conditionals') != -1:
                    lines.insert((lines.index(line)),
                                 '        elif self.current_state == self.{}:\n'
                                 '            if False:  # {}\n'
                                 '                pass  # {}\n'
                                 '        # End of {} conditional\n'.format(str(state_name), str(state_name),
                                                                            str(state_name), str(state_name)))
                    break

            with open(python_file_of_state_machine, "w") as f:
                contents = "".join(lines)
                f.write(contents)
        except:
            pass

        dpg.delete_item("state_name_modal_id")
        # Create the new state object
        dict_of_states[state_name] = State(state_name, drawlayer_states, pos[0], pos[1], is_initial)

    # Ask the user the state name and if it is an initial state, then add the info to the python file (if it exists)
    with dpg.window(width=500, height=230, pos=[300, 300], tag="state_name_modal_id", modal=True) as popup_window:
        dpg.add_text('State name:')
        dpg.add_input_text(callback=get_name_of_state)
        dpg.add_text('______________________________________________')
        dpg.add_checkbox(label='Is it an Initial state\n(only one state can be set to initial)',
                         callback=get_if_it_is_initial)
        dpg.add_text('______________________________________________')
        with dpg.group(horizontal=True, horizontal_spacing=20):
            dpg.add_button(label="Ok", callback=add_state_to_python_script, width=60, height=30)
            dpg.add_button(label='Cancel', width=60, height=30, callback=lambda: dpg.delete_item('state_name_modal_id'))


def delete_state(state_to_delete):
    state_to_delete = state_to_delete

    def yes_delete():
        nonlocal state_to_delete
        dpg.delete_item("class_name_modal_id")

        for k in list(dict_of_states):
            state = dict_of_states[k]
            if state_to_delete == state:

                # Delete the transitions that come into this state and the transitions that leave this state
                for target_state in list(state.transitions_from_here):
                    delete_transition(state, state.transitions_from_here[target_state], with_gui=False)
                for source_state in list(state.transitions_to_here):
                    delete_transition(source_state, source_state.transitions_from_here[state], with_gui=False)
                state.delete_visuals()

                # Remove the state from the python file if there is one specified
                try:
                    state_name = state.name
                    is_initial = state.is_initial
                    # First remove the state definition line
                    with open(python_file_of_state_machine, 'r') as f:
                        lines = f.readlines()

                        line_to_remove = '    state_{} = State("{}", initial={})\n'.format(str(state_name), state_name,
                                                                                           is_initial)
                        lines.remove(line_to_remove)

                        line_to_remove = '        elif self.current_state == self.{}:\n'.format(str(state_name))
                        index_of_line_to_remove = lines.index(line_to_remove)
                        lines.remove(line_to_remove)
                        while '        # End of {} conditional\n'.format(str(state_name)) not in  \
                            lines[index_of_line_to_remove]:
                            del lines[index_of_line_to_remove]
                        del lines[index_of_line_to_remove]

                    with open(python_file_of_state_machine, "w") as f:
                        contents = "".join(lines)
                        f.write(contents)
                except:
                    pass

                del dict_of_states[k]

    def no_do_not_delete():
        dpg.delete_item("class_name_modal_id")

    with dpg.window(width=200, height=130, pos=[300, 300], tag="class_name_modal_id", modal=True):
        dpg.add_text('Delete State?')
        with dpg.group(horizontal=True, horizontal_spacing=10):
            dpg.add_button(label="Yes", callback=yes_delete)
            dpg.add_button(label="No", callback=no_do_not_delete)


def create_new_transition(start_state: State):
    global mouse_double_clicked

    transition = Transition(start_state, drawlayer_transitions, item_handler_registry,
                            (start_state.pos_x, start_state.pos_y))

    mouse_position = dpg.get_mouse_pos()
    end_state = get_state_under_position(mouse_position)
    new_transition_thread = Thread(group=None, target=create_new_transition_thread,
                                   args=[transition, start_state, end_state])
    new_transition_thread.start()


def create_new_transition_thread(transition, start_state, end_state):
    global abort_transition_creation
    global python_file_of_state_machine

    transition_name = None

    def get_transition_name(sender, app_data, user_data):
        nonlocal transition_name
        nonlocal transition
        transition_name = app_data
        transition.name = transition_name
        transition._draw()

    def add_transition_to_python_script():
        nonlocal transition_name
        nonlocal start_state
        nonlocal end_state

        transition_callback_text = dpg.get_value('transition_callback_text')
        transition_conditional_text = dpg.get_value('transition_conditional_text')

        # Write the transition in the python file if there is one specified
        try:
            with open(python_file_of_state_machine, 'r') as f:
                lines = f.readlines()

            # Add the transition definition
            for line in lines:
                if line.find('    # End Transitions') != -1:
                    lines.insert(lines.index(line),
                                 '    trans_{} = state_{}.to(state_{})\n'.format(str(transition_name),
                                                                                 start_state.name,
                                                                                 end_state.name))
                    break

            # Add the transition callback
            for line in lines:
                if line.find('    # End transition callbacks') != -1:
                    function_content = reduce(lambda x, y: x+'\n'+y, transition_callback_text.split('\n')[1:])
                    if function_content == '\n':
                        function_content = '        pass\n'
                    lines.insert(lines.index(line), '    def on_trans_{}(self{}):\n'
                                                    '{}\n'.
                                                    format(str(transition_name), input_variables_text, function_content,
                                                           str(transition_name)))
                    break

            # Add the transition conditional
            for line in lines:
                if line.find('        # End of {} conditional\n'.format(str(start_state.name))) != -1:
                    lines.insert(lines.index(line), '{}\n                self.trans_{}()\n'.
                                 format(transition_conditional_text, str(transition.name)))
                    break

            with open(python_file_of_state_machine, "w") as f:
                contents = "".join(lines)
                f.write(contents)
        except:
            pass

        dpg.delete_item("transition_name_modal_id")

    p2 = None
    # This deals with the drawing of the bezier from the left click on the start state to the touching of the end state
    while (end_state is None or end_state == start_state) and not abort_transition_creation:
        mouse_position = dpg.get_mouse_pos()
        end_state = get_state_under_position(mouse_position)
        transition.spawn(p1=None, p3=mouse_position, p2=p2)

    # This deals with the case where the user ends up touching the end state (and hasn't pressed Esc before)
    # so the transition should be created
    if not abort_transition_creation:
        transition.spawn(p1=None, p3=(end_state.pos_x, end_state.pos_y), p2=p2)
        transition.to_state = end_state
        start_state.transitions_from_here[end_state] = transition
        end_state.transitions_to_here[start_state] = transition

        # Ask the user the transition info and add it to the python script (if there is one)
        with dpg.window(width=500, height=600, pos=[300, 200], tag="transition_name_modal_id", modal=True):
            dpg.add_text('Transition name:')
            dpg.add_input_text(callback=get_transition_name)
            dpg.add_text('______________________________________________')
            dpg.add_text("Complete the transition's callback body")
            dpg.add_text('The state variables are: {}'.
                         format(reduce(lambda x, y: x+', '+y, [i.split('=')[0] for i in state_variables])))
            dpg.add_input_text(multiline=True, width=400, height=100, tag='transition_callback_text',
                               default_value='    def on_transition(self{}):\n\n'.format(input_variables_text))
            dpg.add_text('______________________________________________')
            dpg.add_text("Complete the conditional that will trigger the condition\n"
                         "e.g.: if input_var_1 == some_value:")
            dpg.add_text('The state variables are: {}\nand the input variables are: {}\n'
                         .format(reduce(lambda x, y: x+', '+y, [i.split('=')[0] for i in state_variables]),
                                 input_variables_text[1:]))
            dpg.add_input_text(multiline=True, width=400, height=100, tag='transition_conditional_text',
                               default_value='            elif :')
            dpg.add_text('______________________________________________')
            dpg.add_buton(label="Ok", callback=add_transition_to_python_script, width=60, height=30)
    # This is if the user presses Esc before touching the end state
    else:
        transition.delete_visuals()
        del transition
    abort_transition_creation = False


def delete_transition(from_state, transition, with_gui=True):

    def yes_delete():
        nonlocal transition
        nonlocal from_state
        try:
            dpg.delete_item("class_name_modal_id")
        except:
            pass

        to_state = transition.to_state
        del from_state.transitions_from_here[to_state]
        del to_state.transitions_to_here[from_state]
        transition.delete_visuals()

        # Remove the transition from the python file if there is one specified
        try:
            with open(python_file_of_state_machine, 'r') as f:
                lines = f.readlines()

                # Remove the transition's definition
                line_to_remove = '    trans_{} = state_{}.to(state_{})\n'.format(str(transition.name),
                                                                                 from_state.name,
                                                                                 to_state.name)
                lines.remove(line_to_remove)

                # Remove the transition's callback
                line_indices_to_keep = []
                start_line_removal = False
                for i, line in enumerate(lines):
                    if 'def on_trans_' in line or\
                            '    # End transition callbacks' in line:
                        start_line_removal = False
                    if 'def on_trans_{}'.format(transition.name) in line:
                        start_line_removal = True
                    if not start_line_removal:
                        line_indices_to_keep.append(i)

                new_lines = list(np.array(lines)[line_indices_to_keep])

                # Remove the transition's conditional
                index = 0
                for i, line in enumerate(new_lines):
                    if 'self.trans_{}()\n'.format(transition.name) in line:
                        index = i
                        break

                del new_lines[index-1]
                del new_lines[index-1]

            with open(python_file_of_state_machine, "w") as f:
                contents = "".join(new_lines)
                f.write(contents)
        except:
            pass

        del transition

    def no_do_not_delete():
        dpg.delete_item("class_name_modal_id")

    if with_gui:
        with dpg.window(width=200, height=70, pos=[300, 300], tag="class_name_modal_id", modal=True):
            dpg.add_text('Delete Transition?')
            with dpg.group(horizontal=True, horizontal_spacing=10):
                dpg.add_button(label="Yes", callback=yes_delete)
                dpg.add_button(label="No", callback=no_do_not_delete)
    else:
        yes_delete()


# DPG Main Window and Widgets in it
dpg.create_context()
dpg.create_viewport(title='State Space Maker', width=1200, height=1000, x_pos=200, y_pos=0)


with dpg.font_registry():
    default_font = dpg.add_font(os.path.join(heron_path, 'SF-Pro-Rounded-Medium.ttf'), 18)


# Button and mouse callback registers
with dpg.handler_registry():
    dpg.add_mouse_drag_handler(callback=on_drag)
    dpg.add_mouse_click_handler(callback=on_mouse_click)
    dpg.add_mouse_release_handler(callback=on_mouse_release)
    dpg.add_mouse_double_click_handler(callback=on_mouse_double_click)
    key_press_handler = dpg.add_key_press_handler(key=-1, callback=on_key_pressed)

with dpg.item_handler_registry(tag="widget handler") as item_handler_registry:
    dpg.add_item_clicked_handler()

# Main window
with dpg.window(width=1150, height=920) as main_window:
    dpg.set_primary_window(main_window, True)

    dpg.bind_font(default_font)

    with dpg.menu_bar(label='Menu Bar'):
        with dpg.menu(label='File'):
            dpg.add_menu_item(label='New State Machine', callback=new_state_machine)
            dpg.add_menu_item(label='Save State Machine', callback=save_state_machine)
            dpg.add_menu_item(label='Load State Machine', callback=load_state_machine)

    with dpg.drawlist(width=1150, height=920, label='canvas') as drawlist:
        dpg.draw_rectangle((0, 0), (1150, 920), color=(255, 255, 255, 255), thickness=3)
        with dpg.draw_layer() as drawlayer_transitions:
            pass
        with dpg.draw_layer() as drawlayer_states:
            pass

# Run DPG
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()