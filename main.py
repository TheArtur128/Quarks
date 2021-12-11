from os import path

import pygame
import pymunk.pygame_util
from random import randint as random
from random import choice

pymunk.pygame_util.positive_y_is_up = False


class App:
    """Класс-менеджер для работы с pygame приложением"""
    def __init__(self, visibility, size, FPS, icon=None, caption=None):
        self.__caption = caption
        self.__size = size
        self.__FPS = FPS
        self.__icon = icon
        self.__visibility = visibility
        self.__time = True

    def __app_creation(self):
        self.__window = pygame.display.set_mode(self.__size)
        self.__clock = pygame.time.Clock()
        if self.__icon is not None: pygame.display.set_icon(self.__icon)
        if self.__caption is not None: pygame.display.set_caption(self.__caption)
        self.__pymunk_visibility = pymunk.pygame_util.DrawOptions(self.__window)
        self.__space = self.__create_space()

    def __create_space(self):
        space = pymunk.Space()
        space.gravity = 0, 0
        return space

    def __set_initial_game_scene(self):
        GameZone(space=self.__space, size=[side+8 for side in self.__size], x=self.__size[0]//2, y=self.__size[1]//2, color=(30, 30, 30), border_thickness=8)
        objects_classes = Quark.get_bottom_inheritance_tree()
        objects_classes.remove(Quark)
        for _ in range(128):
            choice(objects_classes)(space=self.__space, x=random(0, self.__size[0]), y=random(0, self.__size[1]))

    def __button_maintenance(self):
        for action in pygame.event.get():
            if action.type == pygame.QUIT:
                self.stop()

    def __computation_everything(self):
        for object in self.__visibility:
            if object.__class__ in Quark.get_bottom_inheritance_tree():
                object.create_contact_objects_nearby()

        for object in self.__visibility:
            object.computation()

    def __render(self):
        for object in self.__visibility:
            object.draw(self.__window)
        self.__space.debug_draw(self.__pymunk_visibility)
        pygame.display.update()

    def __interrupt(self):
        self.__clock.tick(self.__FPS)
        self.__space.step(1 / self.__FPS)

    def run(self):
        self.__app_creation()
        self.__set_initial_game_scene()

        while True:
            self.__button_maintenance()
            self.__computation_everything()
            self.__render()
            self.__interrupt()

    def stop(self):
        pygame.quit()
        exit()

    @property
    def size(self): return tuple(self.__size)

    @property
    def computation_zones(self): return tuple(self.__computation_zones)


class GameObject:
    visibility = []

    def __init__(self, x, y, color="random"):
        GameObject.visibility.append(self)
        self.x = x
        self.y = y
        self.color = [random(0, 255) for _ in range(3)] if color == "random" else color

    def computation(self):
        pass

    def draw(self, surface):
        pass    

    @staticmethod
    def get_objects_near_point(point, radius):
        objects_nearby = []
        for object in GameObject.visibility:
            if (
                point[0]+radius >= object.x >= point[0]-radius
                and point[1]+radius >= object.y >= point[1]-radius
            ):
                objects_nearby.append(object)
        return objects_nearby

    @classmethod
    def get_bottom_inheritance_tree(cls):
        tree = [cls]
        while True:
            found = False
            for class_ in tree:
                for sub_class in class_.__subclasses__():
                    if not sub_class in tree:
                        tree.append(sub_class)
                        found = True
            if not found:
                return tree    


class GameZone(GameObject):
    def __init__(self, space, x, y, size, border_thickness, color="random"):
        super().__init__(x=x, y=y, color=color)
        self.size = size
        #Тема стен будет переосмысленна
        create_border(space, [self.x-self.size[0]//2, self.y-self.size[1]//2], [self.x-self.size[0]//2, self.y+self.size[1]//2], border_thickness)
        create_border(space, [self.x+self.size[0]//2, self.y-self.size[1]//2], [self.x+self.size[0]//2, self.y+self.size[1]//2], border_thickness)
        create_border(space, [self.x-self.size[0]//2, self.y-self.size[1]//2], [self.x+self.size[0]//2, self.y-self.size[1]//2], border_thickness)
        create_border(space, [self.x-self.size[0]//2, self.y+self.size[1]//2], [self.x+self.size[0]//2, self.y+self.size[1]//2], border_thickness)

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            self.color,
            (
                self.x - self.size[0]//2,
                self.y - self.size[1]//2,
                *self.size
            )
        )


class Quark(GameObject):
    """Базовый класс частиц"""
    def __init__(self, space, x, y, max_contacts=3, mass=1, radius=8, color=None):
        if color is None: color = self.__class__.color
        super().__init__(x=x, y=y, color=color)
        self.body, self.form = create_circle(space=space, x=x, y=y, mass=mass, radius=radius, color=color)
        self.max_contacts = max_contacts
        self.contacts = []

    def computation(self):
        self.x, self.y = self.body.position
        self.activation_contacts()

    def activation_contacts(self):
        for contact in self.contacts:
            self.contacts.remove(contact)
            contact.action()

    def create_contact_objects_nearby(self):
        for object in self.objects_nearby:
            if len(self.contacts) < self.max_contacts:
                self.__create_contact(object)
            else:
                break

    def __create_contact(self, object):
        try:
            contact = self.connections_for_objects[object.__class__]
        except KeyError:
            contact = self.connections_for_objects["default"]
        finally:
            self.contacts.append(contact(initiator=self, victim=object))

    @property
    def objects_nearby(self):
        objects = self.get_objects_near_point([self.x, self.y], self.form.radius*6)
        for object in objects:
            if not object.__class__ in Quark.get_bottom_inheritance_tree():
                objects.remove(object)

        objects.remove(self)
        return objects

    @property
    def connections_for_objects(self):
        return {
            "default": Contact
        }


class RedQuark(Quark):
    color = (255, 10, 60, 255)

    @property
    def connections_for_objects(self):
        return {
            "default": Gravitational
        }


class BlueQuark(Quark):
    color = (128, 128, 255, 255)

    @property
    def connections_for_objects(self):
        return {
            "default": Negative
        }


class Contact:
    """Ака посредник отношений"""
    def __init__(self, initiator, victim):
        self.initiator = initiator
        self.victim = victim

    def action(self):
        self.iniciator_computation()
        self.iniciator_victim()

    def iniciator_computation(self):
        pass

    def iniciator_victim(self):
        pass


class Negative(Contact):
    def iniciator_computation(self):
        vector = [int(self.initiator.x - self.victim.x), int(self.initiator.y - self.victim.y)]
        for coordinate in [0, 1]:
            if vector[coordinate] > 0: vector[coordinate] = 1
            elif vector[coordinate] == 0: vector[coordinate] = 0
            else: vector[coordinate] = -1

        self.initiator.body.position += vector


class Gravitational(Contact):
    def iniciator_computation(self):
        vector = [int(self.victim.x - self.initiator.x), int(self.victim.y - self.initiator.y)]
        for coordinate in [0, 1]:
            if vector[coordinate] > 0: vector[coordinate] = 1
            elif vector[coordinate] == 0: vector[coordinate] = 0
            else: vector[coordinate] = -1

        self.initiator.body.position += vector


def create_circle(space, x, y, mass, radius, color="random"):
        body = pymunk.Body(
            mass,
            pymunk.moment_for_circle(mass, 0, radius)
        )
        body.position = [x, y]

        form = pymunk.Circle(
            body=body,
            radius=radius
        )
        form.elasticity = 0.8
        form.friction = 0.5
        form.color = [random(0, 255) for _ in range(4)] if color == "random" else color
        space.add(body, form)
        return (body, form)


def create_border(space, first_point, second_point, thickness):
    body = space.static_body
    form = pymunk.Segment(body, first_point, second_point, thickness)
    form.elasticity = 0.8
    form.friction = 0.5
    space.add(form)
    return (body, form)


def clear_duplicate_elements(array: list):
    for item in array:
        for _ in range(array.count(item) - 1):
            array.remove(item)


if __name__ == "__main__":
    App(
        visibility=GameObject.visibility,
        caption="Quarks",
        size=[640, 460],
        FPS=60,
        icon=pygame.image.load(f"{path.dirname(path.abspath(__file__))}/material/icon.png"), #Автор иконок: https://www.freepik.com from https://www.flaticon.com/ru/
    ).run()
