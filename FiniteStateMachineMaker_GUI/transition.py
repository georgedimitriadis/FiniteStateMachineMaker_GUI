
import numpy as np
import dearpygui.dearpygui as dpg


class Transition:

    def __init__(self, _from_state, _drawlayer, _item_handler_registry, _p1):
        self.from_state = _from_state
        self.to_state = None
        self.name = None
        self.drawlayer = _drawlayer
        self.item_handler_registry = _item_handler_registry
        self.p1 = _p1
        self.p2 = None
        self.p3 = None
        self.selected = False
        self.bezier = None
        self.arrow = None
        self.circle = None
        self.name_text = None

    def spawn(self, p1, p2, p3):
        if p1 is None:
            p1 = np.array(self.p1)
        else:
            p1 = np.array(p1)
        if p3 is None:
            p3 = np.array(self.p3)
        else:
            p3 = np.array(p3)
        if p2 is None:
            self.p2 = tuple((p1 + (p3 - p1)/2))
        else:
            self.p2 = tuple(p2)
        self.p1 = tuple(p1)
        self.p3 = tuple(p3)
        self._draw()

    def move_center_point(self, pos):
        self.p2 = pos
        self._draw()

    def delete_visuals(self):
        dpg.delete_item(self.bezier)
        dpg.delete_item(self.arrow)
        dpg.delete_item(self.circle)
        if self.name_text:
            dpg.delete_item(self.name_text)
        self.bezier = None
        self.arrow = None
        self.circle = None
        self.name_text = None

    def _draw(self):
        if self.bezier:
            dpg.delete_item(self.bezier)
        if self.arrow:
            dpg.delete_item(self.arrow)
        if self.circle:
            dpg.delete_item(self.circle)
        if self.name_text:
            dpg.delete_item(self.name_text)
            self.name_text = None
        self.bezier = dpg.draw_bezier_quadratic(self.p1, self.p2, self.p3, parent=self.drawlayer, thickness=3)
        self.circle = dpg.draw_circle(center=self.p2, radius=4, fill=(50, 255, 50, 255), parent=self.drawlayer)
        arrow_tip = self._calculate_bezier_xy_at(0.5)
        arrow_base = self._calculate_bezier_xy_at(0.4)
        self.arrow = dpg.draw_arrow(arrow_tip, arrow_base, parent=self.drawlayer, size=20)
        if self.name:
            self.name_text = dpg.draw_text(pos=(self.p2[0], self.p2[1] - 25), text=self.name,
                                           parent=self.drawlayer, size=20)

    def _calculate_bezier_xy_at(self, percent):
        t = percent
        x = (1 - t) * (1 - t) * self.p1[0] + 2 * (1 - t) * t * self.p2[0] + t * t * self.p3[0]
        y = (1 - t) * (1 - t) * self.p1[1] + 2 * (1 - t) * t * self.p2[1] + t * t * self.p3[1]

        return x, y
