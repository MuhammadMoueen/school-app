from django.apps import apps
from django.contrib import admin


# Register all models from this app so admin remains functional even if
# model definitions change frequently.
app_config = apps.get_app_config("main")

for model in app_config.get_models():
	try:
		admin.site.register(model)
	except admin.sites.AlreadyRegistered:
		pass
