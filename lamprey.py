#! /usr/bin/python2.7


# Handy tray icon to manage the LAMP services (Apache + MySQL) on
# Ubuntu and Debian systems with a single mouse click.
#
# by Paolo Bernardi <villa.lobos@tiscali.it>
# forked by Nicol van der Merwe <aspersieman@gmail.com>

import gtk
import os
import subprocess
import shlex
import sys
import glib


class LampRey():
    def __init__(self):
        errors = self.check_environment()

        if errors:
            m = gtk.MessageDialog(
                type=gtk.MESSAGE_ERROR,
                buttons=gtk.BUTTONS_CLOSE,
                message_format=errors)
            m.set_title("Something's wrong...")
            m.run()
            m.destroy()

        self.status_icon = gtk.StatusIcon()
        self.status_icon.connect("popup-menu", self.on_click)
        self.status = self.analyze_status()
        self.toggled = self.status["is_running"]
        self.update_icon(self.status)
        glib.timeout_add_seconds(2, self.handler_timeout)

    def handler_timeout(self):
        """This will be called every few seconds by the GLib.timeout.
        """
        self.update_icon(self.analyze_status())
        #self.watcher.loop(async=True)
        # return True so that we get called again
        # returning False will make the timeout stop
        return True

    def check_root(self):
        """Check if the current user is root, if not change the script to run
        as root"""
        euid = os.geteuid()
        if euid != 0:
            args = ['gksudo', sys.executable] + sys.argv + [os.environ]
            # the next line replaces the currently-running process with the
            # sudo
            os.execlpe('gksudo', *args)

    def analyze_status(self):
        """Analyzes the LAMP services status.
        Returns a dictionary with the following informations:
        - "is_running": True if every LAMP service is up, False otherwise;
        - "icon": a confirmation icon if every LAMP service is running,
                a warning icon if some LAMP service is down,
            an error icon if every LAMP service is down;
        - "text": a text caption describing the LAMP services status.
        """

        pa = subprocess.Popen(shlex.split("service apache2 status"),
                              shell=False, stdout=subprocess.PIPE)
        self.apache2 = pa.stdout.read().find(' NOT ') == -1
        print "apache2 ", str(self.apache2)
        #pm = subprocess.Popen(shlex.split("service mysql status"),
        #                      shell=False, stdout=subprocess.PIPE)
        #self.mysql = pm.stdout.read().find('mysql') != -1
        pm = subprocess.Popen(shlex.split("mysqladmin -umysql ping"),
                              shell=False, stdout=subprocess.PIPE)
        self.mysql = pm.stdout.read().find("mysqld is alive") != -1
        print "MySQL ", str(self.mysql)

        if self.apache2:
            text = "Apache is running\n"
        else:
            text = "Apache is NOT running\n"
        if self.mysql:
            text += "MySQL is running"
        else:
            text += "MySQL is NOT running"

        if self.apache2 and self.mysql:
            return {"is_running": True, "icon": gtk.STOCK_YES, "text": text}
        elif self.apache2 or self.mysql:
            return {"is_running": False, "icon": gtk.STOCK_DIALOG_WARNING,
                    "text": text}
        else:
            return {"is_running": False, "icon": gtk.STOCK_STOP, "text": text}

    def update_icon(self, status):
        """Updates the tray icon and its popup text depending on the LAMP
        services status.
        The parameter status is the dictionary returned from analyze_status.
        """
        self.status_icon.set_from_stock(status["icon"])
        self.status_icon.set_tooltip_text(status["text"])

    def start_stop_all(self, event_button):
        """Acts upon a user click on the tray icon, alternating start and stop
        of every LAMP service."""
        self.start_stop("all")

    def start_stop_apache(self, event_button):
        """Starts or stops the apache2 service."""
        self.start_stop("apache")

    def start_stop_mysql(self, event_button):
        """Starts or stops the mysql service."""
        self.start_stop("mysql")

    def start_stop(self, service="all"):
        """Starts and stops the appropriate service."""
        self.status = self.analyze_status()
        s = self.toggled and "stop" or "start"
        # Apparently, service apache2 start/stop doesn't work if not run in
        # a terminal apache2ctl works anyway, so I used it
        #subprocess.call(shlex.split("apache2ctl %s" % s))
        #subprocess.call(shlex.split("service mysql %s" % s))
        if service == "all":
            cmd = "gksudo \"bash -c 'service apache2 %s \
            && service mysql %s'\"" % (s, s)
        elif service == "apache":
            cmd = "gksudo \"bash -c 'service apache2 %s \"" % s
        elif service == "mysql":
            cmd = "gksudo \"bash -c 'service mysql %s \"" % s
        subprocess.call(shlex.split(cmd))
        self.update_icon(self.analyze_status())
        self.toggled = not self.toggled

    def package_installed(self, package):
        """Returns True if package is installed, False otherwise."""

        pa = subprocess.Popen(shlex.split("dpkg -l " + package), shell=False,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return pa.stderr.read().find(
            "No packages found matching " + package) == -1

    def check_environment(self):
        """Checks if the environment is good (LAMP services are there?
        Python and GTK versions are correct?).
        If there's something wrong returns a message about it, otherwise
        returns an empty string.
        """

        messages = []

        if sys.version_info[0] != 2 or sys.version_info[1] < 6:
            messages.append(
                "Python 2.6 or greater is needed (but not Python 3).")

        if gtk.gtk_version[0] < 2 or gtk.gtk_version[1] < 10:
            messages.append("GTK 2.10 or greater is needed.")

        if not self.package_installed("apache2"):
            messages.append("You need to install apache2")

        if not self.package_installed("mysql-server"):
            messages.append("You need to install mysql-server")

        return "\n".join(messages)

    def on_click(self, icon, event_button, event_time):
        """ Executes the on click command of the tray icon."""
        self.status = self.analyze_status()
        self.update_icon(self.status)
        self.make_menu(event_button, event_time)

    def make_menu(self, event_button, event_time):
        menu = gtk.Menu()

        # add start/stop all item
        if self.apache2 and self.mysql:
            start_stop_text = "Stop All"
            start_stop_icon = gtk.STOCK_MEDIA_STOP
        else:
            start_stop_text = "Start All"
            start_stop_icon = gtk.STOCK_MEDIA_PLAY
        start_stop_all = gtk.ImageMenuItem(start_stop_icon)
        start_stop_all.set_label(start_stop_text)
        start_stop_all.show()
        menu.append(start_stop_all)
        start_stop_all.connect('activate', self.start_stop_all)

        # add start/stop Apache item
        if self.apache2:
            start_stop_apache_text = "Stop Apache"
            start_stop_apache_icon = gtk.STOCK_MEDIA_STOP
        else:
            start_stop_apache_text = "Start Apache"
            start_stop_apache_icon = gtk.STOCK_MEDIA_PLAY
        start_stop_apache = gtk.ImageMenuItem(
            start_stop_apache_icon, start_stop_apache_text)
        start_stop_apache = gtk.ImageMenuItem(start_stop_apache_icon)
        start_stop_apache.set_label(start_stop_apache_text)
        start_stop_apache.show()
        menu.append(start_stop_apache)
        start_stop_apache.connect('activate', self.start_stop_apache)

        # add start/stop MySQL item
        if self.mysql:
            start_stop_mysql_text = "Stop MySQL"
            start_stop_mysql_icon = gtk.STOCK_MEDIA_STOP
        else:
            start_stop_mysql_text = "Start MySQL"
            start_stop_mysql_icon = gtk.STOCK_MEDIA_PLAY
        start_stop_mysql = gtk.ImageMenuItem(
            start_stop_mysql_icon, start_stop_mysql_text)
        start_stop_mysql = gtk.ImageMenuItem(
            start_stop_mysql_icon, start_stop_mysql_text)
        start_stop_mysql.set_label(start_stop_mysql_text)
        start_stop_mysql.show()
        menu.append(start_stop_mysql)
        start_stop_mysql.connect('activate', self.start_stop_mysql)

        # show about dialog
        about = gtk.ImageMenuItem(gtk.STOCK_ABOUT, 'About')
        about.show()
        menu.append(about)
        about.connect('activate', self.show_about_dialog)

        # add quit item
        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT, 'Quit')
        quit.show()
        menu.append(quit)
        quit.connect('activate', gtk.main_quit)

        menu.popup(None, None, gtk.status_icon_position_menu, event_button,
                   event_time, self.status_icon)

    def show_about_dialog(self, widget):
        about_dialog = gtk.AboutDialog()
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_icon_name('LAMP Icon')
        about_dialog.set_name('LAMP Icon')
        about_dialog.set_version('0.1b')
        comments = u"Handy tray icon to manage the LAMP services "
        comments += u"(Apache + MySQL) on Debian/Ubuntu"
        about_dialog.set_comments(comments)
        about_dialog.set_authors(
            [u'Paolo Bernardi <villa.lobos@tiscali.it>',
             'Nicol van der Merwe <aspersieman@gmail.com>'])
        about_dialog.run()
        about_dialog.destroy()


if __name__ == "__main__":
    LampRey()
    gtk.main()
