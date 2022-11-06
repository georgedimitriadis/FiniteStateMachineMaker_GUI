
import numpy as np
from functools import reduce
import dearpygui.dearpygui as dpg
from state_node import State


def generate_python_script(python_file_of_state_machine, state_class_name, input_variables_text,
                           state_variables_text, state_variable_constructor_text):
    with open(python_file_of_state_machine, 'w') as f:
        f.write('\n'
                'import numpy as np\n'
                'from statemachine import StateMachine, State\n\n\n'
                'class {st_name}(StateMachine):\n\n'
                '    # Start States\n'
                '    # End States\n\n'
                '    # Start Transitions\n'
                '    # End Transitions\n\n'
                '    def __init__(self{constr_vars}):\n'
                '        super().__init__(StateMachine)\n'
                '        # Start State Variables\n'
                '        {st_vars}'
                '# End State Variables\n\n'
                '    def step(self{inp_vars}):\n'
                '        if False:\n'
                '            pass\n\n'
                '        # Start conditionals\n'
                '        # End conditionals\n\n'
                '    # Start transition callbacks\n'
                '    # End transition callbacks\n'
                .format(st_name=state_class_name, inp_vars=input_variables_text,
                        st_vars=state_variables_text, constr_vars=state_variable_constructor_text))



def add_state_to_python_script(sender, app_data, user_data):

    update_state_info = user_data()
    state_name, is_initial, pos, python_file_of_state_machine, dict_of_states, drawlayer_states = update_state_info

    # Write the state in the python file if there is one specified
    if python_file_of_state_machine is not None:
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
    else:
        pass

    dpg.delete_item("state_name_modal_id")
    # Create the new state object
    if state_name not in dict_of_states.keys():
        dict_of_states[state_name] = State(state_name, drawlayer_states, pos[0], pos[1], is_initial)


def remove_state_from_python_script(python_file_of_state_machine, state_name, is_initial):

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


def add_transition_to_python_script(sender, app_data, user_data):

    update_transition_info = user_data()
    transition_name, start_state, end_state, python_file_of_state_machine, input_variables_text = update_transition_info
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
                             format(transition_conditional_text, str(transition_name)))
                break

        with open(python_file_of_state_machine, "w") as f:
            contents = "".join(lines)
            f.write(contents)
    except:
        pass

    dpg.delete_item("transition_name_modal_id")


def remove_transition_from_python_script(python_file_of_state_machine, transition, from_state, to_state):
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
            if 'def on_trans_' in line or \
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

        del new_lines[index - 1]
        del new_lines[index - 1]

    with open(python_file_of_state_machine, "w") as f:
        contents = "".join(new_lines)
        f.write(contents)
