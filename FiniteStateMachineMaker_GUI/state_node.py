
import dearpygui.dearpygui as dpg
from transition import Transition


class State:

    def __init__(self, _name, _drawlayer, _pos_x, _pos_y, _is_initial):
        self.name = _name
        self.drawlayer = _drawlayer
        self.pos_x = _pos_x
        self.pos_y = _pos_y
        self.selected = False
        self.transitions_from_here = {}  # {state coming from : transition}
        self.transitions_to_here = {}  # {state going to: transition}
        self.is_initial = _is_initial
        self.ellipse_id: dpg.mvDrawEllipse
        self.draw_elipse_at(pmin=(self.pos_x - 100, self.pos_y - 50),
                            pmax=(self.pos_x + 100, self.pos_y + 50))
        self.label_id: dpg.mvDrawText

    def redraw_at(self, new_pos):
        self.pos_x = new_pos[0]
        self.pos_y = new_pos[1]
        self.delete_visuals()
        self.draw_elipse_at(pmin=(self.pos_x - 100, self.pos_y - 50),
                            pmax=(self.pos_x + 100, self.pos_y + 50))

        for i in self.transitions_from_here:
            self.transitions_from_here[i].spawn(p1=(self.pos_x, self.pos_y), p2=self.transitions_from_here[i].p2, p3=None)
        for k in self.transitions_to_here:
            p3 = [self.pos_x, self.pos_y]
            p2 = self.transitions_to_here[k].p2
            if self.transitions_to_here[k].is_a_self_transition:
                p3[0] += 70
            self.transitions_to_here[k].spawn(p1=None, p2=p2, p3=tuple(p3))

    def draw_elipse_at(self, pmin, pmax):
        self.ellipse_id = dpg.draw_ellipse(pmin=pmin, pmax=pmax,
                                           label=self.name,
                                           parent=self.drawlayer,
                                           fill=(150, 150, 150, 255),
                                           thickness=4)
        self.label_id = dpg.draw_text(pos=((pmin[0] + pmax[0])/2 - 6*len(self.name), (pmin[1] + pmax[1])/2 - 20),
                                      text=self.name, size=30, parent=self.drawlayer)

    def delete_visuals(self):
        dpg.delete_item(self.ellipse_id)
        dpg.delete_item(self.label_id)