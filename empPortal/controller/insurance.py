from django.shortcuts import render, redirect
from django.contrib import messages
from ..model import Insurance
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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


def insurance_create(request):
    if request.method == 'POST':
        insurance_company = request.POST.get('insurance_company')
        active = request.POST.get('active', 'Active') 

        # Save to the database
        Insurance.objects.create(
            insurance_company=insurance_company,
            active=active
        )
        messages.success(request, 'Insurance created successfully.')
        return redirect('insurance_index')

    return render(request, 'insurance/insurance_create.html')

def insurance_edit(request, insurance_id):
    insurance = get_object_or_404(Insurance, id=insurance_id)
    if request.method == 'POST':
        insurance.insurance_company = request.POST.get('insurance_company')
        insurance.active = request.POST.get('active', 'Active') 
        messages.success(request, 'Insurance updated successfully.')
        insurance.save()

        return redirect('insurance_index')

    return render(request, 'insurance/insurance_create.html', {'insurance': insurance})

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
