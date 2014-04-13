"""Handle the options for the video thumbnailler"""

# $Id: options.py,v 1.19 2008/01/26 15:40:29 stephen Exp $

import os

import rox
import rox.options
import rox.OptionsBox
import rox.mime
import rox.mime_handler
import rox.AppInfo

import manage

rox.setup_app_options('VideoThumbnail', site='kerofin.demon.co.uk')

tsize=rox.options.Option('tsize', 128)
sprocket=rox.options.Option('sprocket', 1)
ssize=rox.options.Option('ssize', 8)
time_label=rox.options.Option('time', 0)
right_align=rox.options.Option('ralign', 0)
report=rox.options.Option('report', 0)
take_first=rox.options.Option('take_first', False)
generator=rox.options.Option('generator', 'mplayer')
scale=rox.options.Option('scale', False)

rox.app_options.notify()

def install_button_handler(*args):
    try:
        rox.mime_handler.install_from_appinfo(injint=manage.injector_uri)
                
    except:
        rox.report_exception()

def build_install_button(box, node, label):
    #print box, node, label
    button = rox.g.Button(label)
    box.may_add_tip(button, node)
    button.connect('clicked', install_button_handler)
    return [button]

def manage_type_button_handler(*args):
    w=manage.ManageType()
    w.show()

def build_manage_type_button(box, node, label):
    #print box, node, label
    button = rox.g.Button(label)
    box.may_add_tip(button, node)
    button.connect('clicked', manage_type_button_handler)
    return [button]

rox.OptionsBox.widget_registry['install-button'] = build_install_button
rox.OptionsBox.widget_registry['manage-type-button'] = build_manage_type_button
        
def edit_options():
    rox.edit_options()
