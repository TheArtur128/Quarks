from math import sqrt
from os import path

import pygame
from random import randint as random


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


class GameObject:
    """Класс всех игровых обьектов, управляемых App-хой. Абстрактный класс.
    Требует у наслед. классов присутствие интерфейса формы"""
    visibility = []

    def __init__(self, x, y, color="random", *interface_attributes):
        GameObject.visibility.append(self)
        self.x = x
        self.y = y
        self.__color = color if color != "random" else (random(0, 255), random(0, 255), random(0, 255))
        #Запускаем инит интерфейса
        if len(self.__class__.__bases__) > 1:
            self.__class__.__bases__[1].__init__(self, *interface_attributes)
            self._install_hitboxes()
        else:
            raise AttributeError ("needs a form interface")

    def die(self):
        self.__dict__ = {}
        self.__class__.visibility.remove(self)

    def computation(self):
        self._install_hitboxes()

    @classmethod
    def delete_all(cls):
        for object in cls.visibility:
            object.die()

    @property
    def color(self): return self.__color


class FormInterface:
    @staticmethod
    def get_points_distance(first_point, second_point):
        return int(sqrt((second_point[0]-first_point[0])**2+(second_point[1]-first_point[1])**2))

    @staticmethod
    def get_points_distance_by_coordinates(first_point, second_point):
        x = first_point[0] - second_point[0]
        y = first_point[1] - second_point[1]
        return [x, y]

    @staticmethod
    def get_distance_of_vector(vector):
        return FormInterface.get_points_distance(vector, [0, 0])

    @staticmethod
    def get_minimal_vector(*vectors):
        distances = [FormInterface.get_distance_of_vector(vector) for vector in vectors]
        return vectors[distances.index(min(distances))]

    @staticmethod
    def sorting_duplicate_values(list):
        for value in list:
            if list.count(value) > 1:
                while True:
                    if list.count(value) > 1:
                        list.remove(value)
                    else:
                        break


class Circle(FormInterface):
    """Интерфейс кружочко-образной формы"""
    def __init__(self, radius=7):
        self.radius = radius

    def _install_hitboxes(self):
        self.hitboxes = []
        for i in range(360):
            vec = pygame.math.Vector2(0, self.radius).rotate(i)
            self.hitboxes.append([int(self.x+vec.x), int(self.y+vec.y)])
        self.sorting_duplicate_values(self.hitboxes)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)


class Square(FormInterface):
    """Интерфейс квадратной формы"""
    def __init__(self, size_of_sides=12):
        self.__size_of_sides = size_of_sides

    def _install_hitboxes(self):
        self.hitboxes = []
        for i in range(self.__size_of_sides):
            self.hitboxes.extend([
                (self.x-self.__size_of_sides//2+i, self.y-self.__size_of_sides//2),
                (self.x-self.__size_of_sides//2+i, self.y+self.__size_of_sides//2),
                (self.x-self.__size_of_sides//2, self.y-self.__size_of_sides//2+i),
                (self.x-self.__size_of_sides//2, self.y+self.__size_of_sides//2-i)
            ])
        self.sorting_duplicate_values(self.hitboxes)

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            self.color,
            (
                self.x,
                self.y,
                self.__size_of_sides,
                self.__size_of_sides
            )
        )


class GameZone(GameObject, Square):
    """Игровая поверхность игры"""
    def __repr__(self): return "GameZone"


class Quark(GameObject, Circle):
    """Абстрактный класс частиц без взаимодейсвием с другими обьектами"""
    def __init__(self, speed: int, radar_range: int, *atr):
        super().__init__(*atr)
        self.speed = speed
        self.__radar_range = radar_range

    def absorption(self, object):
        self.radius += object.speed//3
        self.speed += object.speed//3
        object.die()

    def move(self, direction: str, factor=1):
        if "left" in direction: self.x -= self.speed*factor
        if "right" in direction: self.x += self.speed*factor
        if "up" in direction: self.y -= self.speed*factor
        if "down" in direction: self.y += self.speed*factor

    def get_objects_near_me(self):
        objects = []
        for object in GameObject.visibility:
            if object != self:
                for point in object.hitboxes:
                    if (self.x + self.__radar_range >= point[0] >= self.x - self.__radar_range
                    and self.y + self.__radar_range >= point[1] >= self.y - self.__radar_range):
                        objects.append(object)
                        break
        return objects

    def get_distance_from_object(self, object):
        min_distance = None
        min_vector = None
        for self_point in self.hitboxes:
            for object_point in object.hitboxes:
                try:
                    if self.get_points_distance(self_point, object_point) < min_distance:
                        min_distance = self.get_points_distance(self_point, object_point)
                        min_vector = self.get_points_distance_by_coordinates(self_point, object_point)
                except TypeError:
                    min_distance = self.get_points_distance(self_point, object_point)
                    min_vector = self.get_points_distance_by_coordinates(self_point, object_point)

        return min_vector

    def computation(self):
        super().computation()
        if self.get_objects_near_me() != []:
            self._interacting_with_nearby_objects()


class Gravitational(Quark, Circle):
    def _interacting_with_nearby_objects(self):
        vectors = []
        for object in self.get_objects_near_me():
            vectors.append(self.get_distance_from_object(object))
            if self.x//self.radius == object.x//self.radius:
                self.absorption(object)

        vector = self.get_minimal_vector(*vectors)
        self.move(
            f'{("left" if vector[0] > 0 else "right")}-{("up" if vector[1] > 0 else "down")}',
        )


class AntiGravitational(Quark, Circle):
    def _interacting_with_nearby_objects(self):
        vectors = [self.get_distance_from_object(object) for object in self.get_objects_near_me()]
        vector = self.get_minimal_vector(*vectors)
        self.move(
            f'{("left" if vector[0] < 0 else "right")}-{("up" if vector[1] < 0 else "down")}',
        )


def set_initial_game_scene():
    GameObject.delete_all()

    GameZone(-500, -500, (40, 40, 40), 1000)
    Gravitational(10, 100, 150, 80)
    Gravitational(10, 100, 350, 280)
    AntiGravitational(10, 100, 250, 180)
    AntiGravitational(10, 100, 275, 180)


if __name__ == "__main__":
    App(
        caption="Quarks",
        size=[480, 360],
        FPS=30,
        computation_zones=[GameObject.visibility],
        icon=pygame.image.load(f"{path.dirname(path.abspath(__file__))}/material/icon.png"), #Автор иконок: https://www.freepik.com from https://www.flaticon.com/ru/
        initial_game_scene=set_initial_game_scene
    ).run()
