from django.shortcuts import render

# Create your views here.


def index(request):
    """View function for home page of site."""

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    context = {'num_visits': num_visits}

    # Render the HTML template index.html with the data in the context variable.
    return render(request, 'index.html', context=context)
