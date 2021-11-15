from os import path

import pygame


class App:
    """Класс-менеджер для работы с pygame приложением"""
    def __init__(self, size, FPS, computation_zones, initial_game_scene, icon=None, caption=None):
        self.__caption = caption
        self.__size = size
        self.__FPS = FPS
        self.__icon = icon
        self.__computation_zones = computation_zones
        self.__set_initial_game_scene = initial_game_scene
        self.__time = True

    def __app_creation(self):
        self.__window = pygame.display.set_mode(self.__size)
        self.__clock = pygame.time.Clock()
        pygame.display.set_icon(self.__icon) if self.__icon is not None else None
        pygame.display.set_caption(self.__caption) if self.__caption is not None else None

    def __button_maintenance(self):
        for action in pygame.event.get():
            if action.type == pygame.QUIT:
                self.stop()

    def __computation_for_all_objects(self):
        for zone in self.__computation_zones:
            for object in zone:
                object.computation()

    def __render(self):
        for zone in self.__computation_zones:
            for object in zone:
                object.draw(self.__window)

        pygame.display.update()

    def run(self):
        pygame.init()
        self.__app_creation()
        self.__set_initial_game_scene()

        while True:
            self.__clock.tick(self.__FPS)
            self.__button_maintenance()
            if self.__time: self.__computation_for_all_objects()
            self.__render()

    def stop(self):
        pygame.quit()
        exit()

    @property
    def size(self): return tuple(self.__size)

    @property
    def computation_zones(self): return tuple(self.__computation_zones)


#DO TO
class GameObject:
    """Класс всех игровых обьектов, управляемых App-хой. Абстрактный класс.
    Требует у наслед. классов присутствие интерфейса формы"""
    visibility = []

    def __init__(self, x, y, color, *interface_attributes):
        GameObject.visibility.append(self)
        self.__x = x
        self.__y = y
        self.__color = color
        #Запускаем инит интерфейса
        if len(self.__class__.__bases__) > 1:
            self.__class__.__bases__[1].__init__(self, *interface_attributes)

    def __die(self):
        self.__dict__ = {}
        self.__class__.visibility.remove(self)

    def computation(self):
        self._install_hitboxes()

    def object_location_relative_to_me(self, object):
        pass

    @classmethod
    def delete_all(cls):
        for object in cls.visibility:
            object.__die()

    @property
    def x(self): return self.__x

    @property
    def y(self): return self.__y

    @property
    def color(self): return self.__color


class Circle:
    """Интерфейс кружочка-образной формы"""
    def __init__(self, radius):
        self.__radius = radius

    def _install_hitboxes(self):
        self.__hitboxes = []
        for i in range(360):
            vec = pygame.math.Vector2(0, -40).rotate(i)
            self.__hitboxes.append([int(self.x+self.__radius//2+vec.x), int(self.y+self.__radius[0]//2+vec.y)])

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y, self.__radius))


class Square:
    """Интерфейс квадраТыной формы"""
    def __init__(self, size_of_sides):
        self.__size_of_sides = size_of_sides

    def _install_hitboxes(self):
        self.__hitboxes = []
        for i in range(self.__size_of_sides):
            self.__hitboxes.extend([
                (self.x-self.__size_of_sides//2+i, self.y-self.__size_of_sides//2),
                (self.x-self.__size_of_sides//2+i, self.y+self.__size_of_sides//2),
                (self.x-self.__size_of_sides//2, self.y-self.__size_of_sides//2+i),
                (self.x-self.__size_of_sides//2, self.y+self.__size_of_sides//2-i)
            ])

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            self.color,
            (
                self.x-self.__size_of_sides//2,
                self.y-self.__size_of_sides//2,
                self.__size_of_sides,
                self.__size_of_sides
            )
        )


class GameZone(GameObject, Square):
    """Игровая поверхность игры"""
    def computation(self):
        super().computation()


class CircleMan(GameObject, Circle):
    pass


def set_initial_game_scene():
    GameObject.delete_all()

    GameZone(-500, -500, (40, 40, 40), 1000)


if __name__ == "__main__":
    App(
        caption="Quarks",
        size=[480, 360],
        FPS=60,
        computation_zones=[GameObject.visibility],
        icon=pygame.image.load(f"{path.dirname(path.abspath(__file__))}/material/icon.png"), #Автор иконок: https://www.freepik.com from https://www.flaticon.com/ru/
        initial_game_scene=set_initial_game_scene
    ).run()
