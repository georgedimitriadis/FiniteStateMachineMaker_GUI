
import os
from os.path import dirname
import sys
from threading import Thread
from pathlib import Path
from functools import reduce
import jsonpickle
jsonpickle.set_preferred_backend('json')

sys.path.insert(0, dirname(dirname(dirname(os.path.realpath(__file__)))))
editor_path = Path(os.path.dirname(os.path.realpath(__file__)))
from state_node import State
from transition import Transition
import script_authoring_functions as safs
import dearpygui.dearpygui as dpg

dict_of_states = {}
python_file_of_state_machine = None
abort_transition_creation = False
input_variables_text = None
state_variables = []
state_variable_constructor = []


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
            if input_variables_text is None:
                input_variables_text = input_var
            else:
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

    def on_cancel(sender, app_data):
        print( app_data)

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

        safs.generate_python_script(python_file_of_state_machine, state_class_name, input_variables_text,
                                    state_variables_text, state_variable_constructor_text)
        dpg.delete_item('file_dialog')

    with dpg.file_dialog(default_filename='.py', callback=on_file_set,
                         cancel_callback=on_cancel, height=500, tag='file_dialog'):
        dpg.add_file_extension(".py", color=[255, 255, 255, 255])


def save_state_machine():
    global python_file_of_state_machine
    if python_file_of_state_machine is None:
        def on_file_set(sender, app_data, user_data):
            global python_file_of_state_machine
            python_file_of_state_machine = app_data['file_path_name']
            dpg.delete_item('file_dialog')

        with dpg.file_dialog(default_filename='.py', callback=on_file_set, height=500, tag='file dialog'):
            dpg.add_file_extension(".py", color=[255, 255, 255, 255])

    pickle_file_of_state_machine = python_file_of_state_machine.split('.')[0] + '.json'
    with open(pickle_file_of_state_machine, 'w') as f:
        dict_to_save = {'states': dict_of_states,
                        'state_variables': state_variables,
                        'input_variables_text': input_variables_text,
                        'state_variable_constructor': state_variable_constructor}
        f.write(jsonpickle.encode(dict_to_save, keys=True, indent=5, make_refs=False))


def load_state_machine():

    def on_file_set(sender, app_data, user_data):
        global python_file_of_state_machine
        global dict_of_states
        global state_variables
        global state_variable_constructor
        global input_variables_text
        global state_variable_constructor

        pickle_file_of_state_machine = app_data['file_path_name']

        python_file_of_state_machine = pickle_file_of_state_machine.split('.')[0] + '.py'
        with open(pickle_file_of_state_machine, 'r') as f:
            text = f.read()
            saved_dict = jsonpickle.decode(text, keys=True)

            dict_of_states = saved_dict['states']
            state_variables = saved_dict['state_variables']
            input_variables_text = saved_dict['input_variables_text']
            state_variable_constructor = saved_dict['state_variable_constructor']

        for s in dict_of_states:
            state = dict_of_states[s]
            state.draw_elipse_at(pmin=(state.pos_x - 100, state.pos_y - 50),
                                 pmax=(state.pos_x + 100, state.pos_y + 50))

            for end_state_name in state.transitions_from_here:
                end_state = dict_of_states[end_state_name]
                transition = state.transitions_from_here[end_state_name]
                if type(transition) is str:
                    dict_of_states[state.name].transitions_from_here[end_state_name] = \
                        dict_of_states[end_state_name].transitions_to_here[state.name]

                transition = state.transitions_from_here[end_state_name]
                transition.spawn(p1=transition.p1, p2=transition.p2, p3=transition.p3)

                end_state.transitions_to_here[state.name] = transition

        dpg.delete_item('file dialog')

    with dpg.file_dialog(default_filename='.py', callback=on_file_set, height=500, tag='file dialog'):
        dpg.add_file_extension(".json", color=[255, 255, 255, 255])


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
    state = None
    state_name = None
    is_initial = False
    pos = dpg.get_mouse_pos()
    self_transition = None
    p2 = None
    p3 = None

    def get_name_of_state(sender, app_data, user_data):
        nonlocal state_name
        state_name = app_data
        dpg.enable_item('self_transition_checkbox_id')

    def get_if_it_is_initial(sender, app_data, user_data):
        nonlocal is_initial
        is_initial = app_data

    def update_state_info():
        nonlocal state_name
        nonlocal is_initial
        nonlocal pos

        return state_name, is_initial, pos, python_file_of_state_machine, dict_of_states, drawlayer_states

    def update_self_transition_info():
        nonlocal self_transition
        nonlocal state
        nonlocal p2
        nonlocal p3

        return self_transition, state, p2, p3

    def create_state_and_self_transition(sender, app_data, user_data):
        nonlocal state
        nonlocal state_name
        nonlocal is_initial
        nonlocal pos
        nonlocal self_transition
        nonlocal p2
        nonlocal p3

        state = State(state_name, drawlayer_states, pos[0], pos[1], is_initial)
        dict_of_states[state_name] = state

        self_transition = Transition(state.name, drawlayer_transitions, item_handler_registry,
                                (pos[0], pos[1]))
        self_transition.is_a_self_transition = True
        p2 = (state.pos_x + 100, state.pos_y - 200)
        p3 = (state.pos_x + 70, state.pos_y)

    def put_state_on_python_script_and_define_self_transition(sender, app_data, user_data):
        safs.add_state_to_python_script(sender=None, app_data=None, user_data=update_state_info)
        self_transition_info = user_data
        transition, state, p2, p3 = self_transition_info()
        if transition is not None:
            transition_generation_gui(transition, state, state, p2, p3)

    # Ask the user the state name and if it is an initial state, then add the info to the python file (if it exists)
    with dpg.window(width=500, height=280, pos=[300, 300], tag="state_name_modal_id", modal=False):
        dpg.add_text('State name:')
        dpg.add_input_text(callback=get_name_of_state)
        dpg.add_text('______________________________________________')
        dpg.add_checkbox(label='Is it an Initial state\n(only one state can be set to initial)',
                         callback=get_if_it_is_initial)
        dpg.add_text('______________________________________________')
        dpg.add_checkbox(label='Add transition to self', callback=create_state_and_self_transition, enabled=False,
                         tag='self_transition_checkbox_id')
        dpg.add_text('______________________________________________')
        with dpg.group(horizontal=True, horizontal_spacing=20):
            dpg.add_button(label="Ok", callback=put_state_on_python_script_and_define_self_transition, user_data=update_self_transition_info,
                           width=60, height=30)
            dpg.add_button(label='Cancel', width=60, height=30, callback=lambda: dpg.delete_item('state_name_modal_id'))


def delete_state(state_to_delete):
    state_to_delete = state_to_delete

    def do_not_delete_state():
        dpg.delete_item("class_name_modal_id")

    def yes_delete_state():

        dpg.delete_item("class_name_modal_id")

        for k in list(dict_of_states):
            state = dict_of_states[k]
            if state_to_delete == state:

                # Delete the transitions that come into this state and the transitions that leave this state
                for target_state in list(state.transitions_from_here):
                    delete_transition(state, state.transitions_from_here[target_state], with_gui=False)
                for source_state in list(state.transitions_to_here):
                    delete_transition(source_state, dict_of_states[source_state].transitions_from_here[state.name],
                                      with_gui=False)
                state.delete_visuals()

                # Remove the state from the python file if there is one specified
                if python_file_of_state_machine is not None:
                    state_name = state.name
                    is_initial = state.is_initial
                    # First remove the state definition line
                    safs.remove_state_from_python_script(python_file_of_state_machine, state_name, is_initial)

                del dict_of_states[k]

    with dpg.window(width=200, height=130, pos=[300, 300], tag="class_name_modal_id", modal=True):
        dpg.add_text('Delete State?')
        with dpg.group(horizontal=True, horizontal_spacing=10):
            dpg.add_button(label="Yes", callback=yes_delete_state)
            dpg.add_button(label="No", callback=do_not_delete_state)


def create_new_transition(start_state: State):
    global mouse_double_clicked

    transition = Transition(start_state, drawlayer_transitions, item_handler_registry,
                            (start_state.pos_x, start_state.pos_y))

    mouse_position = dpg.get_mouse_pos()
    end_state = get_state_under_position(mouse_position)
    new_transition_thread = Thread(group=None, target=create_new_transition_thread,
                                   args=[transition, start_state, end_state])
    new_transition_thread.start()


def transition_generation_gui(transition, start_state, end_state, p2, p3=None):
    if p3 is None:
        p3 = (end_state.pos_x, end_state.pos_y)
    transition.spawn(p1=None, p2=p2, p3=p3)
    transition.to_state = end_state.name
    start_state.transitions_from_here[end_state.name] = transition
    end_state.transitions_to_here[start_state.name] = transition
    transition_name = None

    def get_transition_name(sender, app_data, user_data):
        nonlocal transition_name
        nonlocal transition
        transition_name = app_data
        transition.name = transition_name
        transition.check_and_draw()

    def update_transition_info():
        nonlocal transition_name

        return transition_name, start_state, end_state, python_file_of_state_machine, input_variables_text

    # Ask the user the transition info and add it to the python script (if there is one)
    with dpg.window(width=500, height=600, pos=[300, 200], tag="transition_name_modal_id", modal=True):
        dpg.add_text('Transition name:')
        dpg.add_input_text(callback=get_transition_name)
        dpg.add_text('______________________________________________')
        dpg.add_text("Complete the transition's callback body")
        dpg.add_text('The state variables are: {}'.
                     format(reduce(lambda x, y: x + ', ' + y, [i.split('=')[0] for i in state_variables])))
        dpg.add_input_text(multiline=True, width=400, height=100, tag='transition_callback_text',
                           default_value='    def on_transition(self{}):\n\n'.format(input_variables_text))
        dpg.add_text('______________________________________________')
        dpg.add_text("Complete the conditional that will trigger the condition\n"
                     "e.g.: if input_var_1 == some_value:")
        dpg.add_text('The state variables are: {}\nand the input variables are: {}\n'
                     .format(reduce(lambda x, y: x + ', ' + y, [i.split('=')[0] for i in state_variables]),
                             input_variables_text))
        dpg.add_input_text(multiline=True, width=400, height=100, tag='transition_conditional_text',
                           default_value='            elif :')
        dpg.add_text('______________________________________________')
        dpg.add_button(label="Ok", callback=safs.add_transition_to_python_script, user_data=update_transition_info,
                       width=60, height=30)


def create_new_transition_thread(transition, start_state, end_state):
    global abort_transition_creation
    global python_file_of_state_machine

    transition_name = None

    p2 = None
    # This deals with the drawing of the bezier from the left click on the start state to the touching of the end state
    while (end_state is None or end_state == start_state) and not abort_transition_creation:
        mouse_position = dpg.get_mouse_pos()
        end_state = get_state_under_position(mouse_position)
        transition.spawn(p1=None, p3=mouse_position, p2=p2)

    # This deals with the case where the user ends up touching the end state (and hasn't pressed Esc before)
    # so the transition should be created
    if not abort_transition_creation:
        transition_generation_gui(transition, start_state, end_state, p2)
    # This is if the user presses Esc before touching the end state
    else:
        transition.delete_visuals()
        del transition
    abort_transition_creation = False


def delete_transition(from_state, transition, with_gui=True):

    def yes_delete_transition():
        nonlocal transition
        nonlocal from_state
        try:
            dpg.delete_item("class_name_modal_id")
        except:
            pass

        print(transition.to_state)
        to_state_name = transition.to_state

        del from_state.transitions_from_here[to_state_name]
        del dict_of_states[to_state_name].transitions_to_here[from_state.name]
        transition.delete_visuals()
        to_state = dict_of_states[to_state_name]

        # Remove the transition from the python file if there is one specified
        if python_file_of_state_machine is not None:
            safs.remove_transition_from_python_script(python_file_of_state_machine, transition, from_state, to_state)

        del transition

    def no_do_not_delete_transition():
        dpg.delete_item("class_name_modal_id")

    if with_gui:
        with dpg.window(width=200, height=70, pos=[300, 300], tag="class_name_modal_id", modal=True):
            dpg.add_text('Delete Transition?')
            with dpg.group(horizontal=True, horizontal_spacing=10):
                dpg.add_button(label="Yes", callback=yes_delete_transition)
                dpg.add_button(label="No", callback=no_do_not_delete_transition)
    else:
        yes_delete_transition()


# DPG Main Window and Widgets in it
dpg.create_context()
dpg.create_viewport(title='State Space Maker', width=1450, height=1000, x_pos=200, y_pos=0)


with dpg.font_registry():
    default_font = dpg.add_font(os.path.join(editor_path, 'SF-Pro-Rounded-Medium.ttf'), 18)


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
with dpg.window(width=1400, height=920) as main_window:
    dpg.set_primary_window(main_window, True)

    dpg.bind_font(default_font)

    with dpg.menu_bar(label='Menu Bar'):
        with dpg.menu(label='State Machine'):
            dpg.add_menu_item(label='New State Machine', callback=new_state_machine)
            dpg.add_menu_item(label='Save State Machine', callback=save_state_machine)
            dpg.add_menu_item(label='Load State Machine', callback=load_state_machine)

    with dpg.drawlist(width=1400, height=920, label='canvas') as drawlist:
        dpg.draw_rectangle((0, 0), (1400, 920), color=(255, 255, 255, 255), thickness=3)
        with dpg.draw_layer() as drawlayer_transitions:
            pass
        with dpg.draw_layer() as drawlayer_states:
            pass

# Run DPG
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()