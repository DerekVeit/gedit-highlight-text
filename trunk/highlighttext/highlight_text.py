# -*- coding: utf8 -*-
#  Highlight Text plugin for Gedit
#
#  Copyright (C) 2010 Derek Veit
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module provides the plugin object that Gedit interacts with.

Classes:
HighlightTextPlugin -- object is loaded once by an instance of Gedit
HighlightTextWindowHelper -- object is constructed for each Gedit window

Each time the same Gedit instance makes a new window, Gedit calls the plugin's
activate method.  Each time HighlightTextPlugin is so activated, it constructs
a HighlightTextWindowHelper object to handle the new window.

Settings common to all Gedit windows are attributes of HighlightTextPlugin.
Settings specific to one window are attributes of HighlightTextWindowHelper.

"""

import logging
import os
import sys

import gedit
import gtk

class HighlightTextPlugin(gedit.Plugin):
    
    """
    An object of this class is loaded once by a Gedit instance.
    
    It establishes and maintains the configuration data, and it creates a
    HighlightTextWindowHelper object for each Gedit main window.
    
    Public methods:
    activate -- Gedit calls this to start the plugin.
    deactivate -- Gedit calls this to stop the plugin.
    update_ui -- Gedit calls this at certain times when the ui changes.
    is_configurable -- Gedit calls this to check if the plugin is configurable.
    
    """
    
    def __init__(self):
        """Establish the settings shared by all Highlight Text instances."""
        
        gedit.Plugin.__init__(self)
        
        self.logger = logging.getLogger('highlight_text')
        handler = logging.StreamHandler(sys.stdout)
        log_format = "%(levelname)s - %(message)s"
        #log_format = "%(asctime)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)
        self.log('Highlight Text logging started. '.ljust(72, '-'))
        self.log()
        
        self._instances = {}
        """Each Gedit window will get a HighlightTextWindowHelper instance."""
    
    def activate(self, window):
        """Start a HighlightTextWindowHelper instance for this Gedit window."""
        self.log()
        self._instances[window] = HighlightTextWindowHelper(self, window)
    
    def deactivate(self, window):
        """End the HighlightTextWindowHelper instance for this Gedit window."""
        self.log()
        self._instances[window].deactivate()
        del self._instances[window]
    
    def update_ui(self, window):
        """Forward Gedit's update_ui command for this window."""
        self.log()
        self._instances[window].update_ui(window)
    
    def is_configurable(self):
        """Identify for Gedit that Highlight Text is not configurable."""
        self.log()
        return False
    
    def log(self, message=None, level='info'):
        """Log the message or log the calling function."""
        if message:
            logger = {'debug': self.logger.debug,
                      'info': self.logger.info,
                      'warning': self.logger.warning,
                      'error': self.logger.error,
                      'critical': self.logger.critical}[level]
            logger(message)
        else:
            self.logger.debug(self._whoami())
    
    def _whoami(self):
        """Identify the calling function for logging."""
        filename = os.path.basename(sys._getframe(2).f_code.co_filename)
        line = sys._getframe(2).f_lineno
        class_name = sys._getframe(2).f_locals['self'].__class__.__name__
        function_name = sys._getframe(2).f_code.co_name
        return '%s Line %s %s.%s' % (filename, line, class_name, function_name)

class HighlightTextWindowHelper(object):
    
    """
    HighlightTextPlugin creates a HighlightTextWindowHelper object for each Gedit
    window.
    
    Public methods:
    deactivate -- HighlightTextPlugin calls this when Gedit calls deactivate for
                  this window.
    update_ui -- HighlightTextPlugin calls this when Gedit calls update_ui for
                 this window.  It activates the menu for the Gedit window and
                 connects the mouse event handler to the current View.
                 Also, HighlightTextWindowHelper.__init__ calls this.
    
    """
    
    def __init__(self, plugin, window):
        """Establish the circumstances of this Highlight Text instance."""
        
        self._window = window
        """The window this HighlightTextWindowHelper runs on."""
        self._plugin = plugin
        """The HighlightTextPlugin that spawned this HighlightTextWindowHelper."""
        
        self._plugin.log()
        self._plugin.log('Started for %s' % self._window)
        
        self._ui_id = None
        """The menu's UI identity, saved for removal."""
        self._action_group = None
        """The menu's action group, saved for removal."""
        
        self._insert_menu()
        
        self.update_ui(self._window)
        
    
    def _insert_menu(self):
        """Create the custom menu item under the Search menu."""
        self._plugin.log()

        manager = self._window.get_ui_manager()
        
        name = 'HighlightText'
        stock_id = None
        label = 'Highlight Text'
        accelerator = '<Shift><Control>f'
        tooltip = 'Highlight all occurances of the text currently selected.'
        callback = self._highlight_selection

        actions = [
            (name, stock_id, label, accelerator, tooltip, callback),
            ]
        self._action_group = gtk.ActionGroup("HighlightTextPluginActions")
        self._action_group.add_actions(actions)
        manager.insert_action_group(self._action_group, -1)
        
        ui_str = """
            <ui>
              <menubar name="MenuBar">
                <menu name="SearchMenu" action="Search">
                  <placeholder name="SearchOps_1">
                    <placeholder name="HighlightText">
                      <separator />
                      <menuitem action="HighlightText"/>
                    </placeholder>
                  </placeholder>
                </menu>
              </menubar>
            </ui>
            """
        self._ui_id = manager.add_ui_from_string(ui_str)
    
        self._plugin.log('Menu added for %s' % self._window)
    
    def _remove_menu(self):
        """Remove the custom menu item."""
        self._plugin.log()
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()
        self._plugin.log('Menu removed for %s' % self._window)
    
    def deactivate(self):
        """End this instance of Highlight Text."""
        self._plugin.log()
        self._plugin.log('Stopping for %s' % self._window)
        self._remove_menu()
        self._action_group = None
        self._plugin = None
        self._window = None
    
    def update_ui(self, window):
        """Activate the custom menu."""
        self._plugin.log()
        doc = self._window.get_active_document()
        current_view = self._window.get_active_view()
        if doc and current_view and current_view.get_editable():
            self._action_group.set_sensitive(True)
    
    # Text functions:
    
    def _highlight_selection(self, action):
        """Highlight all occurances of the currently selected text."""
        self._plugin.log()
        doc = self._window.get_active_document()
        text = self._get_text_selection()
        #flags = gedit.SEARCH_DONT_SET_FLAGS
        flags = gedit.SEARCH_CASE_SENSITIVE
        #flags |= gedit.SEARCH_ENTIRE_WORD
        doc.set_search_text(text, flags)
    
    def _get_text_selection(self):
        """Return the currently selected text."""
        self._plugin.log()
        doc = self._window.get_active_document()
        if doc.get_has_selection():
            start_iter, end_iter = doc.get_selection_bounds()
            selected_text = doc.get_text(start_iter, end_iter)
        else:
            selected_text = ''
        return selected_text
    

