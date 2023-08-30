from django.contrib import admin
from .models import *

class IndexFormAdmin(admin.ModelAdmin):
    list_display = ('id', 'lastname', 'firstname', 'middle_name', 'date_bith', 'user')
    # list_display_links = ('id',)
    # search_fields = ('id',)

class MestoObracheniyaAdmin(admin.ModelAdmin):
    list_display = ('osnovnoe_mesto_obr', 'title', 'is_hidden')
    list_display_links = ('osnovnoe_mesto_obr', 'title')
    search_fields = ('osnovnoe_mesto_obr', 'title', 'is_hidden')
    list_editable = ('is_hidden',)

class PlaceOfDetectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_hidden')
    list_display_links = ('title',)
    search_fields = ('title', 'is_hidden')
    list_editable = ('is_hidden',)

class CircumstancesOfDetectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published')
    list_display_links = ('title',)
    search_fields = ('title', 'is_published')
    list_editable = ('is_published',)

class PhysicianAdmin(admin.ModelAdmin):
    list_display = ('title', 'place_of_work', 'is_hidden')
    list_display_links = ('title',)
    search_fields = ('title', 'place_of_work', 'is_hidden')
    list_editable = ('is_hidden',)

class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('title', 'mkb', 'group_of_diagnoses')

class InfoMainAdmin(admin.ModelAdmin):
    list_display = ('about', 'work_mode', 'activity', 'address1', 'number1', 'address2', 'number2', 'address3',
                    'number3')

class MonthClosureAdmin(admin.ModelAdmin):
    list_display = ('month', 'is_closed')
    list_filter = ('month', 'is_closed')
    search_fields = ('month',)
    actions = ['close_selected_months', 'reopen_selected_months']

    def close_selected_months(modeladmin, request, queryset):
        queryset.update(is_closed=True)
    close_selected_months.short_description = 'Закрыть выбранные месяцы'

    def reopen_selected_months(modeladmin, request, queryset):
        queryset.update(is_closed=False)
    reopen_selected_months.short_description = 'Открыть выбранные месяцы'

admin.site.register(IndexForm, IndexFormAdmin)
admin.site.register(MestoObracheniya, MestoObracheniyaAdmin)
admin.site.register(PlaceOfDetection, PlaceOfDetectionAdmin)
admin.site.register(Sex)
admin.site.register(Post)
admin.site.register(District)
admin.site.register(Citizen)
admin.site.register(SocialGroup)
admin.site.register(Category1)
admin.site.register(GroupOfDiagnoses)
admin.site.register(Diagnosis, DiagnosisAdmin)
admin.site.register(CircumstancesOfDetection, CircumstancesOfDetectionAdmin)
admin.site.register(Physician, PhysicianAdmin)
admin.site.register(PlaceOfWork)
admin.site.register(LaboratoryConfirmation)
admin.site.register(InfoMain, InfoMainAdmin)
admin.site.register(MonthClosure, MonthClosureAdmin)