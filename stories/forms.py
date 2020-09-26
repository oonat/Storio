from django import forms
from .models import Entry, Story

class NewEntryForm(forms.ModelForm):
	
	class Meta:
		model = Entry
		fields = ('text', 'notes',)


class NewStoryForm(forms.ModelForm):
	
	class Meta:
		model = Story
		fields = ('title', 'private', 'genre', 'story_img', 'story_description',)


class StorySettingsForm(forms.ModelForm):
	
	class Meta:
		model = Story
		fields = ('title', 'private', 'active', 'genre', 'story_img', 'story_description',)