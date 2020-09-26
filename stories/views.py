from django.shortcuts import render
from .models import Entry, Story
from account.models import Account
from .forms import NewEntryForm, NewStoryForm, StorySettingsForm
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
import math
import re
# for story_download #
from storio.utils import PdfCreator
from django.http import HttpResponse
# for notification
from notifications.signals import notify


def text_cleaner(text):
	clean = re.compile('<.*?>')
	cleaned_string = re.sub(clean, '', text, re.UNICODE)

	return cleaned_string


def landing_page(request):
	if request.user.is_authenticated :
		return redirect('stories:story_list')
	else:
		return render(request, 'stories/misc/landing_page.html', {})

def story_list(request):
	context = {}

	if request.method == "POST":
		form = NewStoryForm(request.POST, request.FILES)
		if form.is_valid():
			story = form.save(commit=False)
			story.title = text_cleaner(story.title)
			story.story_description = text_cleaner(story.story_description)
			story.creator = request.user
			story.active = True

			if story.title != "":
				story.create()

			return redirect('stories:story_list')
	else:
		form = NewStoryForm()


	stories = Story.objects.all()

	if request.method == "GET":
		genre_query = request.GET.get("genre_select", None)
		private_query = request.GET.get("private_select", None)
		active_query = request.GET.get("active_select", None)
		sort_by_query = request.GET.get("sort_by", None)


		if genre_query != "All" and genre_query != None:
			stories = stories.filter(genre=genre_query)

		if private_query != "All" and private_query != None:
			stories = stories.filter(private=private_query)

		if active_query != "All" and active_query != None:
			stories = stories.filter(active=active_query)


		if sort_by_query == "The Most Viewed":
			stories = stories.order_by('-view_count')
		# equals to the most commented
		elif sort_by_query == "The Most Popular":
			stories = stories.annotate(num_entries=Count('entry')).order_by('-num_entries')
		elif sort_by_query == "The Most Liked":
			stories = stories.annotate(num_favs=Count('favorite_stories')).order_by('-num_favs')
		else:
			stories = stories.order_by('-created_date')


	# paginator (reverse order date)
	paginator = Paginator(stories, 12)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	context['form'] = form
	context['page_obj'] = page_obj
	context['order'] = sort_by_query

	return render(request, 'stories/story_views/gallery.html', context)



def story_detail(request, slug_story):
	story = get_object_or_404(Story, slug=slug_story)

	# PERMISSION CHECK 
	if not story.private or request.user == story.creator or story.permitted_users.filter(id=request.user.id).exists():

		if request.method == "POST":
			if 'add_fav' in request.POST:
				request.user.favorite_stories.add(story)
			elif 'remove_fav' in request.POST:
				request.user.favorite_stories.remove(story)
			else:
				form = NewEntryForm(request.POST)
				if form.is_valid() and story.active:
					entry = form.save(commit=False)
					entry.text = text_cleaner(entry.text)
					entry.notes = text_cleaner(entry.notes)
					entry.author = request.user
					entry.story = get_object_or_404(Story, slug=slug_story)

					if entry.text != "":
						creator_user = story.creator
						contributed_users = [ entry.author for entry in Entry.objects.filter(story=story) ]
						favorite_users = list(Account.objects.filter(favorite_stories__in=[story]))
						recipients = list(set(contributed_users + favorite_users + [creator_user]))
						if request.user in recipients: recipients.remove(request.user)

						if recipients != []:
							notify.send(request.user, recipient=recipients, verb='has added entry to', action_object=story)
						entry.publish()

			return redirect('stories:story_detail', slug_story=slug_story)
		else:
			form = NewEntryForm()

		""" enable new_entry button
		if len(entries) != 0:
			enable_new_entry = False if request.user == Entry.objects.filter(story__slug=slug_story).order_by('-published_date')[0].author else True
		else:
			enable_new_entry = True """

		entries = Entry.objects.filter(story__slug=slug_story).order_by('published_date')

		enable_new_entry = True
		context = {'form': form, 'story': story, 'enable_new_entry': enable_new_entry}

		if request.user.is_authenticated:
			is_in_favorites = True if story in request.user.favorite_stories.all() else False
			context['is_in_favorites'] = is_in_favorites

		# display style
		display_style = request.GET.get('display')

		if display_style == None:
			# view counter increases if page has just opened
			story.view_count += 1
			story.save()

		# do not write elif, else condition is for both style= None and style= "timeline"
		if display_style == "paper":
			# paginator paper
			paginator = Paginator(entries, 25)
			page_number = request.GET.get('page')
			page_obj = paginator.get_page(page_number)

			# progressbar
			if page_number == None:
				page_progress = math.floor(100/paginator.num_pages)
			elif int(page_number) > paginator.num_pages:
				page_progress = 100
			else:
				page_progress = math.floor(float(page_number)*100/paginator.num_pages) if paginator.num_pages != 0 else 0

			context['page_obj'] = page_obj
			context['page_progress'] = page_progress

			return render(request, 'stories/story_views/paper.html', context)

		else:
			# paginator timeline
			paginator = Paginator(entries, 10)
			page_number = request.GET.get('page')
			if not page_number:
				page_number = paginator.num_pages
			page_obj = paginator.get_page(page_number)

			context['page_obj'] = page_obj

			return render(request, 'stories/story_views/timeline.html', context)


	else:
		return render(request, 'stories/misc/story_permission_denied.html', {})




def entry_detail(request, slug_entry):
	entry = get_object_or_404(Entry, slug=slug_entry)
	story = entry.story

	# PERMISSION CHECK
	if not story.private or request.user == story.creator or story.permitted_users.filter(id=request.user.id).exists():
		total_len = len("".join([e.text for e in Entry.objects.filter(story=story)]))
		contribution_len = len("".join([e.text for e in Entry.objects.filter(story=story, author=entry.author)]))
		contribution_percentage = math.floor(contribution_len*100/total_len if total_len != 0 else 0)
		return render(request, 'stories/story_views/entry_detail.html', {'entry': entry, 'story': story, 'contribution_percentage': contribution_percentage})

	else:
		return render(request, 'stories/misc/story_permission_denied.html', {})


def search(request):
	query = request.GET.get("q", None)

	if query == None:
		return redirect('stories:story_list')

	stories = get_search_results(query)

	# paginator (reverse order date)
	paginator = Paginator(stories, 16)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'stories/story_views/search.html', {'query': query, 'page_obj': page_obj})

def get_search_results(query=None):

	results = []
	query_list = query.split(" ")

	for q in query_list:
		posts = Story.objects.filter(
			Q(title__icontains=q) | 
			Q(creator__username__icontains=q) | 
			Q(genre__icontains=q)).distinct().order_by('-created_date')

	for post in posts:
		results.append(post)

	return list(set(results))


def story_settings(request, slug_story):

	story = get_object_or_404(Story, slug=slug_story)

	if request.user == story.creator:
		if request.method == "POST":
			form = StorySettingsForm(request.POST, request.FILES, instance=story)
			if form.is_valid():
				story = form.save(commit=False)
				story.title = text_cleaner(story.title)
				story.story_description = text_cleaner(story.story_description)
				story.creator = request.user

				if story.title != "":
					story.create()

				return redirect('stories:story_detail', slug_story=slug_story)
		else:
			form = StorySettingsForm(

				initial={
					"title": story.title, 
					"genre": story.genre,
					"story_description": story.story_description, 
					"private": story.private,
					"active": story.active,
				}

				)


		return render(request, 'stories/settings/story_settings.html', {'story': story, 'settings_form': form})

	else:
		return redirect('stories:story_detail', slug_story=slug_story)



def delete_story(request, slug_story):
	story = get_object_or_404(Story, slug=slug_story)

	if request.user == story.creator:
		story.delete()
		return redirect('stories:story_list')
	else:
		return redirect('stories:story_detail', slug_story=slug_story)



def edit_story_permissions(request, slug_story):

	story = get_object_or_404(Story, slug=slug_story)

	if request.user == story.creator:

		context = {}

		if request.method == "POST":
			target_user_email = request.POST["target_user_email"]

			try:
				target_user = Account.objects.get(email = target_user_email)
				story.permitted_users.add(target_user)
				context['successful_message'] = "The user has been added successfully."

			except Account.DoesNotExist:
				context['warning_message'] = "There is no user with the given email adress."


		users = story.permitted_users.all().order_by('email')

		paginator = Paginator(users, 10)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)

		context['story'] = story
		context['page_obj'] = page_obj


		return render(request, 'stories/settings/edit_story_permissions.html', context)

	else:
		return redirect('stories:story_detail', slug_story=slug_story)




def revoke_user_permission(request, slug_story, user_pk):

	story = get_object_or_404(Story, slug=slug_story)

	if request.user == story.creator:
		target_user = get_object_or_404(Account, pk=user_pk)
		story.permitted_users.remove(target_user)

		return redirect('stories:edit_story_permissions', slug_story=slug_story)
	else:
		return redirect('stories:story_detail', slug_story=slug_story)



def story_download(request, slug_story):

	story = get_object_or_404(Story, slug=slug_story)

	# PERMISSION CHECK 
	if not story.private or request.user == story.creator or story.permitted_users.filter(id=request.user.id).exists():

		entries = Entry.objects.filter(story__slug=slug_story).order_by('published_date')
		whole_story = ""
		for entry in entries:
			whole_story+= entry.text

		pdf_creator = PdfCreator()

		pdf_value = pdf_creator.build_pdf(story.title, whole_story)

		response = HttpResponse(content_type='application/pdf')
		response['Content-Disposition'] = 'attachment; filename='+ story.slug +"_Storio.pdf"
    
		response.write(pdf_value)
		return response

	else:
		return render(request, 'stories/misc/story_permission_denied.html', {})



def add_to_favorites(request, slug_story):

	story = get_object_or_404(Story, slug=slug_story)

	# PERMISSION CHECK 
	if not story.private or request.user == story.creator or story.permitted_users.filter(id=request.user.id).exists():
		request.user.favorite_stories.add(story)
		return redirect('stories:story_detail', slug_story=slug_story)

	else:
		return render(request, 'stories/misc/story_permission_denied.html', {})



def remove_from_favorites(request, slug_story):

	story = get_object_or_404(Story, slug=slug_story)

	# PERMISSION CHECK 
	if not story.private or request.user == story.creator or story.permitted_users.filter(id=request.user.id).exists():
		request.user.favorite_stories.remove(story)
		return redirect('stories:story_detail', slug_story=slug_story)

	else:
		return render(request, 'stories/misc/story_permission_denied.html', {})




def notifications_all(request):

	if request.user.is_authenticated:
		context = {}
		notifications = request.user.notifications.all()

		if request.method == "POST":
			notifications.mark_all_as_read(request.user)

		paginator = Paginator(notifications, 5)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		context['page_obj'] = page_obj
		return render(request, 'stories/notifications/notifications_all.html', context)
	else:
		return redirect('account:login_view')

def notifications_unread(request):

	if request.user.is_authenticated:
		context = {}
		notifications = request.user.notifications.unread()

		if request.method == "POST":
			notifications.mark_all_as_read(request.user)

		paginator = Paginator(notifications, 5)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		context['page_obj'] = page_obj
		return render(request, 'stories/notifications/notifications_unread.html', context)
	else:
		return redirect('account:login_view')

def notifications_read(request):

	if request.user.is_authenticated:
		context = {}
		notifications = request.user.notifications.read()

		if request.method == "POST":
			notifications.mark_all_as_unread(request.user)

		paginator = Paginator(notifications, 5)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		context['page_obj'] = page_obj
		return render(request, 'stories/notifications/notifications_read.html', context)
	else:
		return redirect('account:login_view')
