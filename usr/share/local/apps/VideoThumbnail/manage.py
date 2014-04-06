# $Id: manage.py,v 1.2 2008/01/26 15:40:29 stephen Exp $

import os, sys
import tempfile

import rox
import rox.mime
import rox.mime_handler
import rox.loading

import vidthumb

injector_uri='http://www.kerofin.demon.co.uk/2005/interfaces/VideoThumbnail'

class NonLocalFile(EnvironmentError):
    def __str__(self):
        return 'Can only handle local files'

class ManageType(rox.Dialog, rox.loading.XDSLoader):
    def __init__(self):
        rox.Dialog.__init__(self)

        self.set_title(_('VideoThumbnail: Manage type'))

        self.add_button(rox.g.STOCK_CANCEL, rox.g.RESPONSE_CANCEL)

        vbox=self.vbox

        msg=rox.g.Label(_('Drop a sample file here to test thumbnail generation'))
        msg.set_line_wrap(True)
        vbox.pack_start(msg, False, False, 2)

        icon=rox.g.Image()
        icon.set_size_request(128, 128)
        vbox.pack_start(icon, True, True, 2)
        self.icon=icon

        mtype=rox.g.Label('')
        mtype.set_alignment(0.5, 0.5)
        vbox.pack_start(mtype, False, False, 2)
        self.mtype=mtype

        vbox.show_all()

        self.thumb=vidthumb.get_generator(debug=True)

        rox.loading.XDSLoader.__init__(self, None)

        self.connect('response', self.do_response)

    def xds_load_from_stream(self, name, mimetype, stream):
        if name is None:
            raise NonLocalFile()

        if mimetype is None:
            mimetype=rox.mime.get_type(name)

        self.mtype.set_text(_('Type: %s') % str(mimetype))

        strm, ofname=tempfile.mkstemp(suffix='.png')
        #strm.close()

        try:
            self.thumb.run(name, ofname, 128)
        except:
            rox.report_exception()

        try:
            self.icon.set_from_file(ofname)
        except:
            rox.report_exception()

        try:
            os.remove(ofname)
        except:
            pass

        self.add_button(rox.g.STOCK_OK, rox.g.RESPONSE_OK)
        self.mime_type=rox.mime.get_type(name)
        
    def do_response(self, widget, resp):
        if resp==rox.g.RESPONSE_CANCEL:
            self.hide()
            self.destroy()

        elif resp==rox.g.RESPONSE_OK:
            print `self.mime_type`
            self.set_handler(self.mime_type)

    def set_handler(self, mtype):
        rox.mime_handler.install_thumbnailer((str(mtype),),
                                             injint=injector_uri)

