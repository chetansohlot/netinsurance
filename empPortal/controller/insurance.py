from django.shortcuts import render, redirect
from django.contrib import messages

from empPortal.model.StateCity import City, State
from ..model import Insurance
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
@login_required
def insurance_list(request):
    insurance_qs = Insurance.objects.all().order_by('-created_at')

    total_count = insurance_qs.count()
    active_count = insurance_qs.filter(active='Active').count()    # updated value
    inactive_count = insurance_qs.filter(active='Inactive').count()  # updated value
    return render(request, 'insurance/insurance_index.html',
                  {
                      'insurance_qs': insurance_qs,
                      'total_count': total_count,
                      'active_count': active_count,
                      'inactive_count': inactive_count,
                  })
                  
@login_required
def insurance_create(request):
    states = State.objects.all()
    cities = City.objects.all()

    if request.method == 'POST':
        name = request.POST.get('insurance_company')  # Maps to InsuranceType.name
        status = request.POST.get('active', 'Active')

        pincode = request.POST.get('pincode')
        address = request.POST.get('address')
        commencement_date = request.POST.get('commencement_date')
        state = request.POST.get('state')
        city = request.POST.get('city')
        # Save to the database
        Insurance.objects.create(
            insurance_company=name,
            active=status,
            pincode=pincode if pincode else None,
            address=address,
            commencement_date=commencement_date if commencement_date else None,
            state=state,
            city=city
        )

        messages.success(request, 'Insurance Type created successfully.')
        return redirect('insurance_index')

    return render(request, 'insurance/insurance-create.html',{'states':states, 'cities':cities})
@login_required
def insurance_edit(request, insurance_id):
    insurance = get_object_or_404(Insurance, id=insurance_id)
    states = State.objects.all()
    cities = City.objects.all()

    if request.method == 'POST':
        insurance.insurance_company = request.POST.get('insurance_company')
        insurance.active = request.POST.get('active', 'Active')

        insurance.pincode = request.POST.get('pincode') or None
        insurance.address = request.POST.get('address') or None
        insurance.commencement_date = request.POST.get('commencement_date') or None
        insurance.state = request.POST.get('state') or None
        insurance.city = request.POST.get('city') or None

        insurance.save()
        messages.success(request, 'Insurance updated successfully.')
        return redirect('insurance_index')

    return render(request, 'insurance/insurance-create.html', {'insurance': insurance, 'states':states, 'cities':cities})


@login_required
def toggle_insurance_status(request, insurance_id):
    insurance = get_object_or_404(Insurance, id=insurance_id)

    if insurance.active == 'Active':
        insurance.active = 'Inactive'
        messages.info(request, 'Insurance deactivated successfully.')
    else:
        insurance.active = 'Active'
        messages.success(request, 'Insurance activated successfully.')

    insurance.save()
    return redirect('insurance_index')

def get_state(request):
    states = State.objects.all()
    return render(request, 'insurance/insurance-create.html', {'states': states})

def get_cities(request):
    state_id = request.GET.get('state_id')
    cities = City.objects.filter(state_id=state_id).values('id', 'city')
    return JsonResponse({'cities': list(cities)})
