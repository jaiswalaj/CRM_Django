from urllib import request
from django.core.mail import send_mail
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import generic
from .models import Lead, Agent
from .forms import LeadModelForm, CustomUserCreationForm, AssignAgentForm
from agents.mixins import OrganiserAndLoginRequiredMixin
# Create your views here.


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse("login")


# Landing Page both as Class based view and as Function based view. Only one is being used in production.
class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

def landing_page(request):
    return render(request, "landing.html")


# Lead List Page both as Class based view and as Function based view. Only one is being used in production.
class LeadListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/lead_list.html"
    context_object_name = "leads"

    def get_queryset(self):
        user = self.request.user

        if user.is_organiser:
            queryset = Lead.objects.filter(organisation=user.userprofile, agent__isnull=False)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation, agent__isnull=False)
            queryset = queryset.filter(agent__user=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organiser:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, 
                agent__isnull=True
            )
            context.update({
                "unassigned_leads" : queryset
            })
        return context

def lead_list(request):
    leads = Lead.objects.all()
    context = {
        "leads" : leads
    }
    return render(request, "leads/lead_list.html", context)


# Lead Detail Page both as Class based view and as Function based view. Only one is being used in production.
class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user

        if user.is_organiser:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            queryset = queryset.filter(agent__user=user)
        return queryset


def lead_detail(request, pk):
    lead = Lead.objects.get(id=pk)
    context = {
        "lead" : lead
    }
    return render(request, "leads/lead_detail.html", context)


# Lead Create Page both as Class based view and as Function based view. Only one is being used in production.
class LeadCreateView(OrganiserAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(LeadCreateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs

    def form_valid(self, form):
        lead = form.save(commit=False)
        send_mail(
            subject="A Lead has been created",
            message="A lead with details has been created. Visit your account",
            from_email="test@test.com",
            recipient_list=["test2@test.com"],
        )
        lead.organisation = self.request.user.userprofile
        return super(LeadCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse("leads:lead-list")

def lead_create(request):
    form = LeadModelForm()

    if request.method == "POST":
        form = LeadModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/leads")
    
    context = {
        "form" : form
    }
    return render(request, "leads/lead_create.html", context)


# Lead Create Page both as Class based view and as Function based view. Only one is being used in production.
class LeadUpdateView(OrganiserAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_update.html"
    form_class = LeadModelForm

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.filter(organisation=user.userprofile)
        return queryset


    def get_success_url(self):
        return reverse("leads:lead-list")

def lead_update(request, pk):
    lead = Lead.objects.get(id=pk)
    form = LeadModelForm(instance=lead)
    if request.method == "POST":
        form = LeadModelForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect("/leads")

    context = {
        "lead" : lead,
        "form" : form,
    }
    return render(request, "leads/lead_update.html", context)


# Lead Create Page both as Class based view and as Function based view. Only one is being used in production.
class LeadDeleteView(OrganiserAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/lead_delete.html"

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.filter(organisation=user.userprofile)
        return queryset

    def get_success_url(self):
        return reverse("leads:lead-list")

def lead_delete(request, pk):
    lead = Lead.objects.get(id=pk)
    lead.delete()
    return redirect("/leads")

class AssignAgentView(OrganiserAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)