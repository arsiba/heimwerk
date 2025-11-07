from django.shortcuts import render
from .models import TF_Module, Instance
from django.views import generic
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
    user_instances_count = Instance.objects.filter(owner=user).count()
    all_instances_count = Instance.objects.count()
    can_deploy = is_admin or is_editor or is_user
    context = {
        'num_visits': num_visits,
        'modules': modules,
        'can_deploy': can_deploy,
        'is_admin': is_admin,
        'user_instances_count': user_instances_count,
        'all_instances_count': all_instances_count,
    }

    # Render the HTML template index.html with the data in the context variable.
    return render(request, 'index.html', context=context)

class ModuleListView(generic.ListView):
    """Generic class-based view for a list of modules."""
    model = TF_Module
    paginate_by = 10

class ModuleDetailView(generic.DetailView):
    """Generic class-based detail view for a module."""
    model = TF_Module
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_instances'] = self.object.instances.filter(owner=self.request.user)
        if self.request.user.is_superuser:
            context['user_instances'] = self.object.instances.all()
        else:
            context['user_instances'] = []
        context['can_deploy'] = self.request.user.groups.filter(name="user").exists() or self.request.user.groups.filter(name="editor").exists()
        return context