from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import ExtractYear
from django.shortcuts import render, redirect
from django.db.models import *
from django.views.generic import ListView, TemplateView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from datetime import timedelta, date
from .forms import *
from .models import *

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home-index')
    else:
        form = UserLoginForm()
    return render(request, 'home/login.html', {"form": form})

def user_logout(request):
    logout(request)
    return redirect('login')

def index(request):
    form = InfoMain.objects.get()
    return render(request, 'home/index.html', {'form': form})

@login_required(login_url='/login/', redirect_field_name = 'redirect_to')
def home_index(request):
    groupobj = GroupOfDiagnoses.objects.all()
    diagnosisobj = Diagnosis.objects.all()
    if request.method == 'POST':
        form = IzveshheniyaForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            messages.success(request, 'Успешно')
            return redirect('home-index')
        else:
            messages.error(request, 'Ошибка')
            errors = form.errors
            return render(request, 'home/home-index.html', {'form': form, 'errors': errors})
    else:
        form = IzveshheniyaForm()

        last_closed_month = MonthClosure.objects.filter(is_closed=True).order_by('-month').first()
        if last_closed_month:
            next_month = last_closed_month.month.month + 1
            next_year = last_closed_month.month.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            form.fields['DATE_ZAP'].initial = date(next_year, next_month, 1)

    return render(request, 'home/home-index.html', {'form': form, 'groupobj': groupobj, 'Diagnoses': diagnosisobj})


def get_diagnoses(request):
    group_id = request.GET.get('group_id')
    diagnoses = Diagnosis.objects.filter(group_of_diagnoses=group_id).values('id', 'title')
    return JsonResponse({'diagnoses': list(diagnoses)})

class Search(LoginRequiredMixin, ListView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    template_name = 'home/search_index.html'
    context_object_name = 'form'

    def get_queryset(self):
        lastname = self.request.GET.get('lastname')
        firstname = self.request.GET.get('firstname')
        middle_name = self.request.GET.get('middle_name')
        date_bith = self.request.GET.get('date_bith')
        sex = self.request.GET.get('sex')
        district = self.request.GET.get('district')
        locality = self.request.GET.get('locality')
        street = self.request.GET.get('street')

        queryset = None

        if self.request.GET.get('lastname' and 'firstname' and 'middle_name'):
            queryset = IndexForm.objects.filter(
                lastname__contains=lastname,
                firstname__contains=firstname,
                middle_name__contains=middle_name)
            if self.request.GET.get('lastname' and 'firstname' and 'middle_name' and 'date_bith'):
                queryset = IndexForm.objects.filter(
                    lastname__contains=lastname,
                    firstname__contains=firstname,
                    middle_name__contains=middle_name,
                    date_bith__exact=date_bith)
            elif self.request.GET.get('lastname' and 'firstname' and 'middle_name' and 'sex'):
                queryset = IndexForm.objects.filter(
                    lastname__contains=lastname,
                    firstname__contains=firstname,
                    middle_name__contains=middle_name,
                    sex__title=sex)
            elif self.request.GET.get('lastname' and 'firstname' and 'middle_name' and 'district'):
                queryset = IndexForm.objects.filter(
                    lastname__contains=lastname,
                    firstname__contains=firstname,
                    middle_name__contains=middle_name,
                    district__title=district)
            elif self.request.GET.get('lastname' and 'firstname' and 'middle_name' and 'locality' and 'street'):
                queryset = IndexForm.objects.filter(
                    lastname__contains=lastname,
                    firstname__contains=firstname,
                    middle_name__contains=middle_name,
                    locality__contains=locality,
                    street__contains=street)
            elif self.request.GET.get(
                    'lastname' and 'firstname' and 'middle_name' and 'date_bith' and 'sex' and 'district' and
                    'locality' and 'street'):
                queryset = IndexForm.objects.filter(
                    lastname__contains=lastname,
                    firstname__contains=firstname,
                    middle_name__contains=middle_name,
                    date_bith__exact=date_bith,
                    sex__title=sex,
                    district__title=district,
                    locality__contains=locality,
                    street__contains=street)

        elif 'button' in self.request.GET:
            today = date.today()
            start_of_month = date(today.year, today.month, 1)
            end_of_month = start_of_month + timedelta(days=32) - timedelta(days=1)
            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_of_month, end_of_month])

        return queryset


    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        val = self.request.GET.get('lastname')
        context['search'] = val
        context['question2'] = District.objects.values('title').order_by('id')
        context['question3'] = Sex.objects.values('title').order_by('id')
        return context

class Report(LoginRequiredMixin, ListView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    template_name = 'home/report_index.html'
    context_object_name = 'form'

    def get_queryset(self):
        start_date = self.request.GET.get('start_date')
        end_dates = self.request.GET.get('end_dates')
        home = self.request.GET.get('home')
        registered = self.request.GET.get('registered')
        kdo = self.request.GET.get('kdo')
        citizen = self.request.GET.get('citizen')
        group_of_diagnoses = self.request.GET.get('group_of_diagnoses')
        physician_id = self.request.GET.get('physician')
        district_id = self.request.GET.get('district')
        year = self.request.GET.get('year')

        queryset = None

        if home == "По диагнозам":
            if registered == "Все зарегистрированные":
                if kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
            elif registered == "Саратов":
                if kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .filter(mesto_obracheniya_id=432) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .filter(mesto_obracheniya_id=433) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
            elif registered == "Саратовская область":
                if kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432, district_id__lt=47) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433, district_id__lt=47) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(title=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(~Q(district_id=47), then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  citizen_city=Sum(Case(When(~Q(district_id=47), citizen_id=1, then=1), default=0,
                                                        utput_field=models.IntegerField())),
                                  from_saratov=Sum(Case(When(district_id__lt=7, then=1), default=0,
                                                        output_field=models.IntegerField())),
                                  citizen_village=Sum(Case(When(~Q(district_id=47), citizen_id=2, then=1), default=0,
                                                           output_field=models.IntegerField())),
                                  other_area=Sum(Case(When(district_id=47, then=1), default=0,
                                                      output_field=models.IntegerField())),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1), default=0,
                                                            output_field=models.IntegerField())),
                                  total=Count('diagnosis__title'))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
            else:
                if kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id, mesto_obracheniya_id=432) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(total=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(citizen__in=[1, 2], then=1))),
                                  citizen_city=Sum(Case(When(citizen='1', then=1))),
                                  from_saratov=Sum(Case(When(locality__in=["Саратов", "г.Саратов", "г. Саратов"], then=1))),
                                  citizen_village=Sum(Case(When(citizen_id='2', then=1))),
                                  other_area=Sum(Case(When(category1_id='7', then=1))),
                                  foreign_resident=Sum(Case(When(category1_id='8', then=1))))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id, mesto_obracheniya_id=433) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(total=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(citizen__in=[1, 2], then=1))),
                                  citizen_city=Sum(Case(When(citizen='1', then=1))),
                                  from_saratov=Sum(Case(When(locality__in=["Саратов", "г.Саратов", "г. Саратов"], then=1))),
                                  citizen_village=Sum(Case(When(citizen_id='2', then=1))),
                                  other_area=Sum(Case(When(category1_id='7', then=1))),
                                  foreign_resident=Sum(Case(When(category1_id='8', then=1))))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .values('diagnosis__title').order_by('diagnosis__id') \
                        .annotate(total=Count('diagnosis__title'),
                                  total_area=Sum(Case(When(citizen__in=[1, 2], then=1))),
                                  citizen_city=Sum(Case(When(citizen='1', then=1))),
                                  from_saratov=Sum(Case(When(locality__in=["Саратов", "г.Саратов", "г. Саратов"], then=1))),
                                  citizen_village=Sum(Case(When(citizen_id='2', then=1))),
                                  other_area=Sum(Case(When(district_id=47, then=1))),
                                  foreign_resident=Sum(Case(When(district_id=48, then=1))))

                    total_total = queryset.aggregate(total_total=Sum('total'))['total_total'] or 0
                    area = queryset.aggregate(area=Sum('total_area'))['area'] or 0
                    total_citizen_city = queryset.aggregate(total_citizen_city=
                                                            Sum('citizen_city'))['total_citizen_city'] or 0
                    saratov = queryset.aggregate(saratov=Sum('from_saratov'))['saratov'] or 0
                    village = queryset.aggregate(village=Sum('citizen_village'))['village'] or 0
                    other = queryset.aggregate(other=Sum('other_area'))['other'] or 0
                    resident = queryset.aggregate(resident=Sum('foreign_resident'))['resident'] or 0

                    queryset = list(queryset) + [{'diagnosis__title': "Итого", 'total': total_total, 'total_area': area,
                                                  'citizen_city': total_citizen_city, 'from_saratov': saratov,
                                                  'citizen_village': village, 'other_area': other,
                                                  'foreign_resident': resident}]
        if home == "Соц состав":
            if registered == "Все зарегистрированные":
                if citizen:
                    if group_of_diagnoses:
                        if kdo == "КДО-1":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=432,
                                                                citizen__title=citizen) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        elif kdo == "КДО-2":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=433,
                                                                citizen__title=citizen) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses)\
                                .order_by('post__id').values('post__title') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=433,
                                                            citizen__title=citizen) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif group_of_diagnoses:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=432) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=433) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432) \
                        .values('post__title').order_by('post__id') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
            elif registered == "Саратов":
                if citizen:
                    if group_of_diagnoses:
                        if kdo == "КДО-1":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen, district_id__lt=7,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=432) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        elif kdo == "КДО-2":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen, district_id__lt=7,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=433) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen, district_id__lt=7,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses)\
                                .order_by('post__id').values('post__title') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=432, citizen__title=citizen)\
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=433, citizen__title=citizen)\
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            citizen__title=citizen)\
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif group_of_diagnoses:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=432)\
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=433) \
                            .filter(locality__in=["Саратов", "г.Саратов", "г. Саратов"]) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=432) \
                        .values('post__title').order_by('post__id') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=433) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
            elif registered == "Саратовская область":
                if citizen:
                    if group_of_diagnoses:
                        if kdo == "КДО-1":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen, district_id__lt=47,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=432) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        elif kdo == "КДО-2":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen, district_id__lt=47,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=433) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen, district_id__lt=47,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                                .order_by('post__id').values('post__title') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            citizen__title=citizen) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif group_of_diagnoses:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=432) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=433) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432, district_id__lt=47) \
                        .values('post__title').order_by('post__id') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .filter(mesto_obracheniya_id=433) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
            else:
                if citizen:
                    if group_of_diagnoses:
                        if kdo == "КДО-1":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=432,) \
                                .filter(district__title=district_id) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        elif kdo == "КДО-2":
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                mesto_obracheniya_id=433) \
                                .filter(district__title=district_id) \
                                .values('post__title').order_by('post__id') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                                .filter(district__title=district_id) \
                                .order_by('post__id').values('post__title') \
                                .annotate(total_post=Count('post__title'))

                            post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                            queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .filter(district__title=district_id) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif group_of_diagnoses:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=432) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            mesto_obracheniya_id=433) \
                            .values('post__title').order_by('post__id') \
                            .annotate(total_post=Count('post__title'))
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .filter(district__title=district_id) \
                            .order_by('post__id').values('post__title') \
                            .annotate(total_post=Count('post__title'))

                        post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                        queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432, district__title=district_id) \
                        .values('post__title').order_by('post__id') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id, mesto_obracheniya_id=433) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .order_by('post__id').values('post__title') \
                        .annotate(total_post=Count('post__title'))

                    post = queryset.aggregate(post=Sum('total_post'))['post'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'total_post': post}]
        if home == "Соц состав по всем назологиям":
            if registered == "Все зарегистрированные":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
            elif registered == "Саратов":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        citizen__title=citizen) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
            elif registered == "Саратовская область":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        citizen__title=citizen) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
            else:
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen, district__title=district_id) \
                        .order_by('post__title').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  borod=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .order_by('post__id').values('post__title') \
                        .annotate(sif=Sum(Case(When(diagnosis__group_of_diagnoses__in=[2], then=1))),
                                  gon=Sum(Case(When(diagnosis__group_of_diagnoses__in=[3], then=1))),
                                  trih=Sum(Case(When(diagnosis__group_of_diagnoses__in=[4], then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses__in=[5], then=1))),
                                  gerp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[6], then=1))),
                                  boro=Sum(Case(When(diagnosis__group_of_diagnoses__in=[7], then=1))),
                                  trihot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[8], then=1))),
                                  microsp=Sum(Case(When(diagnosis__group_of_diagnoses__in=[9], then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses__in=[10], then=1))),
                                  stop=Sum(Case(When(diagnosis__group_of_diagnoses__in=[11], then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[12], then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses__in=[13], then=1))))

                    total_sif = queryset.aggregate(total_sif=Sum('sif'))['total_sif'] or 0
                    total_gon = queryset.aggregate(total_gon=Sum('gon'))['total_gon'] or 0
                    total_trih = queryset.aggregate(total_trih=Sum('trih'))['total_trih'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerp = queryset.aggregate(total_gerp=Sum('gerp'))['total_gerp'] or 0
                    total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                    total_trihot = queryset.aggregate(total_trihot=Sum('trihot'))['total_trihot'] or 0
                    total_microsp = queryset.aggregate(total_microsp=Sum('microsp'))['total_microsp'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [{'post__title': 'Итого', 'sif': total_sif, 'gon': total_gon,
                                                  'trih': total_trih, 'hlamid': total_hlamid, 'gerp': total_gerp,
                                                  'borod': total_borod, 'trihot': total_trihot,
                                                  'microsp': total_microsp, 'chesot': total_chesot, 'stop': total_stop,
                                                  'nogti': total_nogti, 'kisti': total_kisti}]
        if home == "Кожные заболевания":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                    citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(triho=Sum(Case(When(diagnosis='84', then=1))),
                              trihodet=Sum(Case(When(diagnosis='84',
                                                     date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              gladk=Sum(Case(When(diagnosis='85', then=1))),
                              gladkdet=Sum(Case(When(diagnosis='85',
                                                     date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              borod=Sum(Case(When(diagnosis='75', then=1))),
                              borodet=Sum(Case(When(diagnosis='75',
                                                    date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              tul=Sum(Case(When(diagnosis='76', then=1))),
                              tuldet=Sum(Case(When(diagnosis='76',
                                                   date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              chesot=Sum(Case(When(diagnosis='71', then=1))),
                              chesotdet=Sum(Case(When(diagnosis='71',
                                                      date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              stop=Sum(Case(When(diagnosis='77', then=1))),
                              stopdet=Sum(Case(When(diagnosis='77',
                                                    date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              nogt=Sum(Case(When(diagnosis='78', then=1))),
                              nogtdet=Sum(Case(When(diagnosis='78',
                                                    date_bith__gte=date.today() - timedelta(days=15*365), then=1))))

                total_triho = queryset.aggregate(total_triho=Sum('triho'))['total_triho'] or 0
                total_trihodet = queryset.aggregate(total_trihodet=Sum('trihodet'))['total_trihodet'] or 0
                total_gladk = queryset.aggregate(total_gladk=Sum('gladk'))['total_gladk'] or 0
                total_gladkdet = queryset.aggregate(total_gladkdet=Sum('gladkdet'))['total_gladkdet'] or 0
                total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                total_borodet = queryset.aggregate(total_borodet=Sum('borodet'))['total_borodet'] or 0
                total_tul = queryset.aggregate(total_tul=Sum('tul'))['total_tul'] or 0
                total_tuldet = queryset.aggregate(total_tuldet=Sum('tuldet'))['total_tuldet'] or 0
                total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                total_chesotdet = queryset.aggregate(total_chesotdet=Sum('chesotdet'))['total_chesotdet'] or 0
                total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                total_stopdet = queryset.aggregate(total_stopdet=Sum('stopdet'))['total_stopdet'] or 0
                total_nogt = queryset.aggregate(total_nogt=Sum('nogt'))['total_nogt'] or 0
                total_nogtdet = queryset.aggregate(total_nogtdet=Sum('nogtdet'))['total_nogtdet'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'triho': total_triho, 'trihodet': total_trihodet, 'gladk': total_gladk,
                     'gladkdet': total_gladkdet, 'borod': total_borod, 'borodet': total_borodet, 'tul': total_tul,
                     'tuldet': total_tuldet, 'chesot': total_chesot, 'chesotdet': total_chesotdet, 'stop': total_stop,
                     'stopdet': total_stopdet, 'nogt': total_nogt, 'nogtdet': total_nogtdet}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(triho=Sum(Case(When(diagnosis='84', then=1))),
                              trihodet=Sum(Case(When(diagnosis='84',
                                                     date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              gladk=Sum(Case(When(diagnosis='85', then=1))),
                              gladkdet=Sum(Case(When(diagnosis='85',
                                                     date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              borod=Sum(Case(When(diagnosis='75', then=1))),
                              borodet=Sum(Case(When(diagnosis='75',
                                                    date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              tul=Sum(Case(When(diagnosis='76', then=1))),
                              tuldet=Sum(Case(When(diagnosis='76',
                                                   date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              chesot=Sum(Case(When(diagnosis='71', then=1))),
                              chesotdet=Sum(Case(When(diagnosis='71',
                                                      date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              stop=Sum(Case(When(diagnosis='77', then=1))),
                              stopdet=Sum(Case(When(diagnosis='77',
                                                    date_bith__gte=date.today() - timedelta(days=15*365), then=1))),
                              nogt=Sum(Case(When(diagnosis='78', then=1))),
                              nogtdet=Sum(Case(When(diagnosis='78',
                                                    date_bith__gte=date.today() - timedelta(days=15*365), then=1))))

                total_triho = queryset.aggregate(total_triho=Sum('triho'))['total_triho'] or 0
                total_trihodet = queryset.aggregate(total_trihodet=Sum('trihodet'))['total_trihodet'] or 0
                total_gladk = queryset.aggregate(total_gladk=Sum('gladk'))['total_gladk'] or 0
                total_gladkdet = queryset.aggregate(total_gladkdet=Sum('gladkdet'))['total_gladkdet'] or 0
                total_borod = queryset.aggregate(total_borod=Sum('borod'))['total_borod'] or 0
                total_borodet = queryset.aggregate(total_borodet=Sum('borodet'))['total_borodet'] or 0
                total_tul = queryset.aggregate(total_tul=Sum('tul'))['total_tul'] or 0
                total_tuldet = queryset.aggregate(total_tuldet=Sum('tuldet'))['total_tuldet'] or 0
                total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                total_chesotdet = queryset.aggregate(total_chesotdet=Sum('chesotdet'))['total_chesotdet'] or 0
                total_stop = queryset.aggregate(total_stop=Sum('stop'))['total_stop'] or 0
                total_stopdet = queryset.aggregate(total_stopdet=Sum('stopdet'))['total_stopdet'] or 0
                total_nogt = queryset.aggregate(total_nogt=Sum('nogt'))['total_nogt'] or 0
                total_nogtdet = queryset.aggregate(total_nogtdet=Sum('nogtdet'))['total_nogtdet'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'triho': total_triho, 'trihodet': total_trihodet, 'gladk': total_gladk,
                     'gladkdet': total_gladkdet, 'borod': total_borod, 'borodet': total_borodet, 'tul': total_tul,
                     'tuldet': total_tuldet, 'chesot': total_chesot, 'chesotdet': total_chesotdet, 'stop': total_stop,
                     'stopdet': total_stopdet, 'nogt': total_nogt, 'nogtdet': total_nogtdet}]
        if home == "ЗППП":
            if registered == "Все зарегистрированные":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen)\
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .exclude(diagnosis__group_of_diagnoses__id=14)\
                        .values('diagnosis__group_of_diagnoses__title')\
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [{'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all,
                                                  'allm': total_allm, 'allw': total_allw, 'allm14': total_allm14,
                                                  'allw14': total_allw14, 'allm17': total_allm17, 'allw17': total_allw17,
                                                  'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                                                  'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39,
                                                  'allm40': total_allm40, 'allw40': total_allw40}]
            elif registered == "Саратов":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            citizen__title=citizen)\
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=432) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=433) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .exclude(diagnosis__group_of_diagnoses__id=14)\
                        .values('diagnosis__group_of_diagnoses__title')\
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
            elif registered == "Саратовская область":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47, mesto_obracheniya_id=432,
                                                            citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47, mesto_obracheniya_id=433,
                                                            citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            citizen__title=citizen)\
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        mesto_obracheniya_id=432) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        mesto_obracheniya_id=433) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .exclude(diagnosis__group_of_diagnoses__id=14)\
                        .values('diagnosis__group_of_diagnoses__title')\
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
            else:
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id, mesto_obracheniya_id=432,
                                                            citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id, mesto_obracheniya_id=433,
                                                            citizen__title=citizen) \
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id, citizen__title=citizen)\
                            .exclude(diagnosis__group_of_diagnoses__id=14) \
                            .values('diagnosis__group_of_diagnoses__title') \
                            .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                      allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                      allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                           date_bith__year__gt=(int(year)-18), then=1))),
                                      allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                           date_bith__year__gt=(int(year)-20), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                           date_bith__year__gt=(int(year)-30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                           date_bith__year__gt=(int(year)-40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                            .order_by('diagnosis__group_of_diagnoses__title')

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                        total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                             'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                             'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19,
                             'allm29': total_allm29, 'allw29': total_allw29, 'allm39': total_allm39,
                             'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id, mesto_obracheniya_id=432) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id, mesto_obracheniya_id=433) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .exclude(diagnosis__group_of_diagnoses__id=14)\
                        .values('diagnosis__group_of_diagnoses__title')\
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  allm=Sum(Case(When(sex_id=1, then=Value(1)), default=Value(0))),
                                  allw=Sum(Case(When(sex_id=2, then=Value(1)), default=Value(0))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                       date_bith__year__gt=(int(year)-18), then=1))),
                                  allm19=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allw19=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-17),
                                                       date_bith__year__gt=(int(year)-20), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-19),
                                                       date_bith__year__gt=(int(year)-30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-29),
                                                       date_bith__year__gt=(int(year)-40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))\
                        .order_by('diagnosis__group_of_diagnoses__title')

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm19 = queryset.aggregate(total_allm19=Sum('allm19'))['total_allm19'] or 0
                    total_allw19 = queryset.aggregate(total_allw19=Sum('allw19'))['total_allw19'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'allm': total_allm,
                         'allw': total_allw, 'allm14': total_allm14, 'allw14': total_allw14, 'allm17': total_allm17,
                         'allw17': total_allw17, 'allm19': total_allm19, 'allw19': total_allw19, 'allm29': total_allm29,
                         'allw29': total_allw29, 'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
        if home == "ЗППП по районам (Сифилис - краткий)":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(pervichm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110], then=1))),
                              pervichw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110], then=1))),
                              vtorichm=Sum(Case(When(sex='1', diagnosis__in=[68, 96], then=1))),
                              vtorichw=Sum(Case(When(sex='2', diagnosis__in=[68, 96], then=1))),
                              ranniym=Sum(Case(When(sex='1', diagnosis=69, then=1))),
                              ranniyw=Sum(Case(When(sex='2', diagnosis=69, then=1))),
                              pozdniym=Sum(Case(When(sex='1', diagnosis=114, then=1))),
                              pozdniyw=Sum(Case(When(sex='2', diagnosis=114, then=1))),
                              vrojdenm=Sum(Case(When(sex='1', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111,
                                                                             107], then=1))),
                              vrojdenw=Sum(Case(When(sex='2', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111,
                                                                             107], then=1))),
                              drugiem=Sum(Case(When(sex='1', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120,
                                                                            108], then=1))),
                              drugiew=Sum(Case(When(sex='2', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120,
                                                                            108], then=1))),
                              allm=Sum(Case(
                                  When(sex='1', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                               106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                               95, 113, 120, 108], then=1))),
                              allw=Sum(Case(
                                  When(sex='2', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                               106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                               95, 113, 120, 108], then=1))))

                total_pervichm = queryset.aggregate(total_pervichm=Sum('pervichm'))['total_pervichm'] or 0
                total_pervichw = queryset.aggregate(total_pervichw=Sum('pervichw'))['total_pervichw'] or 0
                total_vtorichm = queryset.aggregate(total_vtorichm=Sum('vtorichm'))['total_vtorichm'] or 0
                total_vtorichw = queryset.aggregate(total_vtorichw=Sum('vtorichw'))['total_vtorichw'] or 0
                total_ranniym = queryset.aggregate(total_ranniym=Sum('ranniym'))['total_ranniym'] or 0
                total_ranniyw = queryset.aggregate(total_ranniyw=Sum('ranniyw'))['total_ranniyw'] or 0
                total_pozdniym = queryset.aggregate(total_pozdniym=Sum('pozdniym'))['total_pozdniym'] or 0
                total_pozdniyw = queryset.aggregate(total_pozdniyw=Sum('pozdniyw'))['total_pozdniyw'] or 0
                total_vrojdenm = queryset.aggregate(total_vrojdenm=Sum('vrojdenm'))['total_vrojdenm'] or 0
                total_vrojdenw = queryset.aggregate(total_vrojdenw=Sum('vrojdenw'))['total_vrojdenw'] or 0
                total_drugiem = queryset.aggregate(total_drugiem=Sum('drugiem'))['total_drugiem'] or 0
                total_drugiew = queryset.aggregate(total_drugiew=Sum('drugiew'))['total_drugiew'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0

                queryset = list(queryset) + [{'district__title': 'Итого', 'pervichm': total_pervichm,
                                              'pervichw': total_pervichw, 'vtorichm': total_vtorichm,
                                              'vtorichw': total_vtorichw, 'ranniym': total_ranniym,
                                              'ranniyw': total_ranniyw, 'pozdniym': total_pozdniym,
                                              'pozdniyw': total_pozdniyw, 'vrojdenm': total_vrojdenm,
                                              'vrojdenw': total_vrojdenw, 'drugiem': total_drugiem,
                                              'drugiew': total_drugiew, 'allm': total_allm, 'allw': total_allw}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(pervichm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110], then=1))),
                              pervichw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110], then=1))),
                              vtorichm=Sum(Case(When(sex='1', diagnosis__in=[68, 96], then=1))),
                              vtorichw=Sum(Case(When(sex='2', diagnosis__in=[68, 96], then=1))),
                              ranniym=Sum(Case(When(sex='1', diagnosis=69, then=1))),
                              ranniyw=Sum(Case(When(sex='2', diagnosis=69, then=1))),
                              pozdniym=Sum(Case(When(sex='1', diagnosis=114, then=1))),
                              pozdniyw=Sum(Case(When(sex='2', diagnosis=114, then=1))),
                              vrojdenm=Sum(Case(When(sex='1', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111,
                                                                             107], then=1))),
                              vrojdenw=Sum(Case(When(sex='2', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111,
                                                                             107], then=1))),
                              drugiem=Sum(Case(When(sex='1', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120,
                                                                            108], then=1))),
                              drugiew=Sum(Case(When(sex='2', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120,
                                                                            108], then=1))),
                              allm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))),
                              allw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))))

                total_pervichm = queryset.aggregate(total_pervichm=Sum('pervichm'))['total_pervichm'] or 0
                total_pervichw = queryset.aggregate(total_pervichw=Sum('pervichw'))['total_pervichw'] or 0
                total_vtorichm = queryset.aggregate(total_vtorichm=Sum('vtorichm'))['total_vtorichm'] or 0
                total_vtorichw = queryset.aggregate(total_vtorichw=Sum('vtorichw'))['total_vtorichw'] or 0
                total_ranniym = queryset.aggregate(total_ranniym=Sum('ranniym'))['total_ranniym'] or 0
                total_ranniyw = queryset.aggregate(total_ranniyw=Sum('ranniyw'))['total_ranniyw'] or 0
                total_pozdniym = queryset.aggregate(total_pozdniym=Sum('pozdniym'))['total_pozdniym'] or 0
                total_pozdniyw = queryset.aggregate(total_pozdniyw=Sum('pozdniyw'))['total_pozdniyw'] or 0
                total_vrojdenm = queryset.aggregate(total_vrojdenm=Sum('vrojdenm'))['total_vrojdenm'] or 0
                total_vrojdenw = queryset.aggregate(total_vrojdenw=Sum('vrojdenw'))['total_vrojdenw'] or 0
                total_drugiem = queryset.aggregate(total_drugiem=Sum('drugiem'))['total_drugiem'] or 0
                total_drugiew = queryset.aggregate(total_drugiew=Sum('drugiew'))['total_drugiew'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0

                queryset = list(queryset) + [{'district__title': 'Итого', 'pervichm': total_pervichm,
                                              'pervichw': total_pervichw, 'vtorichm': total_vtorichm,
                                              'vtorichw': total_vtorichw, 'ranniym': total_ranniym,
                                              'ranniyw': total_ranniyw, 'pozdniym': total_pozdniym,
                                              'pozdniyw': total_pozdniyw, 'vrojdenm': total_vrojdenm,
                                              'vrojdenw': total_vrojdenw, 'drugiem': total_drugiem,
                                              'drugiew': total_drugiew, 'allm': total_allm, 'allw': total_allw}]
        if home == "ЗППП по районам (Сифилис - полный)":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(A510m=Sum(Case(When(sex='1', diagnosis=70, then=1))),
                              A510w=Sum(Case(When(sex='2', diagnosis=70, then=1))),
                              A511m=Sum(Case(When(sex='1', diagnosis=109, then=1))),
                              A511w=Sum(Case(When(sex='2', diagnosis=109, then=1))),
                              A512m=Sum(Case(When(sex='1', diagnosis=110, then=1))),
                              A512w=Sum(Case(When(sex='2', diagnosis=110, then=1))),
                              A513m=Sum(Case(When(sex='1', diagnosis=68, then=1))),
                              A513w=Sum(Case(When(sex='2', diagnosis=68, then=1))),
                              A514m=Sum(Case(When(sex='1', diagnosis=96, then=1))),
                              A514w=Sum(Case(When(sex='2', diagnosis=96, then=1))),
                              A515m=Sum(Case(When(sex='1', diagnosis=69, then=1))),
                              A515w=Sum(Case(When(sex='2', diagnosis=69, then=1))),
                              A528m=Sum(Case(When(sex='1', diagnosis=114, then=1))),
                              A528w=Sum(Case(When(sex='2', diagnosis=114, then=1))),
                              A500m=Sum(Case(When(sex='1', diagnosis=116, then=1))),
                              A500w=Sum(Case(When(sex='2', diagnosis=116, then=1))),
                              A501m=Sum(Case(When(sex='1', diagnosis=117, then=1))),
                              A501w=Sum(Case(When(sex='2', diagnosis=117, then=1))),
                              A502m=Sum(Case(When(sex='1', diagnosis=115, then=1))),
                              A502w=Sum(Case(When(sex='2', diagnosis=115, then=1))),
                              A503m=Sum(Case(When(sex='1', diagnosis=105, then=1))),
                              A503w=Sum(Case(When(sex='2', diagnosis=105, then=1))),
                              A504m=Sum(Case(When(sex='1', diagnosis=106, then=1))),
                              A504w=Sum(Case(When(sex='2', diagnosis=106, then=1))),
                              A505m=Sum(Case(When(sex='1', diagnosis=97, then=1))),
                              A505w=Sum(Case(When(sex='2', diagnosis=97, then=1))),
                              A506m=Sum(Case(When(sex='1', diagnosis=112, then=1))),
                              A506w=Sum(Case(When(sex='2', diagnosis=112, then=1))),
                              A507m=Sum(Case(When(sex='1', diagnosis=111, then=1))),
                              A507w=Sum(Case(When(sex='2', diagnosis=111, then=1))),
                              A509m=Sum(Case(When(sex='1', diagnosis=107, then=1))),
                              A509w=Sum(Case(When(sex='2', diagnosis=107, then=1))),
                              A519m=Sum(Case(When(sex='1', diagnosis=118, then=1))),
                              A519w=Sum(Case(When(sex='2', diagnosis=118, then=1))),
                              A520m=Sum(Case(When(sex='1', diagnosis=119, then=1))),
                              A520w=Sum(Case(When(sex='2', diagnosis=119, then=1))),
                              A521m=Sum(Case(When(sex='1', diagnosis=104, then=1))),
                              A521w=Sum(Case(When(sex='2', diagnosis=104, then=1))),
                              A522m=Sum(Case(When(sex='1', diagnosis=102, then=1))),
                              A522w=Sum(Case(When(sex='2', diagnosis=102, then=1))),
                              A523m=Sum(Case(When(sex='1', diagnosis=103, then=1))),
                              A523w=Sum(Case(When(sex='2', diagnosis=103, then=1))),
                              A527m=Sum(Case(When(sex='1', diagnosis=95, then=1))),
                              A527w=Sum(Case(When(sex='2', diagnosis=95, then=1))),
                              A529m=Sum(Case(When(sex='1', diagnosis=113, then=1))),
                              A529w=Sum(Case(When(sex='2', diagnosis=113, then=1))),
                              A530m=Sum(Case(When(sex='1', diagnosis=120, then=1))),
                              A530w=Sum(Case(When(sex='2', diagnosis=120, then=1))),
                              A539m=Sum(Case(When(sex='1', diagnosis=108, then=1))),
                              A539w=Sum(Case(When(sex='2', diagnosis=108, then=1))),
                              allm=Sum(
                                  Case(When(sex='1', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                    106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                    95, 113, 120, 108], then=1))),
                              allw=Sum(
                                  Case(When(sex='2', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                    106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                    95, 113, 120, 108], then=1))))

                total_A510m = queryset.aggregate(total_A510m=Sum('A510m'))['total_A510m'] or 0
                total_A510w = queryset.aggregate(total_A510w=Sum('A510w'))['total_A510w'] or 0
                total_A511m = queryset.aggregate(total_A511m=Sum('A511m'))['total_A511m'] or 0
                total_A511w = queryset.aggregate(total_A511w=Sum('A511w'))['total_A511w'] or 0
                total_A512m = queryset.aggregate(total_A512m=Sum('A512m'))['total_A512m'] or 0
                total_A512w = queryset.aggregate(total_A512w=Sum('A512w'))['total_A512w'] or 0
                total_A513m = queryset.aggregate(total_A513m=Sum('A513m'))['total_A513m'] or 0
                total_A513w = queryset.aggregate(total_A513w=Sum('A513w'))['total_A513w'] or 0
                total_A514m = queryset.aggregate(total_A514m=Sum('A514m'))['total_A514m'] or 0
                total_A514w = queryset.aggregate(total_A514w=Sum('A514w'))['total_A514w'] or 0
                total_A515m = queryset.aggregate(total_A515m=Sum('A515m'))['total_A515m'] or 0
                total_A515w = queryset.aggregate(total_A515w=Sum('A515w'))['total_A515w'] or 0
                total_A528m = queryset.aggregate(total_A528m=Sum('A528m'))['total_A528m'] or 0
                total_A528w = queryset.aggregate(total_A528w=Sum('A528w'))['total_A528w'] or 0
                total_A500m = queryset.aggregate(total_A500m=Sum('A500m'))['total_A500m'] or 0
                total_A500w = queryset.aggregate(total_A500w=Sum('A500w'))['total_A500w'] or 0
                total_A501m = queryset.aggregate(total_A501m=Sum('A501m'))['total_A501m'] or 0
                total_A501w = queryset.aggregate(total_A501w=Sum('A501w'))['total_A501w'] or 0
                total_A502m = queryset.aggregate(total_A512m=Sum('A502m'))['total_A512m'] or 0
                total_A502w = queryset.aggregate(total_A502w=Sum('A502w'))['total_A502w'] or 0
                total_A503m = queryset.aggregate(total_A503m=Sum('A503m'))['total_A503m'] or 0
                total_A503w = queryset.aggregate(total_A503w=Sum('A503w'))['total_A503w'] or 0
                total_A504m = queryset.aggregate(total_A504m=Sum('A504m'))['total_A504m'] or 0
                total_A504w = queryset.aggregate(total_A504w=Sum('A504w'))['total_A504w'] or 0
                total_A505m = queryset.aggregate(total_A505m=Sum('A505m'))['total_A505m'] or 0
                total_A505w = queryset.aggregate(total_A505w=Sum('A505w'))['total_A505w'] or 0
                total_A506m = queryset.aggregate(total_A506m=Sum('A506m'))['total_A506m'] or 0
                total_A506w = queryset.aggregate(total_A506w=Sum('A506w'))['total_A506w'] or 0
                total_A507m = queryset.aggregate(total_A507m=Sum('A507m'))['total_A507m'] or 0
                total_A507w = queryset.aggregate(total_A507w=Sum('A507w'))['total_A507w'] or 0
                total_A509m = queryset.aggregate(total_A509m=Sum('A509m'))['total_A509m'] or 0
                total_A509w = queryset.aggregate(total_A509w=Sum('A509w'))['total_A509w'] or 0
                total_A519m = queryset.aggregate(total_A519m=Sum('A519m'))['total_A519m'] or 0
                total_A519w = queryset.aggregate(total_A519w=Sum('A519w'))['total_A519w'] or 0
                total_A520m = queryset.aggregate(total_A520m=Sum('A520m'))['total_A520m'] or 0
                total_A520w = queryset.aggregate(total_A520w=Sum('A520w'))['total_A520w'] or 0
                total_A521m = queryset.aggregate(total_A521m=Sum('A521m'))['total_A521m'] or 0
                total_A521w = queryset.aggregate(total_A521w=Sum('A521w'))['total_A521w'] or 0
                total_A522m = queryset.aggregate(total_A522m=Sum('A522m'))['total_A522m'] or 0
                total_A522w = queryset.aggregate(total_A522w=Sum('A522w'))['total_A522w'] or 0
                total_A523m = queryset.aggregate(total_A523m=Sum('A523m'))['total_A523m'] or 0
                total_A523w = queryset.aggregate(total_A523w=Sum('A523w'))['total_A523w'] or 0
                total_A527m = queryset.aggregate(total_A527m=Sum('A527m'))['total_A527m'] or 0
                total_A527w = queryset.aggregate(total_A527w=Sum('A527w'))['total_A527w'] or 0
                total_A529m = queryset.aggregate(total_A529m=Sum('A529m'))['total_A529m'] or 0
                total_A529w = queryset.aggregate(total_A529w=Sum('A529w'))['total_A529w'] or 0
                total_A530m = queryset.aggregate(total_A530m=Sum('A530m'))['total_A530m'] or 0
                total_A530w = queryset.aggregate(total_A530w=Sum('A530w'))['total_A530w'] or 0
                total_A539m = queryset.aggregate(total_A539m=Sum('A539m'))['total_A539m'] or 0
                total_A539w = queryset.aggregate(total_A539w=Sum('A539w'))['total_A539w'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'A510m': total_A510m, 'A510w': total_A510w, 'A511m': total_A511m,
                     'A511w': total_A511w, 'A512m': total_A512m, 'A512w': total_A512w, 'A513m': total_A513m,
                     'A513w': total_A513w, 'A514m': total_A514m, 'A514w': total_A514w, 'A515m': total_A515m,
                     'A515w': total_A515w, 'A528m': total_A528m, 'A528w': total_A528w, 'A500m': total_A500m,
                     'A500w': total_A500w, 'A501m': total_A501m, 'A501w': total_A501w, 'A502m': total_A502m,
                     'A502w': total_A502w, 'A503m': total_A503m, 'A503w': total_A503w, 'A504m': total_A504m,
                     'A504w': total_A504w, 'A505m': total_A505m, 'A505w': total_A505w, 'A506m': total_A506m,
                     'A506w': total_A506w, 'A507m': total_A507m, 'A507w': total_A507w, 'A509m': total_A509m,
                     'A509w': total_A509w, 'A519m': total_A519m, 'A519w': total_A519w, 'A520m': total_A520m,
                     'A520w': total_A520w, 'A521m': total_A521m, 'A521w': total_A521w, 'A522m': total_A522m,
                     'A522w': total_A522w, 'A523m': total_A523m, 'A523w': total_A523w, 'A527m': total_A527m,
                     'A527w': total_A527w, 'A529m': total_A529m, 'A529w': total_A529w, 'A530m': total_A530m,
                     'A530w': total_A530w, 'A539m': total_A539m, 'A539w': total_A539w, 'allm': total_allm,
                     'allw': total_allw}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(A510m=Sum(Case(When(sex='1', diagnosis=70, then=1))),
                              A510w=Sum(Case(When(sex='2', diagnosis=70, then=1))),
                              A511m=Sum(Case(When(sex='1', diagnosis=109, then=1))),
                              A511w=Sum(Case(When(sex='2', diagnosis=109, then=1))),
                              A512m=Sum(Case(When(sex='1', diagnosis=110, then=1))),
                              A512w=Sum(Case(When(sex='2', diagnosis=110, then=1))),
                              A513m=Sum(Case(When(sex='1', diagnosis=68, then=1))),
                              A513w=Sum(Case(When(sex='2', diagnosis=68, then=1))),
                              A514m=Sum(Case(When(sex='1', diagnosis=96, then=1))),
                              A514w=Sum(Case(When(sex='2', diagnosis=96, then=1))),
                              A515m=Sum(Case(When(sex='1', diagnosis=69, then=1))),
                              A515w=Sum(Case(When(sex='2', diagnosis=69, then=1))),
                              A528m=Sum(Case(When(sex='1', diagnosis=114, then=1))),
                              A528w=Sum(Case(When(sex='2', diagnosis=114, then=1))),
                              A500m=Sum(Case(When(sex='1', diagnosis=116, then=1))),
                              A500w=Sum(Case(When(sex='2', diagnosis=116, then=1))),
                              A501m=Sum(Case(When(sex='1', diagnosis=117, then=1))),
                              A501w=Sum(Case(When(sex='2', diagnosis=117, then=1))),
                              A502m=Sum(Case(When(sex='1', diagnosis=115, then=1))),
                              A502w=Sum(Case(When(sex='2', diagnosis=115, then=1))),
                              A503m=Sum(Case(When(sex='1', diagnosis=105, then=1))),
                              A503w=Sum(Case(When(sex='2', diagnosis=105, then=1))),
                              A504m=Sum(Case(When(sex='1', diagnosis=106, then=1))),
                              A504w=Sum(Case(When(sex='2', diagnosis=106, then=1))),
                              A505m=Sum(Case(When(sex='1', diagnosis=97, then=1))),
                              A505w=Sum(Case(When(sex='2', diagnosis=97, then=1))),
                              A506m=Sum(Case(When(sex='1', diagnosis=112, then=1))),
                              A506w=Sum(Case(When(sex='2', diagnosis=112, then=1))),
                              A507m=Sum(Case(When(sex='1', diagnosis=111, then=1))),
                              A507w=Sum(Case(When(sex='2', diagnosis=111, then=1))),
                              A509m=Sum(Case(When(sex='1', diagnosis=107, then=1))),
                              A509w=Sum(Case(When(sex='2', diagnosis=107, then=1))),
                              A519m=Sum(Case(When(sex='1', diagnosis=118, then=1))),
                              A519w=Sum(Case(When(sex='2', diagnosis=118, then=1))),
                              A520m=Sum(Case(When(sex='1', diagnosis=119, then=1))),
                              A520w=Sum(Case(When(sex='2', diagnosis=119, then=1))),
                              A521m=Sum(Case(When(sex='1', diagnosis=104, then=1))),
                              A521w=Sum(Case(When(sex='2', diagnosis=104, then=1))),
                              A522m=Sum(Case(When(sex='1', diagnosis=102, then=1))),
                              A522w=Sum(Case(When(sex='2', diagnosis=102, then=1))),
                              A523m=Sum(Case(When(sex='1', diagnosis=103, then=1))),
                              A523w=Sum(Case(When(sex='2', diagnosis=103, then=1))),
                              A527m=Sum(Case(When(sex='1', diagnosis=95, then=1))),
                              A527w=Sum(Case(When(sex='2', diagnosis=95, then=1))),
                              A529m=Sum(Case(When(sex='1', diagnosis=113, then=1))),
                              A529w=Sum(Case(When(sex='2', diagnosis=113, then=1))),
                              A530m=Sum(Case(When(sex='1', diagnosis=120, then=1))),
                              A530w=Sum(Case(When(sex='2', diagnosis=120, then=1))),
                              A539m=Sum(Case(When(sex='1', diagnosis=108, then=1))),
                              A539w=Sum(Case(When(sex='2', diagnosis=108, then=1))),
                              allm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))),
                              allw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))))

                total_A510m = queryset.aggregate(total_A510m=Sum('A510m'))['total_A510m'] or 0
                total_A510w = queryset.aggregate(total_A510w=Sum('A510w'))['total_A510w'] or 0
                total_A511m = queryset.aggregate(total_A511m=Sum('A511m'))['total_A511m'] or 0
                total_A511w = queryset.aggregate(total_A511w=Sum('A511w'))['total_A511w'] or 0
                total_A512m = queryset.aggregate(total_A512m=Sum('A512m'))['total_A512m'] or 0
                total_A512w = queryset.aggregate(total_A512w=Sum('A512w'))['total_A512w'] or 0
                total_A513m = queryset.aggregate(total_A513m=Sum('A513m'))['total_A513m'] or 0
                total_A513w = queryset.aggregate(total_A513w=Sum('A513w'))['total_A513w'] or 0
                total_A514m = queryset.aggregate(total_A514m=Sum('A514m'))['total_A514m'] or 0
                total_A514w = queryset.aggregate(total_A514w=Sum('A514w'))['total_A514w'] or 0
                total_A515m = queryset.aggregate(total_A515m=Sum('A515m'))['total_A515m'] or 0
                total_A515w = queryset.aggregate(total_A515w=Sum('A515w'))['total_A515w'] or 0
                total_A528m = queryset.aggregate(total_A528m=Sum('A528m'))['total_A528m'] or 0
                total_A528w = queryset.aggregate(total_A528w=Sum('A528w'))['total_A528w'] or 0
                total_A500m = queryset.aggregate(total_A500m=Sum('A500m'))['total_A500m'] or 0
                total_A500w = queryset.aggregate(total_A500w=Sum('A500w'))['total_A500w'] or 0
                total_A501m = queryset.aggregate(total_A501m=Sum('A501m'))['total_A501m'] or 0
                total_A501w = queryset.aggregate(total_A501w=Sum('A501w'))['total_A501w'] or 0
                total_A502m = queryset.aggregate(total_A512m=Sum('A502m'))['total_A512m'] or 0
                total_A502w = queryset.aggregate(total_A502w=Sum('A502w'))['total_A502w'] or 0
                total_A503m = queryset.aggregate(total_A503m=Sum('A503m'))['total_A503m'] or 0
                total_A503w = queryset.aggregate(total_A503w=Sum('A503w'))['total_A503w'] or 0
                total_A504m = queryset.aggregate(total_A504m=Sum('A504m'))['total_A504m'] or 0
                total_A504w = queryset.aggregate(total_A504w=Sum('A504w'))['total_A504w'] or 0
                total_A505m = queryset.aggregate(total_A505m=Sum('A505m'))['total_A505m'] or 0
                total_A505w = queryset.aggregate(total_A505w=Sum('A505w'))['total_A505w'] or 0
                total_A506m = queryset.aggregate(total_A506m=Sum('A506m'))['total_A506m'] or 0
                total_A506w = queryset.aggregate(total_A506w=Sum('A506w'))['total_A506w'] or 0
                total_A507m = queryset.aggregate(total_A507m=Sum('A507m'))['total_A507m'] or 0
                total_A507w = queryset.aggregate(total_A507w=Sum('A507w'))['total_A507w'] or 0
                total_A509m = queryset.aggregate(total_A509m=Sum('A509m'))['total_A509m'] or 0
                total_A509w = queryset.aggregate(total_A509w=Sum('A509w'))['total_A509w'] or 0
                total_A519m = queryset.aggregate(total_A519m=Sum('A519m'))['total_A519m'] or 0
                total_A519w = queryset.aggregate(total_A519w=Sum('A519w'))['total_A519w'] or 0
                total_A520m = queryset.aggregate(total_A520m=Sum('A520m'))['total_A520m'] or 0
                total_A520w = queryset.aggregate(total_A520w=Sum('A520w'))['total_A520w'] or 0
                total_A521m = queryset.aggregate(total_A521m=Sum('A521m'))['total_A521m'] or 0
                total_A521w = queryset.aggregate(total_A521w=Sum('A521w'))['total_A521w'] or 0
                total_A522m = queryset.aggregate(total_A522m=Sum('A522m'))['total_A522m'] or 0
                total_A522w = queryset.aggregate(total_A522w=Sum('A522w'))['total_A522w'] or 0
                total_A523m = queryset.aggregate(total_A523m=Sum('A523m'))['total_A523m'] or 0
                total_A523w = queryset.aggregate(total_A523w=Sum('A523w'))['total_A523w'] or 0
                total_A527m = queryset.aggregate(total_A527m=Sum('A527m'))['total_A527m'] or 0
                total_A527w = queryset.aggregate(total_A527w=Sum('A527w'))['total_A527w'] or 0
                total_A529m = queryset.aggregate(total_A529m=Sum('A529m'))['total_A529m'] or 0
                total_A529w = queryset.aggregate(total_A529w=Sum('A529w'))['total_A529w'] or 0
                total_A530m = queryset.aggregate(total_A530m=Sum('A530m'))['total_A530m'] or 0
                total_A530w = queryset.aggregate(total_A530w=Sum('A530w'))['total_A530w'] or 0
                total_A539m = queryset.aggregate(total_A539m=Sum('A539m'))['total_A539m'] or 0
                total_A539w = queryset.aggregate(total_A539w=Sum('A539w'))['total_A539w'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'A510m': total_A510m, 'A510w': total_A510w, 'A511m': total_A511m,
                     'A511w': total_A511w, 'A512m': total_A512m, 'A512w': total_A512w, 'A513m': total_A513m,
                     'A513w': total_A513w, 'A514m': total_A514m, 'A514w': total_A514w, 'A515m': total_A515m,
                     'A515w': total_A515w, 'A528m': total_A528m, 'A528w': total_A528w, 'A500m': total_A500m,
                     'A500w': total_A500w, 'A501m': total_A501m, 'A501w': total_A501w, 'A502m': total_A502m,
                     'A502w': total_A502w, 'A503m': total_A503m, 'A503w': total_A503w, 'A504m': total_A504m,
                     'A504w': total_A504w, 'A505m': total_A505m, 'A505w': total_A505w, 'A506m': total_A506m,
                     'A506w': total_A506w, 'A507m': total_A507m, 'A507w': total_A507w, 'A509m': total_A509m,
                     'A509w': total_A509w, 'A519m': total_A519m, 'A519w': total_A519w, 'A520m': total_A520m,
                     'A520w': total_A520w, 'A521m': total_A521m, 'A521w': total_A521w, 'A522m': total_A522m,
                     'A522w': total_A522w, 'A523m': total_A523m, 'A523w': total_A523w, 'A527m': total_A527m,
                     'A527w': total_A527w, 'A529m': total_A529m, 'A529w': total_A529w, 'A530m': total_A530m,
                     'A530w': total_A530w, 'A539m': total_A539m, 'A539w': total_A539w, 'allm': total_allm,
                     'allw': total_allw}]
        if home == "ЗППП по районам (Ост. заболевания)":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(gonoreyallm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=3, then=1))),
                              gonoreyallw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=3, then=1))),
                              A541m=Sum(Case(When(sex='1', diagnosis=73, then=1))),
                              A541w=Sum(Case(When(sex='2', diagnosis=73, then=1))),
                              gonoreykids=Sum(Case(When(diagnosis__group_of_diagnoses__id=3,
                                                        date_bith__year__gt=(int(year) - 15), then=1))),
                              trichom=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=4, then=1))),
                              trichow=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=4, then=1))),
                              hlamidm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=5, then=1))),
                              hlamidw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=5, then=1))),
                              gerpesm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=6, then=1))),
                              gerpesw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=6, then=1))),
                              borodavkim=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=7, then=1))),
                              borodavkiw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=7, then=1))))

                total_gonoreyallm = queryset.aggregate(total_gonoreyallm=Sum('gonoreyallm'))['total_gonoreyallm'] or 0
                total_gonoreyallw = queryset.aggregate(total_gonoreyallw=Sum('gonoreyallw'))['total_gonoreyallw'] or 0
                total_A541m = queryset.aggregate(total_A541m=Sum('A541m'))['total_A541m'] or 0
                total_A541w = queryset.aggregate(total_A541w=Sum('A541w'))['total_A541w'] or 0
                total_gonoreykids = queryset.aggregate(total_gonoreykids=Sum('gonoreykids'))['total_gonoreykids'] or 0
                total_trichom = queryset.aggregate(total_trichom=Sum('trichom'))['total_trichom'] or 0
                total_trichow = queryset.aggregate(total_trichow=Sum('trichow'))['total_trichow'] or 0
                total_hlamidm = queryset.aggregate(total_hlamidm=Sum('hlamidm'))['total_hlamidm'] or 0
                total_hlamidw = queryset.aggregate(total_hlamidw=Sum('hlamidw'))['total_hlamidw'] or 0
                total_gerpesm = queryset.aggregate(total_gerpesm=Sum('gerpesm'))['total_gerpesm'] or 0
                total_gerpesw = queryset.aggregate(total_gerpesw=Sum('gerpesw'))['total_gerpesw'] or 0
                total_borodavkim = queryset.aggregate(total_borodavkim=Sum('borodavkim'))['total_borodavkim'] or 0
                total_borodavkiw = queryset.aggregate(total_borodavkiw=Sum('borodavkiw'))['total_borodavkiw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'gonoreyallm': total_gonoreyallm, 'gonoreyallw': total_gonoreyallw,
                     'A541m': total_A541m, 'A541w': total_A541w, 'gonoreykids': total_gonoreykids,
                     'trichom': total_trichom, 'trichow': total_trichow,'hlamidm': total_hlamidm,
                     'hlamidw': total_hlamidw, 'gerpesm': total_gerpesm, 'gerpesw': total_gerpesw,
                     'borodavkim': total_borodavkim, 'borodavkiw': total_borodavkiw}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(gonoreyallm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=3, then=1))),
                              gonoreyallw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=3, then=1))),
                              A541m=Sum(Case(When(sex='1', diagnosis=73, then=1))),
                              A541w=Sum(Case(When(sex='2', diagnosis=73, then=1))),
                              gonoreykids=Sum(Case(When(diagnosis__group_of_diagnoses__id=3,
                                                        date_bith__year__gt=(int(year) - 15), then=1))),
                              trichom=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=4, then=1))),
                              trichow=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=4, then=1))),
                              hlamidm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=5, then=1))),
                              hlamidw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=5, then=1))),
                              gerpesm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=6, then=1))),
                              gerpesw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=6, then=1))),
                              borodavkim=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=7, then=1))),
                              borodavkiw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=7, then=1))))

                total_gonoreyallm = queryset.aggregate(total_gonoreyallm=Sum('gonoreyallm'))['total_gonoreyallm'] or 0
                total_gonoreyallw = queryset.aggregate(total_gonoreyallw=Sum('gonoreyallw'))['total_gonoreyallw'] or 0
                total_A541m = queryset.aggregate(total_A541m=Sum('A541m'))['total_A541m'] or 0
                total_A541w = queryset.aggregate(total_A541w=Sum('A541w'))['total_A541w'] or 0
                total_gonoreykids = queryset.aggregate(total_gonoreykids=Sum('gonoreykids'))['total_gonoreykids'] or 0
                total_trichom = queryset.aggregate(total_trichom=Sum('trichom'))['total_trichom'] or 0
                total_trichow = queryset.aggregate(total_trichow=Sum('trichow'))['total_trichow'] or 0
                total_hlamidm = queryset.aggregate(total_hlamidm=Sum('hlamidm'))['total_hlamidm'] or 0
                total_hlamidw = queryset.aggregate(total_hlamidw=Sum('hlamidw'))['total_hlamidw'] or 0
                total_gerpesm = queryset.aggregate(total_gerpesm=Sum('gerpesm'))['total_gerpesm'] or 0
                total_gerpesw = queryset.aggregate(total_gerpesw=Sum('gerpesw'))['total_gerpesw'] or 0
                total_borodavkim = queryset.aggregate(total_borodavkim=Sum('borodavkim'))['total_borodavkim'] or 0
                total_borodavkiw = queryset.aggregate(total_borodavkiw=Sum('borodavkiw'))['total_borodavkiw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'gonoreyallm': total_gonoreyallm, 'gonoreyallw': total_gonoreyallw,
                     'A541m': total_A541m, 'A541w': total_A541w, 'gonoreykids': total_gonoreykids,
                     'trichom': total_trichom, 'trichow': total_trichow,'hlamidm': total_hlamidm,
                     'hlamidw': total_hlamidw, 'gerpesm': total_gerpesm, 'gerpesw': total_gerpesw,
                     'borodavkim': total_borodavkim, 'borodavkiw': total_borodavkiw}]
        if home == "ЗППП Форма 9 (Таблица 2000)":
            if registered == "Все зарегистрированные":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40,
                         'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
            elif registered == "Саратов":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            citizen__title=citizen)\
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=432) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=433) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
            elif registered == "Саратовская область":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            citizen__title=citizen) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        mesto_obracheniya_id=432) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        mesto_obracheniya_id=433) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
            else:
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=432, citizen__titel=citizen,
                                                            district__title=district_id) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=433, citizen__title=citizen,
                                                            district__title=district_id) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen, district__title=district_id) \
                            .values('diagnosis__title').order_by('diagnosis__title') \
                            .annotate(all=Count('diagnosis__title'),
                                      allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                      allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                           date_bith__year__gt=(int(year)-15), then=1))),
                                      allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                           date_bith__year__gt=(int(year) - 18), then=1))),
                                      allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                           date_bith__year__gt=(int(year) - 30), then=1))),
                                      allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                           date_bith__year__gt=(int(year) - 40), then=1))),
                                      allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                      allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                        total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                        total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                        total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                        total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                        total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                        total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                        total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                        total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                        total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                        total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                        total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                        total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                        queryset = list(queryset) + [
                            {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                             'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                             'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                             'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432,
                                                        district__title=district_id) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433,
                                                        district__title=district_id) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .values('diagnosis__title').order_by('diagnosis__title') \
                        .annotate(all=Count('diagnosis__title'),
                                  allm=Sum(Case(When(sex='1', then=1))), allw=Sum(Case(When(sex='2', then=1))),
                                  allm1=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allw1=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 2), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-1),
                                                       date_bith__year__gt=(int(year)-15), then=1))),
                                  allm17=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allw17=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                       date_bith__year__gt=(int(year) - 18), then=1))),
                                  allm29=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allw29=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 17),
                                                       date_bith__year__gt=(int(year) - 30), then=1))),
                                  allm39=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allw39=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 29),
                                                       date_bith__year__gt=(int(year) - 40), then=1))),
                                  allm40=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 39), then=1))),
                                  allw40=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 39), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_allm1 = queryset.aggregate(total_allm1=Sum('allm1'))['total_allm1'] or 0
                    total_allw1 = queryset.aggregate(total_allw1=Sum('allw1'))['total_allw1'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_allm17 = queryset.aggregate(total_allm17=Sum('allm17'))['total_allm17'] or 0
                    total_allw17 = queryset.aggregate(total_allw17=Sum('allw17'))['total_allw17'] or 0
                    total_allm29 = queryset.aggregate(total_allm29=Sum('allm29'))['total_allm29'] or 0
                    total_allw29 = queryset.aggregate(total_allw29=Sum('allw29'))['total_allw29'] or 0
                    total_allm39 = queryset.aggregate(total_allm39=Sum('allm39'))['total_allm39'] or 0
                    total_allw39 = queryset.aggregate(total_allw39=Sum('allw39'))['total_allw39'] or 0
                    total_allm40 = queryset.aggregate(total_allm40=Sum('allm40'))['total_allm40'] or 0
                    total_allw40 = queryset.aggregate(total_allw40=Sum('allw40'))['total_allw40'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'allm1': total_allm1, 'allw1': total_allw1, 'allm14': total_allm14, 'allw14': total_allw14,
                         'allm17': total_allm17, 'allw17': total_allw17, 'allm29': total_allm29, 'allw29': total_allw29,
                         'allm39': total_allm39, 'allw39': total_allw39, 'allm40': total_allm40, 'allw40': total_allw40}]
        if home == "Районный срез заболеваемости":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(sifil=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                              gonor=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                              triho=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                              hlami=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                              mikro=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                              cheso=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))))

                total_sifil = queryset.aggregate(total_sifil=Sum('sifil'))['total_sifil'] or 0
                total_gonor = queryset.aggregate(total_gonor=Sum('gonor'))['total_gonor'] or 0
                total_triho = queryset.aggregate(total_triho=Sum('triho'))['total_triho'] or 0
                total_hlami = queryset.aggregate(total_hlami=Sum('hlami'))['total_hlami'] or 0
                total_mikro = queryset.aggregate(total_mikro=Sum('mikro'))['total_mikro'] or 0
                total_cheso = queryset.aggregate(total_cheso=Sum('cheso'))['total_cheso'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'sifil': total_sifil, 'gonor': total_gonor, 'triho': total_triho,
                     'hlami': total_hlami, 'mikro': total_mikro, 'cheso': total_cheso}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(sifil=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                              gonor=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                              triho=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                              hlami=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                              mikro=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                              cheso=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))))

                total_sifil = queryset.aggregate(total_sifil=Sum('sifil'))['total_sifil'] or 0
                total_gonor = queryset.aggregate(total_gonor=Sum('gonor'))['total_gonor'] or 0
                total_triho = queryset.aggregate(total_triho=Sum('triho'))['total_triho'] or 0
                total_hlami = queryset.aggregate(total_hlami=Sum('hlami'))['total_hlami'] or 0
                total_mikro = queryset.aggregate(total_mikro=Sum('mikro'))['total_mikro'] or 0
                total_cheso = queryset.aggregate(total_cheso=Sum('cheso'))['total_cheso'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'sifil': total_sifil, 'gonor': total_gonor, 'triho': total_triho,
                     'hlami': total_hlami, 'mikro': total_mikro, 'cheso': total_cheso}]
        if home == "Районный срез заболеваемости (Сифилис)":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(pervichm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110], then=1))),
                              pervichw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110], then=1))),
                              vtorichm=Sum(Case(When(sex='1', diagnosis__in=[68, 96], then=1))),
                              vtorichw=Sum(Case(When(sex='2', diagnosis__in=[68, 96], then=1))),
                              ranniym=Sum(Case(When(sex='1', diagnosis=69, then=1))),
                              ranniyw=Sum(Case(When(sex='2', diagnosis=69, then=1))),
                              pozdniym=Sum(Case(When(sex='1', diagnosis=114, then=1))),
                              pozdniyw=Sum(Case(When(sex='2', diagnosis=114, then=1))),
                              vrojdenm=Sum(Case(When(sex='1', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111, 107],
                                                     then=1))),
                              vrojdenw=Sum(Case(When(sex='2', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111, 107],
                                                     then=1))),
                              drugiem=Sum(Case(When(sex='1', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120, 108],
                                                    then=1))),
                              drugiew=Sum(Case(When(sex='2', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120, 108],
                                                    then=1))),
                              allm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))),
                              allw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))))

                total_pervichm = queryset.aggregate(total_pervichm=Sum('pervichm'))['total_pervichm'] or 0
                total_pervichw = queryset.aggregate(total_pervichw=Sum('pervichw'))['total_pervichw'] or 0
                total_vtorichm = queryset.aggregate(total_vtorichm=Sum('vtorichm'))['total_vtorichm'] or 0
                total_vtorichw = queryset.aggregate(total_vtorichw=Sum('vtorichw'))['total_vtorichw'] or 0
                total_ranniym = queryset.aggregate(total_ranniym=Sum('ranniym'))['total_ranniym'] or 0
                total_ranniyw = queryset.aggregate(total_ranniyw=Sum('ranniyw'))['total_ranniyw'] or 0
                total_pozdniym = queryset.aggregate(total_pozdniym=Sum('pozdniym'))['total_pozdniym'] or 0
                total_pozdniyw = queryset.aggregate(total_pozdniyw=Sum('pozdniyw'))['total_pozdniyw'] or 0
                total_vrojdenm = queryset.aggregate(total_vrojdenm=Sum('vrojdenm'))['total_vrojdenm'] or 0
                total_vrojdenw = queryset.aggregate(total_vrojdenw=Sum('vrojdenw'))['total_vrojdenw'] or 0
                total_drugiem = queryset.aggregate(total_drugiem=Sum('drugiem'))['total_drugiem'] or 0
                total_drugiew = queryset.aggregate(total_drugiew=Sum('drugiew'))['total_drugiew'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'pervichm': total_pervichm, 'pervichw': total_pervichw,
                     'vtorichm': total_vtorichm, 'vtorichw': total_vtorichw, 'ranniym': total_ranniym,
                     'ranniyw': total_ranniyw, 'pozdniym': total_pozdniym, 'pozdniyw': total_pozdniyw,
                     'vrojdenm': total_vrojdenm, 'vrojdenw': total_vrojdenw, 'drugiem': total_drugiem,
                     'drugiew': total_drugiew, 'allm': total_allm, 'allw': total_allw}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(pervichm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110], then=1))),
                              pervichw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110], then=1))),
                              vtorichm=Sum(Case(When(sex='1', diagnosis__in=[68, 96], then=1))),
                              vtorichw=Sum(Case(When(sex='2', diagnosis__in=[68, 96], then=1))),
                              ranniym=Sum(Case(When(sex='1', diagnosis=69, then=1))),
                              ranniyw=Sum(Case(When(sex='2', diagnosis=69, then=1))),
                              pozdniym=Sum(Case(When(sex='1', diagnosis=114, then=1))),
                              pozdniyw=Sum(Case(When(sex='2', diagnosis=114, then=1))),
                              vrojdenm=Sum(Case(When(sex='1', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111, 107],
                                                     then=1))),
                              vrojdenw=Sum(Case(When(sex='2', diagnosis__in=[116, 117, 115, 105, 106, 97, 112, 111, 107],
                                                     then=1))),
                              drugiem=Sum(Case(When(sex='1', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120, 108],
                                                    then=1))),
                              drugiew=Sum(Case(When(sex='2', diagnosis__in=[118, 119, 104, 102, 103, 95, 113, 120, 108],
                                                    then=1))),
                              allm=Sum(Case(When(sex='1', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))),
                              allw=Sum(Case(When(sex='2', diagnosis__in=[70, 109, 110, 68, 96, 69, 114, 116, 117, 115, 105,
                                                                         106, 97, 112, 111, 107, 118, 119, 104, 102, 103,
                                                                         95, 113, 120, 108], then=1))))

                total_pervichm = queryset.aggregate(total_pervichm=Sum('pervichm'))['total_pervichm'] or 0
                total_pervichw = queryset.aggregate(total_pervichw=Sum('pervichw'))['total_pervichw'] or 0
                total_vtorichm = queryset.aggregate(total_vtorichm=Sum('vtorichm'))['total_vtorichm'] or 0
                total_vtorichw = queryset.aggregate(total_vtorichw=Sum('vtorichw'))['total_vtorichw'] or 0
                total_ranniym = queryset.aggregate(total_ranniym=Sum('ranniym'))['total_ranniym'] or 0
                total_ranniyw = queryset.aggregate(total_ranniyw=Sum('ranniyw'))['total_ranniyw'] or 0
                total_pozdniym = queryset.aggregate(total_pozdniym=Sum('pozdniym'))['total_pozdniym'] or 0
                total_pozdniyw = queryset.aggregate(total_pozdniyw=Sum('pozdniyw'))['total_pozdniyw'] or 0
                total_vrojdenm = queryset.aggregate(total_vrojdenm=Sum('vrojdenm'))['total_vrojdenm'] or 0
                total_vrojdenw = queryset.aggregate(total_vrojdenw=Sum('vrojdenw'))['total_vrojdenw'] or 0
                total_drugiem = queryset.aggregate(total_drugiem=Sum('drugiem'))['total_drugiem'] or 0
                total_drugiew = queryset.aggregate(total_drugiew=Sum('drugiew'))['total_drugiew'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'pervichm': total_pervichm, 'pervichw': total_pervichw,
                     'vtorichm': total_vtorichm, 'vtorichw': total_vtorichw, 'ranniym': total_ranniym,
                     'ranniyw': total_ranniyw, 'pozdniym': total_pozdniym, 'pozdniyw': total_pozdniyw,
                     'vrojdenm': total_vrojdenm, 'vrojdenw': total_vrojdenw, 'drugiem': total_drugiem,
                     'drugiew': total_drugiew, 'allm': total_allm, 'allw': total_allw}]
        if home == "Районный срез заболеваемости (Ост. заболевания)":
            if citizen:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], citizen__title=citizen) \
                    .order_by('district__id').values('district__title') \
                    .annotate(gonoreyallm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=3, then=1))),
                              gonoreyallw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=3, then=1))),
                              A541m=Sum(Case(When(sex='1', diagnosis=73, then=1))),
                              A541w=Sum(Case(When(sex='2', diagnosis=73, then=1))),
                              gonoreykids=Sum(Case(When(diagnosis__group_of_diagnoses__id=3,
                                                        date_bith__year__gt=(int(year) - 15), then=1))),
                              trichom=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=4, then=1))),
                              trichow=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=4, then=1))),
                              hlamidm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=5, then=1))),
                              hlamidw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=5, then=1))),
                              gerpesm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=6, then=1))),
                              gerpesw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=6, then=1))),
                              borodavkim=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=7, then=1))),
                              borodavkiw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=7, then=1))))

                total_gonoreyallm = queryset.aggregate(total_gonoreyallm=Sum('gonoreyallm'))['total_gonoreyallm'] or 0
                total_gonoreyallw = queryset.aggregate(total_gonoreyallw=Sum('gonoreyallw'))['total_gonoreyallw'] or 0
                total_A541m = queryset.aggregate(total_A541m=Sum('A541m'))['total_A541m'] or 0
                total_A541w = queryset.aggregate(total_A541w=Sum('A541w'))['total_A541w'] or 0
                total_gonoreykids = queryset.aggregate(total_gonoreykids=Sum('gonoreykids'))['total_gonoreykids'] or 0
                total_trichom = queryset.aggregate(total_trichom=Sum('trichom'))['total_trichom'] or 0
                total_trichow = queryset.aggregate(total_trichow=Sum('trichow'))['total_trichow'] or 0
                total_hlamidm = queryset.aggregate(total_hlamidm=Sum('hlamidm'))['total_hlamidm'] or 0
                total_hlamidw = queryset.aggregate(total_hlamidw=Sum('hlamidw'))['total_hlamidw'] or 0
                total_gerpesm = queryset.aggregate(total_gerpesm=Sum('gerpesm'))['total_gerpesm'] or 0
                total_gerpesw = queryset.aggregate(total_gerpesw=Sum('gerpesw'))['total_gerpesw'] or 0
                total_borodavkim = queryset.aggregate(total_borodavkim=Sum('borodavkim'))['total_borodavkim'] or 0
                total_borodavkiw = queryset.aggregate(total_borodavkiw=Sum('borodavkiw'))['total_borodavkiw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'gonoreyallm': total_gonoreyallm, 'gonoreyallw': total_gonoreyallw,
                     'A541m': total_A541m, 'A541w': total_A541w, 'gonoreykids': total_gonoreykids,
                     'trichom': total_trichom, 'trichow': total_trichow,'hlamidm': total_hlamidm,
                     'hlamidw': total_hlamidw, 'gerpesm': total_gerpesm, 'gerpesw': total_gerpesw,
                     'borodavkim': total_borodavkim, 'borodavkiw': total_borodavkiw}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(gonoreyallm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=3, then=1))),
                              gonoreyallw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=3, then=1))),
                              A541m=Sum(Case(When(sex='1', diagnosis=73, then=1))),
                              A541w=Sum(Case(When(sex='2', diagnosis=73, then=1))),
                              gonoreykids=Sum(Case(When(diagnosis__group_of_diagnoses__id=3,
                                                        date_bith__year__gt=(int(year) - 15), then=1))),
                              trichom=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=4, then=1))),
                              trichow=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=4, then=1))),
                              hlamidm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=5, then=1))),
                              hlamidw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=5, then=1))),
                              gerpesm=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=6, then=1))),
                              gerpesw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=6, then=1))),
                              borodavkim=Sum(Case(When(sex='1', diagnosis__group_of_diagnoses__id=7, then=1))),
                              borodavkiw=Sum(Case(When(sex='2', diagnosis__group_of_diagnoses__id=7, then=1))))

                total_gonoreyallm = queryset.aggregate(total_gonoreyallm=Sum('gonoreyallm'))['total_gonoreyallm'] or 0
                total_gonoreyallw = queryset.aggregate(total_gonoreyallw=Sum('gonoreyallw'))['total_gonoreyallw'] or 0
                total_A541m = queryset.aggregate(total_A541m=Sum('A541m'))['total_A541m'] or 0
                total_A541w = queryset.aggregate(total_A541w=Sum('A541w'))['total_A541w'] or 0
                total_gonoreykids = queryset.aggregate(total_gonoreykids=Sum('gonoreykids'))['total_gonoreykids'] or 0
                total_trichom = queryset.aggregate(total_trichom=Sum('trichom'))['total_trichom'] or 0
                total_trichow = queryset.aggregate(total_trichow=Sum('trichow'))['total_trichow'] or 0
                total_hlamidm = queryset.aggregate(total_hlamidm=Sum('hlamidm'))['total_hlamidm'] or 0
                total_hlamidw = queryset.aggregate(total_hlamidw=Sum('hlamidw'))['total_hlamidw'] or 0
                total_gerpesm = queryset.aggregate(total_gerpesm=Sum('gerpesm'))['total_gerpesm'] or 0
                total_gerpesw = queryset.aggregate(total_gerpesw=Sum('gerpesw'))['total_gerpesw'] or 0
                total_borodavkim = queryset.aggregate(total_borodavkim=Sum('borodavkim'))['total_borodavkim'] or 0
                total_borodavkiw = queryset.aggregate(total_borodavkiw=Sum('borodavkiw'))['total_borodavkiw'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'gonoreyallm': total_gonoreyallm, 'gonoreyallw': total_gonoreyallw,
                     'A541m': total_A541m, 'A541w': total_A541w, 'gonoreykids': total_gonoreykids,
                     'trichom': total_trichom, 'trichow': total_trichow,'hlamidm': total_hlamidm,
                     'hlamidw': total_hlamidw, 'gerpesm': total_gerpesm, 'gerpesw': total_gerpesw,
                     'borodavkim': total_borodavkim, 'borodavkiw': total_borodavkiw}]
        if home == "Заболеваемость населения до 14 лет":
            if registered == "Все зарегистрированные":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title')\
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
            elif registered == "Саратов":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        citizen__title=citizen) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
            elif registered == "Саратовская область":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        citizen__title=citizen) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
            else:
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen, district__title=district_id) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title') \
                        .order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  city14=Sum(Case(When(citizen_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  village14=Sum(Case(When(citizen_id=2, date_bith__year__gt=(int(year) - 15), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_city14 = queryset.aggregate(total_city14=Sum('city14'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_village14 = queryset.aggregate(total_village14=Sum('village14'))['total_village14'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'city14': total_city14, 'village': total_village, 'village14': total_village14}]
        if home == "Заболеваемость населения":
            if registered == "Все зарегистрированные":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
            elif registered == "Саратов":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        citizen__title=citizen) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title')\
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
            elif registered == "Саратовская область":
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        citizen__title=citizen) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
            else:
                if citizen:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen, district__title=district_id) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .exclude(diagnosis__group_of_diagnoses__id=14) \
                        .values('diagnosis__group_of_diagnoses__title').order_by('diagnosis__group_of_diagnoses__title') \
                        .annotate(all=Count('diagnosis__group_of_diagnoses__title'),
                                  city=Sum(Case(When(citizen_id=1, then=Value(1)), default=Value(0))),
                                  saratov=Sum(
                                      Case(When(district__in=[1, 2, 3, 4, 5, 6], then=Value(1)), default=Value(0))),
                                  village=Sum(Case(When(citizen_id=2, then=Value(1)), default=Value(0))),
                                  rf=Sum(Case(When(district_id=47, then=Value(1)), default=Value(0))),
                                  ingr=Sum(Case(When(district_id=48, then=Value(1)), default=Value(0))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_city = queryset.aggregate(total_city=Sum('city'))['total_city'] or 0
                    total_saratov = queryset.aggregate(total_city14=Sum('saratov'))['total_city14'] or 0
                    total_village = queryset.aggregate(total_village=Sum('village'))['total_village'] or 0
                    total_rf = queryset.aggregate(total_rf=Sum('rf'))['total_rf'] or 0
                    total_ingr = queryset.aggregate(total_ingr=Sum('ingr'))['total_ingr'] or 0

                    queryset = list(queryset) + [
                        {'diagnosis__group_of_diagnoses__title': 'Итого', 'all': total_all, 'city': total_city,
                         'saratov': total_saratov, 'village': total_village, 'rf': total_rf, 'ingr': total_ingr}]
        if home == "Заболеваемость дети":
            if registered == "Все зарегистрированные":
                if citizen:
                    if group_of_diagnoses:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                elif group_of_diagnoses:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
            elif registered == "Саратов":
                if citizen:
                    if group_of_diagnoses:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            citizen__title=citizen,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            citizen__title=citizen) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                elif group_of_diagnoses:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
            elif registered == "Саратовская область":
                if citizen:
                    if group_of_diagnoses:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            citizen__title=citizen,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            citizen__title=citizen) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                elif group_of_diagnoses:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
            else:
                if citizen:
                    if group_of_diagnoses:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen, district__title=district_id,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen, district__title=district_id) \
                            .order_by('district__id').values('district__title') \
                            .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                      all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                      allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                      allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                      all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                            date_bith__year__gt=(int(year)-18), then=1))),
                                      allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))),
                                      allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                             date_bith__year__gt=(int(year)-18), then=1))))

                        total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                        total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                        total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                        total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                        total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                        total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                        total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                        queryset = list(queryset) + [
                            {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                             'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                             'allw1417': total_allw1417}]
                elif group_of_diagnoses:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id,
                                                        diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all17=Sum(Case(When(date_bith__year__gt=(int(year) - 18), then=1))),
                                  all14=Sum(Case(When(date_bith__year__gt=(int(year) - 15), then=1))),
                                  allm14=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 15), then=1))),
                                  allw14=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 15), then=1))),
                                  all1417=Sum(Case(When(date_bith__year__lt=(int(year)-13),
                                                        date_bith__year__gt=(int(year)-18), then=1))),
                                  allm1417=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))),
                                  allw1417=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-13),
                                                         date_bith__year__gt=(int(year)-18), then=1))))

                    total_all17 = queryset.aggregate(total_all17=Sum('all17'))['total_all17'] or 0
                    total_all14 = queryset.aggregate(total_all14=Sum('all14'))['total_all14'] or 0
                    total_allm14 = queryset.aggregate(total_allm14=Sum('allm14'))['total_allm14'] or 0
                    total_allw14 = queryset.aggregate(total_allw14=Sum('allw14'))['total_allw14'] or 0
                    total_all1417 = queryset.aggregate(total_all1417=Sum('all1417'))['total_all1417'] or 0
                    total_allm1417 = queryset.aggregate(total_allm1417=Sum('allm1417'))['total_allm1417'] or 0
                    total_allw1417 = queryset.aggregate(total_allw1417=Sum('allw1417'))['total_allw1417'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all17': total_all17, 'all14': total_all14, 'allm14': total_allm14,
                         'allw14': total_allw14, 'all1417': total_all1417, 'allm1417': total_allm1417,
                         'allw1417': total_allw1417}]
        if home == "Способы выявления":
            if registered == "Все зарегистрированные":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=432) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        mesto_obracheniya_id=433) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
            elif registered == "Саратов":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                            citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=432) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7,
                                                        mesto_obracheniya_id=433) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=7) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
            elif registered == "Саратовская область":
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                            citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        mesto_obracheniya_id=432) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47,
                                                        mesto_obracheniya_id=433) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates], district_id__lt=47) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
            else:
                if citizen:
                    if kdo == "КДО-1":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            mesto_obracheniya_id=432, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    elif kdo == "КДО-2":
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            mesto_obracheniya_id=433, citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            citizen__title=citizen) \
                            .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                            .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                      sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                      gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                      trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                      hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                      gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                      boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                      trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                      mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                      chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                      stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                      nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                      kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                        total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                        total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                        total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                        total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                        total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                        total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                        total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                        total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                        total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                        total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                        total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                        total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                        total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                        queryset = list(queryset) + [
                            {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                             'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                             'boroda': total_boroda, 'trihof': total_trihof,
                             'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                             'kisti': total_kisti}]
                elif kdo == "КДО-1":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id,
                                                        mesto_obracheniya_id=432) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                elif kdo == "КДО-2":
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id,
                                                        mesto_obracheniya_id=433) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .values('circumstances_of_detection__title').order_by('circumstances_of_detection__id') \
                        .annotate(drugie=Sum(Case(When(diagnosis__group_of_diagnoses_id=1, then=1))),
                                  sifili=Sum(Case(When(diagnosis__group_of_diagnoses_id=2, then=1))),
                                  gonore=Sum(Case(When(diagnosis__group_of_diagnoses_id=3, then=1))),
                                  trihom=Sum(Case(When(diagnosis__group_of_diagnoses_id=4, then=1))),
                                  hlamid=Sum(Case(When(diagnosis__group_of_diagnoses_id=5, then=1))),
                                  gerpes=Sum(Case(When(diagnosis__group_of_diagnoses_id=6, then=1))),
                                  boroda=Sum(Case(When(diagnosis__group_of_diagnoses_id=7, then=1))),
                                  trihof=Sum(Case(When(diagnosis__group_of_diagnoses_id=8, then=1))),
                                  mikros=Sum(Case(When(diagnosis__group_of_diagnoses_id=9, then=1))),
                                  chesot=Sum(Case(When(diagnosis__group_of_diagnoses_id=10, then=1))),
                                  stopa=Sum(Case(When(diagnosis__group_of_diagnoses_id=11, then=1))),
                                  nogti=Sum(Case(When(diagnosis__group_of_diagnoses_id=12, then=1))),
                                  kisti=Sum(Case(When(diagnosis__group_of_diagnoses_id=13, then=1))))

                    total_drugie = queryset.aggregate(total_drugie=Sum('drugie'))['total_drugie'] or 0
                    total_sifili = queryset.aggregate(total_sifili=Sum('sifili'))['total_sifili'] or 0
                    total_gonore = queryset.aggregate(total_gonore=Sum('gonore'))['total_gonore'] or 0
                    total_trihom = queryset.aggregate(total_trihom=Sum('trihom'))['total_trihom'] or 0
                    total_hlamid = queryset.aggregate(total_hlamid=Sum('hlamid'))['total_hlamid'] or 0
                    total_gerpes = queryset.aggregate(total_gerpes=Sum('gerpes'))['total_gerpes'] or 0
                    total_boroda = queryset.aggregate(total_boroda=Sum('boroda'))['total_boroda'] or 0
                    total_trihof = queryset.aggregate(total_trihof=Sum('trihof'))['total_trihof'] or 0
                    total_mikros = queryset.aggregate(total_mikros=Sum('mikros'))['total_mikros'] or 0
                    total_chesot = queryset.aggregate(total_chesot=Sum('chesot'))['total_chesot'] or 0
                    total_stopa = queryset.aggregate(total_stopa=Sum('stopa'))['total_stopa'] or 0
                    total_nogti = queryset.aggregate(total_nogti=Sum('nogti'))['total_nogti'] or 0
                    total_kisti = queryset.aggregate(total_kisti=Sum('kisti'))['total_kisti'] or 0

                    queryset = list(queryset) + [
                        {'circumstances_of_detection__title': 'Итого', 'drugie': total_drugie, 'sifili': total_sifili,
                         'gonore': total_gonore, 'trihom': total_trihom, 'hlamid': total_hlamid, 'gerpes': total_gerpes,
                         'boroda': total_boroda, 'trihof': total_trihof,
                         'mikros': total_mikros, 'chesot': total_chesot, 'stopa': total_stopa, 'nogti': total_nogti,
                         'kisti': total_kisti}]
        if home == "Для Роспотребнадзора":
            if citizen:
                if group_of_diagnoses:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen,
                                                        diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all=Count('district__title'), allm=Sum(Case(When(sex_id=1, then=1))),
                                  allw=Sum(Case(When(sex_id=2, then=1))),
                                  m01=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 1), then=1))),
                                  w01=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 1), then=1))),
                                  m12=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-0),
                                                    date_bith__year__gt=(int(year)-3), then=1))),
                                  w12=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-0),
                                                    date_bith__year__gt=(int(year)-3), then=1))),
                                  morg36=Sum(Case(When(sex_id=1, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                       date_bith__year__gt=(int(year) - 7), then=1))),
                                  worg36=Sum(Case(When(sex_id=2, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                       date_bith__year__gt=(int(year) - 7), then=1))),
                                  mneorg36=Sum(Case(When(sex_id=1, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                         date_bith__year__gt=(int(year) - 7), then=1))),
                                  wneorg36=Sum(Case(When(sex_id=2, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                         date_bith__year__gt=(int(year) - 7), then=1))),
                                  m714=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-6),
                                                     date_bith__year__gt=(int(year)-15), then=1))),
                                  w714=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-6),
                                                     date_bith__year__gt=(int(year)-15), then=1))),
                                  m1517=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                      date_bith__year__gt=(int(year)-18), then=1))),
                                  w1517=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                      date_bith__year__gt=(int(year)-18), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_m01 = queryset.aggregate(total_m01=Sum('m01'))['total_m01'] or 0
                    total_w01 = queryset.aggregate(total_w01=Sum('w01'))['total_w01'] or 0
                    total_m12 = queryset.aggregate(total_m12=Sum('m12'))['total_m12'] or 0
                    total_w12 = queryset.aggregate(total_w12=Sum('w12'))['total_w12'] or 0
                    total_morg36 = queryset.aggregate(total_morg36=Sum('morg36'))['total_morg36'] or 0
                    total_worg36 = queryset.aggregate(total_worg36=Sum('worg36'))['total_worg36'] or 0
                    total_mneorg36 = queryset.aggregate(total_mneorg36=Sum('mneorg36'))['total_mneorg36'] or 0
                    total_wneorg36 = queryset.aggregate(total_wneorg36=Sum('wneorg36'))['total_wneorg36'] or 0
                    total_m714 = queryset.aggregate(total_m714=Sum('m714'))['total_m714'] or 0
                    total_w714 = queryset.aggregate(total_w714=Sum('w714'))['total_w714'] or 0
                    total_m1517 = queryset.aggregate(total_m1517=Sum('m1517'))['total_m1517'] or 0
                    total_w1517 = queryset.aggregate(total_w1517=Sum('w1517'))['total_w1517'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'm01': total_m01, 'w01': total_w01, 'm12': total_m12, 'w12': total_w12, 'morg36': total_morg36,
                         'worg36': total_worg36, 'mneorg36': total_mneorg36, 'wneorg36': total_wneorg36, 'm714': total_m714,
                         'w714': total_w714, 'm1517': total_m1517, 'w1517': total_w1517}]
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        citizen__title=citizen) \
                        .order_by('district__id').values('district__title') \
                        .annotate(all=Count('district__title'), allm=Sum(Case(When(sex_id=1, then=1))),
                                  allw=Sum(Case(When(sex_id=2, then=1))),
                                  m01=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 1), then=1))),
                                  w01=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 1), then=1))),
                                  m12=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 0),
                                                    date_bith__year__gt=(int(year) - 3), then=1))),
                                  w12=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 0),
                                                    date_bith__year__gt=(int(year) - 3), then=1))),
                                  morg36=Sum(Case(When(sex_id=1, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                       date_bith__year__gt=(int(year) - 7), then=1))),
                                  worg36=Sum(Case(When(sex_id=2, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                       date_bith__year__gt=(int(year) - 7), then=1))),
                                  mneorg36=Sum(Case(When(sex_id=1, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                         date_bith__year__gt=(int(year) - 7), then=1))),
                                  wneorg36=Sum(Case(When(sex_id=2, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                         date_bith__year__gt=(int(year) - 7), then=1))),
                                  m714=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 6),
                                                     date_bith__year__gt=(int(year) - 15), then=1))),
                                  w714=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 6),
                                                     date_bith__year__gt=(int(year) - 15), then=1))),
                                  m1517=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                      date_bith__year__gt=(int(year) - 18), then=1))),
                                  w1517=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                      date_bith__year__gt=(int(year) - 18), then=1))))

                    total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                    total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                    total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                    total_m01 = queryset.aggregate(total_m01=Sum('m01'))['total_m01'] or 0
                    total_w01 = queryset.aggregate(total_w01=Sum('w01'))['total_w01'] or 0
                    total_m12 = queryset.aggregate(total_m12=Sum('m12'))['total_m12'] or 0
                    total_w12 = queryset.aggregate(total_w12=Sum('w12'))['total_w12'] or 0
                    total_morg36 = queryset.aggregate(total_morg36=Sum('morg36'))['total_morg36'] or 0
                    total_worg36 = queryset.aggregate(total_worg36=Sum('worg36'))['total_worg36'] or 0
                    total_mneorg36 = queryset.aggregate(total_mneorg36=Sum('mneorg36'))['total_mneorg36'] or 0
                    total_wneorg36 = queryset.aggregate(total_wneorg36=Sum('wneorg36'))['total_wneorg36'] or 0
                    total_m714 = queryset.aggregate(total_m714=Sum('m714'))['total_m714'] or 0
                    total_w714 = queryset.aggregate(total_w714=Sum('w714'))['total_w714'] or 0
                    total_m1517 = queryset.aggregate(total_m1517=Sum('m1517'))['total_m1517'] or 0
                    total_w1517 = queryset.aggregate(total_w1517=Sum('w1517'))['total_w1517'] or 0

                    queryset = list(queryset) + [
                        {'district__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                         'm01': total_m01, 'w01': total_w01, 'm12': total_m12, 'w12': total_w12, 'morg36': total_morg36,
                         'worg36': total_worg36, 'mneorg36': total_mneorg36, 'wneorg36': total_wneorg36,
                         'm714': total_m714,
                         'w714': total_w714, 'm1517': total_m1517, 'w1517': total_w1517}]
            elif group_of_diagnoses:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                    diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                    .order_by('district__id').values('district__title') \
                    .annotate(all=Count('district__title'), allm=Sum(Case(When(sex_id=1, then=1))),
                              allw=Sum(Case(When(sex_id=2, then=1))),
                              m01=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 1), then=1))),
                              w01=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 1), then=1))),
                              m12=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 0),
                                                date_bith__year__gt=(int(year) - 3), then=1))),
                              w12=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 0),
                                                date_bith__year__gt=(int(year) - 3), then=1))),
                              morg36=Sum(Case(When(sex_id=1, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                   date_bith__year__gt=(int(year) - 7), then=1))),
                              worg36=Sum(Case(When(sex_id=2, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                   date_bith__year__gt=(int(year) - 7), then=1))),
                              mneorg36=Sum(Case(When(sex_id=1, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                     date_bith__year__gt=(int(year) - 7), then=1))),
                              wneorg36=Sum(Case(When(sex_id=2, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                     date_bith__year__gt=(int(year) - 7), then=1))),
                              m714=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 6),
                                                 date_bith__year__gt=(int(year) - 15), then=1))),
                              w714=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 6),
                                                 date_bith__year__gt=(int(year) - 15), then=1))),
                              m1517=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year) - 14),
                                                  date_bith__year__gt=(int(year) - 18), then=1))),
                              w1517=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year) - 14),
                                                  date_bith__year__gt=(int(year) - 18), then=1))))

                total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                total_m01 = queryset.aggregate(total_m01=Sum('m01'))['total_m01'] or 0
                total_w01 = queryset.aggregate(total_w01=Sum('w01'))['total_w01'] or 0
                total_m12 = queryset.aggregate(total_m12=Sum('m12'))['total_m12'] or 0
                total_w12 = queryset.aggregate(total_w12=Sum('w12'))['total_w12'] or 0
                total_morg36 = queryset.aggregate(total_morg36=Sum('morg36'))['total_morg36'] or 0
                total_worg36 = queryset.aggregate(total_worg36=Sum('worg36'))['total_worg36'] or 0
                total_mneorg36 = queryset.aggregate(total_mneorg36=Sum('mneorg36'))['total_mneorg36'] or 0
                total_wneorg36 = queryset.aggregate(total_wneorg36=Sum('wneorg36'))['total_wneorg36'] or 0
                total_m714 = queryset.aggregate(total_m714=Sum('m714'))['total_m714'] or 0
                total_w714 = queryset.aggregate(total_w714=Sum('w714'))['total_w714'] or 0
                total_m1517 = queryset.aggregate(total_m1517=Sum('m1517'))['total_m1517'] or 0
                total_w1517 = queryset.aggregate(total_w1517=Sum('w1517'))['total_w1517'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                     'm01': total_m01, 'w01': total_w01, 'm12': total_m12, 'w12': total_w12, 'morg36': total_morg36,
                     'worg36': total_worg36, 'mneorg36': total_mneorg36, 'wneorg36': total_wneorg36, 'm714': total_m714,
                     'w714': total_w714, 'm1517': total_m1517, 'w1517': total_w1517}]
            else:
                queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                    .order_by('district__id').values('district__title') \
                    .annotate(all=Count('district__title'), allm=Sum(Case(When(sex_id=1, then=1))),
                              allw=Sum(Case(When(sex_id=2, then=1))),
                              m01=Sum(Case(When(sex_id=1, date_bith__year__gt=(int(year) - 1), then=1))),
                              w01=Sum(Case(When(sex_id=2, date_bith__year__gt=(int(year) - 1), then=1))),
                              m12=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-0),
                                                date_bith__year__gt=(int(year)-3), then=1))),
                              w12=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-0),
                                                date_bith__year__gt=(int(year)-3), then=1))),
                              morg36=Sum(Case(When(sex_id=1, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                   date_bith__year__gt=(int(year) - 7), then=1))),
                              worg36=Sum(Case(When(sex_id=2, post_id=23, date_bith__year__lt=(int(year) - 2),
                                                   date_bith__year__gt=(int(year) - 7), then=1))),
                              mneorg36=Sum(Case(When(sex_id=1, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                     date_bith__year__gt=(int(year) - 7), then=1))),
                              wneorg36=Sum(Case(When(sex_id=2, post_id=24, date_bith__year__lt=(int(year) - 2),
                                                     date_bith__year__gt=(int(year) - 7), then=1))),
                              m714=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-6),
                                                 date_bith__year__gt=(int(year)-15), then=1))),
                              w714=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-6),
                                                 date_bith__year__gt=(int(year)-15), then=1))),
                              m1517=Sum(Case(When(sex_id=1, date_bith__year__lt=(int(year)-14),
                                                  date_bith__year__gt=(int(year)-18), then=1))),
                              w1517=Sum(Case(When(sex_id=2, date_bith__year__lt=(int(year)-14),
                                                  date_bith__year__gt=(int(year)-18), then=1))))

                total_all = queryset.aggregate(total_all=Sum('all'))['total_all'] or 0
                total_allm = queryset.aggregate(total_allm=Sum('allm'))['total_allm'] or 0
                total_allw = queryset.aggregate(total_allw=Sum('allw'))['total_allw'] or 0
                total_m01 = queryset.aggregate(total_m01=Sum('m01'))['total_m01'] or 0
                total_w01 = queryset.aggregate(total_w01=Sum('w01'))['total_w01'] or 0
                total_m12 = queryset.aggregate(total_m12=Sum('m12'))['total_m12'] or 0
                total_w12 = queryset.aggregate(total_w12=Sum('w12'))['total_w12'] or 0
                total_morg36 = queryset.aggregate(total_morg36=Sum('morg36'))['total_morg36'] or 0
                total_worg36 = queryset.aggregate(total_worg36=Sum('worg36'))['total_worg36'] or 0
                total_mneorg36 = queryset.aggregate(total_mneorg36=Sum('mneorg36'))['total_mneorg36'] or 0
                total_wneorg36 = queryset.aggregate(total_wneorg36=Sum('wneorg36'))['total_wneorg36'] or 0
                total_m714 = queryset.aggregate(total_m714=Sum('m714'))['total_m714'] or 0
                total_w714 = queryset.aggregate(total_w714=Sum('w714'))['total_w714'] or 0
                total_m1517 = queryset.aggregate(total_m1517=Sum('m1517'))['total_m1517'] or 0
                total_w1517 = queryset.aggregate(total_w1517=Sum('w1517'))['total_w1517'] or 0

                queryset = list(queryset) + [
                    {'district__title': 'Итого', 'all': total_all, 'allm': total_allm, 'allw': total_allw,
                     'm01': total_m01, 'w01': total_w01, 'm12': total_m12, 'w12': total_w12, 'morg36': total_morg36,
                     'worg36': total_worg36, 'mneorg36': total_mneorg36, 'wneorg36': total_wneorg36, 'm714': total_m714,
                     'w714': total_w714, 'm1517': total_m1517, 'w1517': total_w1517}]
        if home == "Пофамильный отчет":
            if registered == "Все зарегистрированные":
                if citizen:
                    if group_of_diagnoses:
                        if physician_id:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                physician__title=physician_id,
                                                                citizen__title=citizen) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    elif physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            physician__title=physician_id, citizen__title=citizen) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif group_of_diagnoses:
                    if physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            physician__title=physician_id) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif physician_id:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        physician__title=physician_id) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField())) \
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection') \
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField()))\
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection')\
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith', 'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
            elif registered == "Саратов":
                if citizen:
                    if group_of_diagnoses:
                        if physician_id:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                physician__title=physician_id,
                                                                citizen__title=citizen,
                                                                district_id__in=[1, 2, 3, 4, 5, 6]) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                district_id__in=[1, 2, 3, 4, 5, 6],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    elif physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district_id__in=[1, 2, 3, 4, 5, 6],
                                                            physician__title=physician_id, citizen__title=citizen) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district_id__in=[1, 2, 3, 4, 5, 6],
                                                            citizen__title=citizen) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif group_of_diagnoses:
                    if physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district_id__in=[1, 2, 3, 4, 5, 6],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            physician__title=physician_id) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district_id__in=[1, 2, 3, 4, 5, 6],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif physician_id:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district_id__in=[1, 2, 3, 4, 5, 6],
                                                        physician__title=physician_id) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField())) \
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection') \
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district_id__in=[1, 2, 3, 4, 5, 6]) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField()))\
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection')\
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith', 'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
            elif registered == "Саратовская область":
                if citizen:
                    if group_of_diagnoses:
                        if physician_id:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                physician__title=physician_id,
                                                                citizen__title=citizen) \
                                .filter(
                                district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                                 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                                 39, 40, 41, 42, 43, 44, 45, 46]) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                                .filter(
                                district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                                 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                                 39, 40, 41, 42, 43, 44, 45, 46]) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    elif physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            physician__title=physician_id, citizen__title=citizen) \
                            .filter(
                            district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                             21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                             39, 40, 41, 42, 43, 44, 45, 46]) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            citizen__title=citizen) \
                            .filter(
                            district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                             21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                             39, 40, 41, 42, 43, 44, 45, 46]) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif group_of_diagnoses:
                    if physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            physician__title=physician_id) \
                            .filter(
                            district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                             21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                             39, 40, 41, 42, 43, 44, 45, 46]) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .filter(
                            district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                             21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                             39, 40, 41, 42, 43, 44, 45, 46]) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif physician_id:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        physician__title=physician_id) \
                        .filter(district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                                 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                                 39, 40, 41, 42, 43, 44, 45, 46]) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField())) \
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection') \
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                        .filter(district_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                                 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                                 39, 40, 41, 42, 43, 44, 45, 46]) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField()))\
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection')\
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith', 'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
            else:
                if citizen:
                    if group_of_diagnoses:
                        if physician_id:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                district__title=district_id,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                                physician__title=physician_id,
                                                                citizen__title=citizen) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                        else:
                            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                                district__title=district_id,
                                                                citizen__title=citizen,
                                                                diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                                   When(sex_id=2, then=Value('Ж')),
                                                                                   default=F('id'),
                                                                                   output_field=CharField())) \
                                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                                'mesto_obracheniya', 'circumstances_of_detection') \
                                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                        'district__title',
                                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    elif physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            physician__title=physician_id, citizen__title=citizen) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            citizen__title=citizen) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif group_of_diagnoses:
                    if physician_id:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses,
                                                            physician__title=physician_id) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                    else:
                        queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                            district__title=district_id,
                                                            diagnosis__group_of_diagnoses__title=group_of_diagnoses) \
                            .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                               When(sex_id=2, then=Value('Ж')),
                                                                               default=F('id'),
                                                                               output_field=CharField())) \
                            .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                            'mesto_obracheniya', 'circumstances_of_detection') \
                            .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                    'district__title',
                                    'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                    'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                    'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                elif physician_id:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id,
                                                        physician__title=physician_id) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField())) \
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection') \
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith',
                                'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
                else:
                    queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                        district__title=district_id) \
                        .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                           When(sex_id=2, then=Value('Ж')),
                                                                           default=F('id'),
                                                                           output_field=CharField()))\
                        .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                        'mesto_obracheniya', 'circumstances_of_detection')\
                        .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith', 'district__title',
                                'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                                'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                                'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
        if home == "АГБ":
            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates]) \
                .filter(circumstances_of_detection__in=[12, 13])\
                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                   When(sex_id=2, then=Value('Ж')), default=F('id'),
                                                                   output_field=CharField()))\
                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                'mesto_obracheniya', 'circumstances_of_detection')\
                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith', 'district__title',
                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                        'circumstances_of_detection__title', 'date_of_establishment', 'VRACH')
        if home == "Пофамильный отчет по врачам":
            queryset = IndexForm.objects.filter(DATE_ZAP__range=[start_date, end_dates],
                                                physician__title=physician_id) \
                .order_by('lastname').annotate(translated_sex=Case(When(sex_id=1, then=Value('М')),
                                                                   When(sex_id=2, then=Value('Ж')), default=F('id'),
                                                                   output_field=CharField())) \
                .select_related('district', 'citizen', 'post', 'diagnosis', 'place_of_detection',
                                'mesto_obracheniya', 'circumstances_of_detection', 'physician') \
                .values('lastname', 'firstname', 'middle_name', 'translated_sex', 'date_bith', 'district__title',
                        'locality', 'citizen__title', 'street', 'home', 'body', 'flat', 'post__title',
                        'diagnosis__mkb', 'place_of_detection__title', 'mesto_obracheniya__title',
                        'circumstances_of_detection__title', 'date_of_establishment', 'physician__title')
        return queryset


    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        district_id = self.request.GET.get('district')
        context['start_date'] = self.request.GET.get('start_date')
        context['end_dates'] = self.request.GET.get('end_dates')
        context['districts'] = self.request.GET.get('districts')
        context['home'] = self.request.GET.get('home')
        context['registered'] = self.request.GET.get('registered')
        context['citizen'] = self.request.GET.get('citizen')
        context['group_of_diagnoses'] = self.request.GET.get('group_of_diagnoses')
        context['kdo'] = self.request.GET.get('kdo')
        context['question1'] = Physician.objects.values('title')
        context['question2'] = District.objects.values('title').order_by('id')
        context['question3'] = GroupOfDiagnoses.objects.values('title').order_by('id')
        context['question4'] = Citizen.objects.values('title').order_by('id')
        context['district_title'] = district_id
        return context