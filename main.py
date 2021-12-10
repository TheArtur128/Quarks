from os import path

import pygame
import pymunk.pygame_util
from random import randint as random

pymunk.pygame_util.positive_y_is_up = False


class App:
    """Класс-менеджер для работы с pygame приложением"""
    def __init__(self, size, FPS, icon=None, caption=None):
        self.__caption = caption
        self.__size = size
        self.__FPS = FPS
        self.__icon = icon
        self.__counter_for_changing_gravity = {"real": 0, "full": self.__FPS//4} #Test
        self.__time = True

    def __app_creation(self):
        self.__window = pygame.display.set_mode(self.__size)
        self.__clock = pygame.time.Clock()
        if self.__icon is not None: pygame.display.set_icon(self.__icon)
        if self.__caption is not None: pygame.display.set_caption(self.__caption)
        self.__visibility = pymunk.pygame_util.DrawOptions(self.__window)
        self.__space = self.__create_space()

    def __create_space(self):
        space = pymunk.Space()
        space.gravity = 0, 0
        return space

    def __set_initial_game_scene(self):
        GameZone(space=self.__space, size=self.__size, x=self.__size[0]//2, y=self.__size[1]//2, color=(30, 30, 30), border_thickness=2)
        for i in range(512):
            create_circle(
                space=self.__space, 
                x=random(0, self.__size[0]),
                y=random(0, self.__size[1]),
                mass=1,
                radius=8
            )

    def __button_maintenance(self):
        for action in pygame.event.get():
            if action.type == pygame.QUIT:
                self.stop()

    def __test_condition(self):
        self.__counter_for_changing_gravity["real"] -= 1

        if self.__counter_for_changing_gravity["real"] < 0:
            self.__space.gravity = random(0, 1)*5000, random(0, 1)*5000
            self.__counter_for_changing_gravity["real"] = self.__counter_for_changing_gravity["full"]
            print("THE WORLD!")

    def __render(self):
        for object in GameObject.visibility:
            object.draw(self.__window)
        self.__space.debug_draw(self.__visibility)
        pygame.display.update()

    def __interrupt(self):
        self.__clock.tick(self.__FPS)
        self.__space.step(1 / self.__FPS)

    def run(self):
        self.__app_creation()
        self.__set_initial_game_scene()

        while True:
            self.__interrupt()
            self.__button_maintenance()
            self.__test_condition()
            self.__render()

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

    def draw(self, surface):
        pass


class GameZone(GameObject):
    def __init__(self, space, x, y, size, border_thickness, color="random"):
        super().__init__(x=x, y=y, color=color)
        self.size = size
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
    form.friction = 1.0
    space.add(form)
    return (body, form)


if __name__ == "__main__":
    App(
        caption="Quarks",
        size=[640, 460],
        FPS=60,
        icon=pygame.image.load(f"{path.dirname(path.abspath(__file__))}/material/icon.png"), #Автор иконок: https://www.freepik.com from https://www.flaticon.com/ru/
    ).run()
