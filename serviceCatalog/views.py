from django.shortcuts import render
from .models import TF_Module
# Create your views here.


def index(request):
    """View function for home page of site."""

    modules = TF_Module.objects.all()[:5]

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits
    user = request.user
    print(user.groups.all())
    is_admin = user.groups.filter(name="admin").exists()
    is_editor = user.groups.filter(name="editor").exists()
    is_user = user.groups.filter(name="user").exists()
    can_deploy = is_admin or is_editor or is_user
    context = {
        'num_visits': num_visits,
        'modules': modules,
        'can_deploy': can_deploy,
        'is_admin': is_admin,
    }

    # Render the HTML template index.html with the data in the context variable.
    return render(request, 'index.html', context=context)