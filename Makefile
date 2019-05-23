settings.patch: settings.ini
	mv settings.ini settings-local.ini
	git checkout settings.ini
	! diff settings.ini settings-local.ini > settings.patch
	mv settings-local.ini settings.ini

patch:
	patch settings.ini settings.patch
