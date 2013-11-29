from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.core import serializers
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from pos.models import *
from pos.project_forms import *


@login_required()
def advanced(request):
    return render_to_response('pos/advanced/advanced.html',
        {},
        context_instance=RequestContext(request)
    )

@login_required()
def manage_projects(request):
    user = request.user  # Get the user to load their relevant projects
    projects = Project.objects.filter(user=user)

    # Load the template
    t = loader.get_template('pos/project/manage_projects.html')
    c = RequestContext(request, {
        'projects': projects
    })
    return HttpResponse(t.render(c))

@login_required()
def add_project(request):
    # Create the form with no bound data
    projectForm = ProjectForm()
    next_url = ''

    # If request was GET
    if request.method == 'GET':
        # Check if this needs to redirect after creating the Project
        if 'next' in request.GET:
            next_url = request.GET['next']

    # If request was POST
    if request.method == 'POST':
        if 'next' in request.POST:
            next_url = request.POST['next']
            if next_url == 'select_lga_or_suburb':
                region_type = REGION_TYPE_CHOICE_USER_LGA_SUBURB
            else:
                region_type = REGION_TYPE_CHOICE_USER
        if 'project_name' in request.POST:
            projectForm = ProjectForm(request.POST)
            # Save the new project if the form is valid
            if projectForm.is_valid():
                # Get the user who will own the Project
                user = request.user
                project_name = projectForm.cleaned_data['project_name']
                # Create a User Region object for this project
                user_region = Region()
                user_region.sub_lga_id = "-"
                user_region.name = project_name
                user_region.type = region_type
                user_region.save()
                # Create a User modifiable statistics object for this project
                user_statistic = User_Statistic()
                user_statistic.save()
                # Create the project
                project = Project()
                project.user = user
                project.project_name = project_name
                project.region = user_region
                project.user_statistic = user_statistic
                project.save()
                user_region.sub_lga_id = region_type + str(project.pk)
                user_region.save()
                # Redirect to the appropriate page after successful creation
                if next_url == 'draw_project':
                    return HttpResponseRedirect(
                        reverse('draw_user_region', args=(user_region.pk,))
                    )
                elif next_url == 'upload_project':
                    return HttpResponseRedirect(
                        reverse('upload_user_region', args=(user_region.pk,))
                    )
                elif next_url == 'select_lga_or_suburb':
                    return HttpResponseRedirect(
                        reverse('select_lga_suburb_user_region', args=(user_region.pk,))
                    )
                else:
                    return HttpResponseRedirect(reverse('manage_projects'))
            # Else form invalid
            else:
                messages.error(request, 'Please review the form and correct it before re-submitting.')

    # Load the template
    return render_to_response('pos/project/add_project.html',
        {
            'projectForm': projectForm,
            'next_url': next_url
        },
        context_instance=RequestContext(request)
    )

@login_required()
def delete_project(request):

    # If request was POST
    if request.method == 'POST':
        if 'project_pk' in request.POST:
            project_pk = request.POST['project_pk']

            # Check if the currently logged in user is deleting their own project
            # And that the Project PK actually exists
            user = request.user
            try:
                project = Project.objects.get(pk=project_pk)
            except Project.DoesNotExist:
                raise Http404, 'This project with primary key= %s does not exist' % project_pk
            if user != project.user:
                raise Http404, 'User %s does not own project %s with primary key= %s' % (user.username, project.project_name, project_pk)

            # Delete the necessary data
            try:
                abs_pop_stats = ABS_Region_Population.objects.get(sub_lga_id=project.region.sub_lga_id)
                abs_pop_stats.delete()
            except:
                x = 1
            # This cascade-deletes any area_pop_stats and facility_statistics
            project.region.delete()
            project.user_statistic.delete()
            project.delete()

            # Load the template
            messages.success(request, 'The project was successfully deleted.')
            return HttpResponseRedirect(reverse('manage_projects'))
        else:
            raise Http404, 'No primary key was supplied for the project to delete.'
    else:
        return HttpResponseNotAllowed(['POST'])
