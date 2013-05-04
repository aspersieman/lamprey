.PHONY: all clean install uninstall

all:
	@echo "It's all there, just an ls away!"

clean:
	rm -f *~

install:
	mkdir -p $(DESTDIR)/usr/share/lamprey/
	cp lamprey.py running.png stopped.png lamprey.svg $(DESTDIR)/usr/share/lamprey/
	mkdir -p $(DESTDIR)/usr/share/doc/lamprey/
	cp AUTHORS COPYING README $(DESTDIR)/usr/share/doc/lamprey/
	test -d $(DESTDIR)/usr/bin/ || mkdir -p $(DESTDIR)/usr/bin/

	# A symbolic link isn't the same... The absolute path is stored into
	# it, so my computer's path would remain into it; a script seems a
	# better choice.
	#ln -s $(DESTDIR)/usr/share/lamprey/lamprey.py $(DESTDIR)/usr/bin/lamprey
	echo /usr/share/lamprey/lamprey.py > $(DESTDIR)/usr/bin/lamprey
	chmod +x $(DESTDIR)/usr/bin/lamprey

	test -d $(DESTDIR)/usr/share/applications/ || mkdir -p $(DESTDIR)/usr/share/applications/
	cp lamprey.desktop $(DESTDIR)/usr/share/applications/
	update-desktop-database || true

uninstall:
	rm -f $(DESTDIR)/usr/bin/lamprey
	rm -fr $(DESTDIR)/usr/share/lamprey/
	rm -fr $(DESTDIR)/usr/share/doc/lamprey/
	rm -f $(DESTDIR)/usr/share/applications/lamprey.desktop
	update-desktop-database || true
