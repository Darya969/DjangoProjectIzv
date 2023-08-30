from django.db import models
from datetime import date, datetime
from django.contrib.auth.models import User

def get_first_day_of_month():
    return datetime.today().replace(day=1).date()

class IndexForm(models.Model):
    mesto_obracheniya = models.ForeignKey('MestoObracheniya', on_delete=models.PROTECT,
                                          verbose_name='Место выявления', null=True)
    place_of_detection = models.ForeignKey('PlaceOfDetection', on_delete=models.PROTECT,
                                           verbose_name='Основное место', null=True)
    lastname = models.CharField(max_length=50, verbose_name='Фамилия')
    firstname = models.CharField(max_length=50, verbose_name='Имя')
    middle_name = models.CharField(max_length=50, verbose_name='Отчество', blank=True)
    sex = models.ForeignKey('Sex', on_delete=models.PROTECT, verbose_name='Пол')
    date_bith = models.DateField(max_length=10, auto_now=False, verbose_name='Дата рождения')
    locality = models.CharField(max_length=100, verbose_name='Населенный пункт', help_text='г. Саратов')
    district = models.ForeignKey('District', on_delete=models.PROTECT, verbose_name='Район')
    street = models.CharField(max_length=100, verbose_name='Улица')
    home = models.CharField(max_length=100, verbose_name='Дом')
    body = models.CharField(blank=True, max_length=100, verbose_name='Корпус')
    flat = models.CharField(blank=True, max_length=20, verbose_name='Квартира')
    citizen = models.ForeignKey('Citizen', on_delete=models.PROTECT, verbose_name='Житель')
    social_group = models.ForeignKey('SocialGroup', on_delete=models.PROTECT, verbose_name='Социальная группа')
    job = models.CharField(max_length=150, verbose_name='Место работы', blank=True)
    post = models.ForeignKey('Post', on_delete=models.PROTECT, verbose_name='Должность')
    date_of_application = models.DateField(max_length=10, auto_now=False, verbose_name='Дата обращения')
    category1 = models.ForeignKey('Category1', on_delete=models.PROTECT, verbose_name='Категория больного')
    diagnosis = models.ForeignKey('Diagnosis', on_delete=models.PROTECT, verbose_name='Диагноз')
    circumstances_of_detection = models.ForeignKey('CircumstancesOfDetection', on_delete=models.PROTECT,
                                                   verbose_name='Обстоятельства выявления')
    date_of_establishment = models.DateField(max_length=10, auto_now=False, verbose_name='Дата установления')
    physician = models.ForeignKey('Physician', on_delete=models.PROTECT, verbose_name='Врач')
    laboratory_confirmation = models.ForeignKey('LaboratoryConfirmation', on_delete=models.PROTECT,
                                                verbose_name='Лабораторное подтверждение')
    DATE_ZAP = models.DateField(default=get_first_day_of_month)
    VRACH = models.CharField(max_length=50, verbose_name='VRACH')
    create_at1 = models.DateTimeField(verbose_name='Дата публикации', null=True, auto_now_add=True)
    LAB_POT_RAS = models.CharField(max_length=50, verbose_name='LAB_POT_RAS', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.lastname

    class Meta:
        verbose_name = 'Извещение'
        verbose_name_plural = 'Извещения'
        ordering = ['-id', 'lastname', 'date_bith']


class MestoObracheniya(models.Model):
    osnovnoe_mesto_obr = models.ForeignKey('PlaceOfDetection', on_delete=models.PROTECT,
                                           verbose_name='Основное место', null=True)
    title = models.CharField(max_length=500, db_index=True, verbose_name='Место Обращения')
    is_hidden = models.BooleanField(default=False, verbose_name='Скрыть данные')

    def __str__(self):
        return self.title

    def get_data(self):
        if self.hide_data:
            return "Data is hidden"
        else:
            return self.title

    class Meta:
        verbose_name = 'Место Обращения'
        verbose_name_plural = 'Места Обращения'
        ordering = ['title']

class PlaceOfDetection(models.Model):
    title = models.CharField(max_length=100, db_index=True, verbose_name='Основное место обращения')
    is_hidden = models.BooleanField(default=False, verbose_name='Скрыть данные')

    def __str__(self):
        return self.title

    def get_data(self):
        if self.hide_data:
            return "Data is hidden"
        else:
            return self.title

    class Meta:
        verbose_name = 'Основное место обращения'
        verbose_name_plural = 'Основные места обращения'
        ordering = ['title']

class Sex(models.Model):
    title = models.CharField(max_length=7, db_index=True, verbose_name='Пол')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Пол'
        verbose_name_plural = 'Пол'
        ordering = ['id']

class Post(models.Model):
    title = models.CharField(max_length=100, db_index=True, verbose_name='Должность')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['id']

class District(models.Model):
    title = models.CharField(max_length=100, db_index=True, verbose_name='Район')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'
        ordering = ['id']

class Citizen(models.Model):
    title = models.CharField(max_length=100, db_index=True, verbose_name='Житель')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Житель'
        verbose_name_plural = 'Жители'
        ordering = ['title']

class SocialGroup(models.Model):
    title = models.CharField(max_length=100, db_index=True, verbose_name='Социальная группа')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Социальная группа'
        verbose_name_plural = 'Социальные группы'
        ordering = ['-title']

class Category1(models.Model):
    title = models.CharField(max_length=50, db_index=True, verbose_name='Категория больного')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория больного'
        verbose_name_plural = 'Категории больных'
        ordering = ['title']

class Diagnosis(models.Model):
    group_of_diagnoses = models.ForeignKey('GroupOfDiagnoses', on_delete=models.PROTECT,
                                           verbose_name='Группа диагнозов', null=True)
    title = models.CharField(max_length=600, db_index=True, verbose_name='Диагноз')
    mkb = models.CharField(max_length=50, db_index=True, verbose_name='МКБ-10')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Диагноз'
        verbose_name_plural = 'Диагнозы'
        ordering = ['id', 'title', 'mkb']

class GroupOfDiagnoses(models.Model):
    title = models.CharField(max_length=50, db_index=True, verbose_name='Группа диагнозов')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа диагнозов'
        verbose_name_plural = 'Группы диагнозов'
        ordering = ['title']

class CircumstancesOfDetection(models.Model):
    title = models.CharField(max_length=200, db_index=True, verbose_name='Обстоятельства выявления')
    is_published = models.BooleanField(default=True, verbose_name='Скрыто')

    def __str__(self):
        return self.title

    def get_data(self):
        if self.hide_data:
            return "Data is hidden"
        else:
            return self.title

    class Meta:
        verbose_name = 'Обстоятельства выявления'
        verbose_name_plural = 'Обстоятельства выявления'
        ordering = ['title']

class Physician(models.Model):
    title = models.CharField(max_length=200, db_index=True, verbose_name='Врач')
    place_of_work = models.ForeignKey('PlaceOfWork', on_delete=models.PROTECT,
                                      verbose_name='Место работы', null=True)
    is_hidden = models.BooleanField(default=False, verbose_name='Скрыть данные')

    def __str__(self):
        return self.title

    def get_data(self):
        if self.hide_data:
            return "Data is hidden"
        else:
            return self.title

    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'
        ordering = ['title']

class PlaceOfWork(models.Model):
    title = models.CharField(max_length=500, db_index=True, verbose_name='Место работы')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Место работы'
        verbose_name_plural = 'Места работы'
        ordering = ['title']

class LaboratoryConfirmation(models.Model):
    title = models.CharField(max_length=200, db_index=True, verbose_name='Лабораторное подтверждение')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Лабораторное подтверждение'
        verbose_name_plural = 'Лабораторные подтверждения'
        ordering = ['title']

class InfoMain(models.Model):
    about = models.TextField(max_length=1200, db_index=True, verbose_name='О нас')
    work_mode = models.TextField(max_length=1200, db_index=True, verbose_name='Режим работы')
    activity = models.TextField(max_length=1200, db_index=True, verbose_name='Деятельность')
    address1 = models.TextField(max_length=100, db_index=True, verbose_name='Адрес 1')
    number1 = models.CharField(max_length=20, db_index=True, verbose_name='Номер 1')
    address2 = models.CharField(max_length=100, db_index=True, verbose_name='Адрес 2')
    number2 = models.CharField(max_length=20, db_index=True, verbose_name='Номер 2')
    address3 = models.CharField(max_length=100, db_index=True, verbose_name='Адрес 3')
    number3 = models.CharField(max_length=20, db_index=True, verbose_name='Номер 3')

    def __str__(self):
        return self.about

    class Meta:
        verbose_name = 'Главная'
        verbose_name_plural = 'Главная'
        ordering = ['about', 'work_mode', 'activity']

class MonthClosure(models.Model):
    month = models.DateField(verbose_name='Месяц')
    is_closed = models.BooleanField(default=False, verbose_name='Закрытие месяца')

    class Meta:
        verbose_name = 'Закрытие месяца'
        verbose_name_plural = 'Закрытие месяца'

    def __str__(self):
        return f'{self.month} - {"Закрыт" if self.is_closed else "Открыт"}'