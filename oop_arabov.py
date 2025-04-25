from abc import ABC, abstractmethod
import datetime
import json
from typing import Dict, List
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('university.log'),
        logging.StreamHandler()
    ]
)


#исключение и декораторы 
class PermissionDeniedError(Exception):
    """Исключение при отсутствии прав доступа"""
    pass

def check_permissions(allowed_roles):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'get_role'):
                raise PermissionDeniedError("Объект не имеет метода get_role()")
            
            user_role = self.get_role().lower()
            if user_role not in [role.lower() for role in allowed_roles]:
                raise PermissionDeniedError(f"Роль {user_role} не имеет доступа")
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class InvalidPersonError(Exception):
    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(f"Некорректные данные в поле {field_name}: {message}")

class PermissionDeniedError(Exception):
    def __init__(self, action: str, role: str):
        super().__init__(f"Роль '{role}' не имеет прав для выполнения: {action}")

class CourseNotFoundError(Exception):
    def __init__(self, course_name: str):
        super().__init__(f"Курс '{course_name}' не найден")

#Метаклассы

class PersonMeta(type):

    registry={}

    def __new__(cls, name_cls, bases, atributes):
        new_class=super().__new__(cls, name_cls,bases, atributes)
        if name_cls!="Person":
            PersonMeta.registry[name_cls]=new_class
    
        return new_class
    @staticmethod
    def created_by_type(name: str, *args, **kwargs):
        cls=PersonMeta.registry.get(name)
        if not cls:
            raise ValueError(f"Класс {name} не найден в реестре классов")
        return cls(*args, **kwargs)
    


#задание 8-цепочка обязанностей

"""
TeacherHandler - проверяет небольшие изменения в оценке (разница ≤ 1 балл)

DepartmentHeadHandler - проверяет средние изменения в оценке  (разница ≤ 2 балла)

DeanHandler - одобряет любые изменения в оценке
"""

class Grade_Change_Chain(ABC):
    def __init__(self):
        self._next_step=None

    def set_next(self, new_next):
        self._next=new_next
        return self._next
    
    @abstractmethod
    def handle_request(self, request):
        if self._next:
            return self._next.handle_request(request)
        return None  


    
class TeacherHandler(Grade_Change_Chain):
    def handle_request(self, request):
        if abs(request['new_grade'] - request['old_grade']) <= 1:
            print(f"Преподаватель {request['teacher'].get_name()} одобрил изменение оценки "
                  f"с {request['old_grade']} на {request['new_grade']}")
            return True
        else:
            print(f"Преподаватель {request['teacher'].get_name()} передает запрос выше")
            return super().handle_request(request)

class DepartmentHeadHandler(Grade_Change_Chain):
    def handle_request(self, request):
        if abs(request['new_grade'] - request['old_grade']) <= 2:
            print(f"Заведующий кафедрой одобрил изменение оценки "
                  f"с {request['old_grade']} на {request['new_grade']}")
            return True
        else:
            print("Заведующий кафедрой передает запрос декану")
            return super().handle_request(request)

class DeanHandler(Grade_Change_Chain):
    def handle_request(self, request):
        print(f"Декан одобрил изменение оценки "
              f"с {request['old_grade']} на {request['new_grade']}")
        return True
    



    
#Создание абстрактного класса
class Person(ABC, metaclass=PersonMeta):

     #"""Базовый класс для всех участников учебного процесса."""
    
    def __init__(self, person_id: int, name: str, age: int, email: str):
        """Инициализация человека.
        
        Args:
            person_id: Уникальный идентификатор
            name: Имя человека
            age: Возраст
            email: Электронная почта
        """
        self.__person_id = person_id
        self.__name = name
        self.__age = age
        self.__email = email
        logging.info(f"Создан человек: {name}")
    #Сеттеры 
    def set_name(self, new_name):
        if not isinstance(new_name, str):
            raise InvalidPersonError("name", "Имя должно быть строкой")
        self.__name = new_name
        
    def set_age(self, new_age):
        if not isinstance(new_age, int) or new_age <= 0:
            raise InvalidPersonError("age", "Возраст должен быть положительным целым числом")
        self.__age = new_age

    def set_email(self, new_mail):
        if not isinstance(new_mail, str) or "@" not in new_mail:
            raise InvalidPersonError("email", "Почта должна быть строкой с символом @")
        self.__email = new_mail

    #геттеры
    def get_id(self):
        return self.__person_id

    def get_name(self):
        return self.__name

    def get_age(self):
        return self.__age

    def get_email(self):
        return self.__email
    
    @abstractmethod
    def get_role() ->str :
        pass

    def __str__(self)->str:
        result = f"Человек: {self._name}, Возраст: {self._age}"
        return result
    

    def __eq__(self, other) -> bool:
        """Проверка равенства по ID и email"""
        if not isinstance(other, Person):
            return False
        return self.__person_id == other.get_id() and self.__email == other.get_email()
    
    def __lt__(self, other) -> bool:
        """Сравнение по возрасту (меньше значит младше)"""
        if not isinstance(other, Person):
            raise TypeError("Можно сравнивать только объекты Person")
        return self.__age < other.get_age()
    
    def __gt__(self, other) -> bool:
        """Сравнение по возрасту (больше значит старше)"""
        if not isinstance(other, Person):
            raise TypeError("Можно сравнивать только объекты Person")
        return self.__age > other.get_age()
    


    def to_dict(self) -> Dict:
        """Преобразует объект Person в словарь"""
        return {
            'person_id': self.get_id(),
            'name': self.get_name(),
            'age': self.get_age(),
            'email': self.get_email(),
            'class_name': self.__class__.__name__
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Создает объект Person из словаря"""
        return cls(
            person_id=data['person_id'],
            name=data['name'],
            age=data['age'],
            email=data['email']
        )
   
#/////////////////////////////////////////////////////////////////////////////////////////
#Наследование (задание 2)
class Student(Person):
    #"""Класс студента, наследуется от Person."""
    
    def __init__(self, person_id: int, name: str, age: int, email: str, student_id: int):
        """Инициализация студента.
        
        Args:
            person_id: Уникальный идентификатор
            name: Имя студента
            age: Возраст
            email: Электронная почта
            student_id: ID студента
        """
        super().__init__(person_id, name, age, email)
        self.__student_id = student_id
        self.__courses = []
        self.__grades = {}
        logging.info(f"Создан студент: {name}, ID: {student_id}")
    def set_courses(self, new_courses):#?
        for i in range(len(new_courses)-1):
            if not isinstance(new_courses[i], str):
             raise TypeError("Переданное значение не являетс строкой")
            else:
             self.__courses.append(new_courses[i])



    def set_grade(self,new_grades,course_name ):
        if not isinstance(new_grades, int ) or (new_grades <=0 and new_grades>5):
            raise ValueError("Передали не подходящий вид оценки")
        else:
            if course_name not in self.__courses:
                self.__courses.append(course_name)
            self.__grades[course_name]=new_grades
    
    def get_st_id(self):
        return self.__student_id
    
    def get_courses(self):
        return self.__courses
    
    def get_grades(self):
        return self.__grades

    def __str__(self):
        return f" Студент {self.__name}, Курсы {self.__courses}"

    
    def get_role(self):
        return "Студент"
    
    def __eq__(self, other) -> bool:
        """Проверка равенства по ID студента"""
        if not isinstance(other, Student):
            return False
        return super().__eq__(other) and self.__student_id == other.get_st_id()
    
    def __lt__(self, other) -> bool:
        """Сравнение студентов по количеству курсов"""
        if not isinstance(other, Student):
            raise TypeError("Можно сравнивать только объекты Student")
        return len(self.__courses) < len(other.get_courses())
    
    def __gt__(self, other) -> bool:
        """Сравнение студентов по количеству курсов"""
        if not isinstance(other, Student):
            raise TypeError("Можно сравнивать только объекты Student")
        return len(self.__courses) > len(other.get_courses())
    
    def change_grade(self, course_name, new_grade, teacher, handler):
        if course_name not in self.__grades:
            raise CourseNotFoundError(course_name)
        
        request = {
            'student': self,
            'course': course_name,
            'old_grade': self.__grades[course_name],
            'new_grade': new_grade,
            'teacher': teacher
        }
        
        if handler.handle_request(request):
            self.__grades[course_name] = new_grade
            print(f"Оценка успешно изменена на {new_grade}")
        else:
            print("Изменение оценки не было одобрено")


    def to_dict(self) -> Dict:
        """Преобразует объект Student в словарь"""
        person_data = super().to_dict()
        student_data = {
            'student_id': self.get_st_id(),
            'courses': self.get_courses(),
            'grades': self.get_grades()
        }
        return {**person_data, **student_data}

    @classmethod
    def from_dict(cls, data: Dict):
        """Создает объект Student из словаря"""
        student = cls(
            person_id=data['person_id'],
            name=data['name'],
            age=data['age'],
            email=data['email'],
            student_id=data['student_id']
        )
        
        for course in data['courses']:
            student.set_courses([course])
            
        for course, grade in data['grades'].items():
            student.set_grade(grade, course)
            
        return student
    
#/////////////////////////////////////////////////////////////////////////////////////////
class Teacher(Person):
    #"""Класс преподавателя, наследуется от Person."""
    
    def __init__(self, person_id: int, name: str, age: int, email: str, teacher_id: int):
        """Инициализация преподавателя.
        
        Args:
            person_id: Уникальный идентификатор
            name: Имя преподавателя
            age: Возраст
            email: Электронная почта
            teacher_id: ID преподавателя
        """
        super().__init__(person_id, name, age, email)
        self.__teacher_id = teacher_id
        self.__subjects = []
        logging.info(f"Создан преподаватель: {name}, ID: {teacher_id}")


    def set_subjects(self, new_sub):
        if not isinstance(new_sub, str):
            raise TypeError("Переданное значение не является строкой")
        self.__subjects.append(new_sub)


    def get_subjects(self):
        return self.__subjects
    
    def get_tch_id(self):
        return self.__teacher_id
    

    def get_role(self):
        return "Преподаватель"
    
    def __str__(self):
        return f" Преподаватель {self.__name}, Предметы {self.__courses}"
    

    def __eq__(self, other) -> bool:
        """Проверка равенства по ID преподавателя"""
        if not isinstance(other, Teacher):
            return False
        return super().__eq__(other) and self.__teacher_id == other.get_tch_id()
    
    def __lt__(self, other) -> bool:
        """Сравнение преподавателей по количеству предметов"""
        if not isinstance(other, Teacher):
            raise TypeError("Можно сравнивать только объекты Teacher")
        return len(self.__subjects) < len(other.get_subjects())
    
    def __gt__(self, other) -> bool:
        """Сравнение преподавателей по количеству предметов"""
        if not isinstance(other, Teacher):
            raise TypeError("Можно сравнивать только объекты Teacher")
        return len(self.__subjects) > len(other.get_subjects())
    

    def to_dict(self) -> Dict:
        """Преобразует объект Teacher в словарь"""
        person_data = super().to_dict()
        teacher_data = {
            'teacher_id': self.get_tch_id(),
            'subjects': self.get_subjects()
        }
        return {**person_data, **teacher_data}

    @classmethod
    def from_dict(cls, data: Dict):
        """Создает объект Teacher из словаря"""
        teacher = cls(
            person_id=data['person_id'],
            name=data['name'],
            age=data['age'],
            email=data['email'],
            teacher_id=data['teacher_id']
        )
        
        for subject in data['subjects']:
            teacher.set_subjects(subject)
            
        return teacher

#/////////////////////////////////////////////////////////////////////////////////////////
#Интерфейсы для работы с обр. учреждением (4 задание)
    
class Enrollable(ABC):
    @abstractmethod
    def enroll_student(self, student):
        pass


class Reportable(ABC):
    @abstractmethod

    def generate_report(self):
        pass


class LoggingMixin:
    def log_action(self, message: str, log_file: str = "info_about_logs.txt"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        with open(log_file, "a", encoding="utf-8") as file:
            file.write(full_message)


class NotificationMixin:
    def send_notification(self, message: str):
        print(f"[NOTIFICATION] {message}")

#/////////////////////////////////////////////////////////////////////////////////////////
#Композиция и агрегация 

class Courses(Enrollable, Reportable, LoggingMixin, NotificationMixin):
     

    #композиция
    class Materials:
        def __init__(self):
            self.__lectures = []          
        def add_lecture(self, lecture: str):
            self.__lectures.append(lecture)

        
        def get_lectures(self) -> list:
            return self.__lectures
    
        
     #"""Класс для представления учебного курса."""
    
    def __init__(self, courses_id: int, course_name: str, teacher: Teacher):
        """Инициализация курса.
        
        Args:
            courses_id: ID курса
            course_name: Название курса
            teacher: Преподаватель курса
        """
        self.__courses_id = courses_id
        self.__course_name = course_name
        self.__teacher = teacher
        self.__students = []
        logging.info(f"Создан курс: {course_name}, преподаватель: {teacher.get_name()}")


    def set_teacher(self, new_teacher: Teacher):
        if not isinstance(new_teacher, Teacher):
            raise TypeError("Некорректное имя преподавателя")
        self.__teacher=new_teacher

    def set_schedule(self, day, time):
        if not isinstance(day, str) or  not isinstance(time, int):
            raise TypeError("Некорректное значение")
        self.__schedule[day]=time


    def add_student(self, st: Student):
        if not isinstance(st, Student):
            raise TypeError("Некорректное значение")
        if st not in self.__students:
            self.__students.append(st)
        else :
            print("Студент уже записан на курс")


    def remove_student(self, st_name: Student):
         if not isinstance(st_name, Student):
            raise TypeError("Некорректное значение")
         if st_name in self.__students:
            self.__students.remove(st_name)


    def get_course_id(self):
        return self.__courses_id
    
    def get_course_name(self):
        return self.__course_name
    
    def get_course_teacher(self):
        return self.__teacher
    
    def get_students(self):
        return self.__students
    
    def get_schedule(self):
        return self.__schedules
    """
    функция до применения задания 9
    def enroll_student(self, student: Student):
        if not isinstance(student, Student):
            raise TypeError("Можно записывать только студентов.")
        self.add_student(student)
        student.set_courses([self.__course_name])
        the_message=f"Студент {student.get_name()} записан на курс {self.__course_name}"
        self.log_action(the_message, log_file= "info_about_logs.txt")
        self.send_notification(f"Вы записаны на курс {self.get_course_name()}")
"""

    def generate_report(self):
        report=f"Отчет по курсу: {self.course_name}\n"
        report+=f"Преподаватель {self.get_course_teacher}\n"
        report+=f"Количество студентов {len(self.__students)}\n"
        report+=f"Список студентов \n"

        for i, student in enumerate(self.__students, start=1):
         report += f"{i}. Студент {student.get_name()} ID({student.get_st_id()})\n"

    @check_permissions(["teacher", "admin"]) 
    def enroll_student(self, student: Student):
        if not isinstance(student, Student):
            raise TypeError("Можно записывать только студентов.")
        if student in self.__students:
            raise ValueError("Студент уже записан на этот курс")
        self.__students.append(student)
        student.set_courses([self.__course_name])
        self.log_action(f"Студент {student.get_name()} записан на курс {self.__course_name}")


    def to_dict(self) -> Dict:
        """Преобразует объект Courses в словарь"""
        return {
            'courses_id': self.get_course_id(),
            'course_name': self.get_course_name(),
            'teacher': self.get_course_teacher().to_dict() if self.get_course_teacher() else None,
            'students': [student.to_dict() for student in self.get_students()],
            'schedule': self.get_schedule(),
            'materials': [lecture for lecture in self.__course_materials.get_lectures()]
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Создает объект Courses из словаря"""
        teacher = Teacher.from_dict(data['teacher']) if data['teacher'] else None
        course = cls(
            courses_id=data['courses_id'],
            course_name=data['course_name'],
            teacher=teacher
        )
        
        for student_data in data['students']:
            student = Student.from_dict(student_data)
            course.add_student(student)
            
        for day, time in data['schedule'].items():
            course.set_schedule(day, time)
            
        for lecture in data['materials']:
            course.__course_materials.add_lecture(lecture)
            
        return course

#задание 7 -фабричные методы
class PersonFactory:
    @staticmethod
    def create_person(person_type: str, *args, **kwargs):
        return PersonMeta.created_by_type(person_type, *args, **kwargs)
    



#задание 9-Шаблонный метод
    
class EnrollmentProcess(ABC, LoggingMixin, NotificationMixin):
    def enroll_student(self, student: Student, course: Courses) -> bool:
        """Шаблонный метод, определяющий общую структуру процесса записи"""
        self.log_action(f"Начало процесса записи студента {student.get_name()} на курс {course.get_course_name()}")

        if not self._verify_student_eligibility(student):
            self.notify("Студент не соответствует требованиям")
            return False

        if not self._check_course_availability(course):
            self.notify("Курс недоступен для записи")
            return False

        if not self._register_student(student, course):
            self.notify("Ошибка при регистрации")
            return False

        self._process_payment(student, course)
        self._send_confirmation(student, course)
        self._post_registration_actions(student, course)

        self.log_action(f"Студент {student.get_name()} успешно записан на курс {course.get_course_name()}")
        return True

    # Шаги процесса (абстрактные методы)
    @abstractmethod
    def _verify_student_eligibility(self, student: Student) -> bool:
        pass

    @abstractmethod
    def _check_course_availability(self, course: Courses) -> bool:
        pass

    @abstractmethod
    def _register_student(self, student: Student, course: Courses) -> bool:
        pass

    @abstractmethod
    def _process_payment(self, student: Student, course: Courses):
        pass

    @abstractmethod
    def _send_confirmation(self, student: Student, course: Courses):
        pass

    def _post_registration_actions(self, student: Student, course: Courses):
        pass

class OnlineEnrollmentProcess(EnrollmentProcess):
    def _verify_student_eligibility(self, student: Student) -> bool:
        """Проверка технических требований для онлайн-курса"""
        print("Проверка email и доступа к платформе...")
        return "@" in student.get_email()  # Простая проверка email

    def _check_course_availability(self, course: Courses) -> bool:
        """Проверка свободных мест в онлайн-курсе"""
        print("Проверка доступности онлайн-курса...")
        return len(course.get_students()) < 100  # Лимит для онлайн-курсов

    def _register_student(self, student: Student, course: Courses) -> bool:
        """Онлайн-регистрация"""
        print(f"Создание учетной записи для {student.get_name()} на обучающей платформе...")
        try:
            course.enroll_student(student)
            return True
        except Exception as e:
            self.log_action(f"Ошибка онлайн-регистрации: {str(e)}")
            return False

    def _process_payment(self, student: Student, course: Courses):
        """Онлайн-платеж"""
        print(f"Перенаправление на платежный шлюз для {student.get_name()}...")

    def _send_confirmation(self, student: Student, course: Courses):
        """Электронное подтверждение"""
        print(f"Отправка email-подтверждения на {student.get_email()}")
        self.notify(f"Вы записаны на онлайн-курс {course.get_course_name()}")

class OfflineEnrollmentProcess(EnrollmentProcess):
    def _verify_student_eligibility(self, student: Student) -> bool:
        """Проверка документов для очного обучения"""
        print("Проверка документов и возраста студента...")
        return student.get_age() >= 18  # Только для совершеннолетних

    def _check_course_availability(self, course: Courses) -> bool:
        """Проверка мест в аудитории"""
        print("Проверка свободных мест в аудитории...")
        return len(course.get_students()) < 30  # Лимит для очных курсов

    def _register_student(self, student: Student, course: Courses) -> bool:
        """Очная регистрация"""
        print(f"Добавление {student.get_name()} в журнал группы...")
        try:
            course.enroll_student(student)
            return True
        except Exception as e:
            self.log_action(f"Ошибка очной регистрации: {str(e)}")
            return False

    def _process_payment(self, student: Student, course: Courses):
        """Оплата через кассу"""
        print(f"Выписка квитанции для оплаты в кассе для {student.get_name()}")

    def _send_confirmation(self, student: Student, course: Courses):
        """Печатное подтверждение"""
        print(f"Печать справки о зачислении для {student.get_name()}")
        self.notify(f"Ваша заявка на курс {course.get_course_name()} одобрена")

    def _post_registration_actions(self, student: Student, course: Courses):
        """Дополнительные действия после регистрации"""
        print(f"Выдача студенческого билета {student.get_st_id()}")


class StandardEnrollment(EnrollmentProcess):
    def _check_availability(self, course: Courses) -> bool:
        
        return len(course.get_students()) < 30  # Лимит 30 студентов

    def _register_student(self, student: Student, course: Courses) -> bool:
        try:
            course.enroll_student(student)
            return True
        except Exception as e:
            self.log_action(f"Ошибка записи: {str(e)}")
            return False

    def _send_confirmation(self, student: Student, course: Courses):
        self.notify(f"Вы записаны на курс {course.get_course_name()}")
        student.set_courses([course.get_course_name()])




# Функции для работы с JSON
def save_to_json(data, filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_from_json(filename: str):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_system_data(students: list[Student], teachers: list[Teacher], courses: list[Courses], filename: str):
    data = {
        'students': [s.to_dict() for s in students],
        'teachers': [t.to_dict() for t in teachers],
        'courses': [c.to_dict() for c in courses]
    }
    save_to_json(data, filename)

def load_system_data(filename: str) -> tuple:
    data = load_from_json(filename)
    
    students = [Student.from_dict(s) for s in data['students']]
    teachers = [Teacher.from_dict(t) for t in data['teachers']]
    courses = [Courses.from_dict(c) for c in data['courses']]
    
    return students, teachers, courses



def main():
    """Основная функция для демонстрации работы системы."""
    try:
        # Инициализация данных
        teacher = Teacher(1, "Иванова Мария Петровна", 45, "ivanova@univ.ru", 101)
        student1 = Student(2, "Петров Иван Сергеевич", 20, "petrov@mail.ru", 202)
        student2 = Student(3, "Сидорова Анна Дмитриевна", 21, "sidorova@mail.ru", 203)
        
        # Создаем курс
        math_course = Courses(1, "Математика", teacher)
        
        # Запись студентов на курс
        enrollment = StandardEnrollment()
        enrollment.enroll_student(student1, math_course)
        enrollment.enroll_student(student2, math_course)
        
        # Установка оценок
        student1.set_grade(4, "Математика")
        student2.set_grade(3, "Математика")
        
        # Демонстрация изменения оценки через цепочку обязанностей
        chain = TeacherHandler()
        chain.set_next(DepartmentHeadHandler()).set_next(DeanHandler())
        
        print("\nПопытка изменить оценку с 4 на 5 (разница 1):")
        student1.change_grade("Математика", 5, teacher, chain)
        
        print("\nПопытка изменить оценку с 3 на 1 (разница 2):")
        student2.change_grade("Математика", 1, teacher, chain)
        
        # Сериализация данных
        print("\nСохранение данных в файл...")
        save_system_data(
            students=[student1, student2],
            teachers=[teacher],
            courses=[math_course],
            filename="university_data.json"
        )
        
        # Десериализация данных
        print("\nЗагрузка данных из файла...")
        loaded_students, loaded_teachers, loaded_courses = load_system_data("university_data.json")
        
        print("\nЗагруженные студенты:")
        for student in loaded_students:
            print(f"- {student.get_name()}, курсы: {student.get_courses()}")
            
    except Exception as e:
        logging.error(f"Ошибка в работе системы: {str(e)}")
        raise

if __name__ == "__main__":
    main()