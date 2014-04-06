#!/usr/bin/env python
#
# $Id: vidthumb.py,v 1.25 2008/03/26 19:21:11 stephen Exp $

"""Generate thumbnails for video files.  This must be called as
      vidthumb.py source_file destination_thumbnail maximum_size
where maximum_size is the maximum width and height.

This uses mplayer to grab a single frame as a .png file, then gdk-pixbuf (via
pygtk 1.99.x) to generate a thumbnail of that frame.  A film strip effect is
added to mark the thumbnail as from a video file.

To use this in ROX-Filer, get a recent version then run VideoThumbnail and
click on "Install handlers".  Generating a video thumbnail takes a lot longer
than a simple image file, but ROX-Filer remains responsive while it is
being processed.
"""

import os, sys
import md5
import rox, rox.mime, rox.thumbnail
import pango

import thumb

# Defaults
import options

outname=None
rsize=options.tsize.int_value
take_first=options.take_first.int_value

# Width of the film strip effect to put at each side
bwidth=options.ssize.int_value

# How best to select the frame for a given type.  Worked out by trial and error
first_by_types={
    'video/mpeg': True,
    'video/x-ms-wmv': False
}

def binaryInPath(b):
    for path in os.environ["PATH"].split(":"):
        if os.access(os.path.join(path, b), os.R_OK | os.X_OK):
            return True
    return False

def execute_return_err(cmd):
    errmsg=""
    cin, cout=os.popen4(cmd, 'r')
    cin.close()
    for l in cout:
        errmsg+=l
    cout.close()
    #cerr.close()
    if debug: print cmd, errmsg
    if errmsg:
        return errmsg
        
debug=os.environ.get('VIDTHUMB_DEBUG', 0)

class VidThumbNail(rox.thumbnail.Thumbnailer):
    """Generate thumbnail for video files understood by totem"""
    def __init__(self, debug=False):
        """Initialize Video thumbnailer"""
        rox.thumbnail.Thumbnailer.__init__(self, 'VideoThumbnail', 'vidthumb',
                                    True, debug)

    def failed_image(self, rsize, tstr):
        if debug: print 'failed_image', self, rsize, tstr
        if not tstr:
            tstr=_('Error!')
        w=rsize
        h=rsize/4*3
        try:
            p=rox.g.gdk.Pixbuf(rox.g.gdk.COLORSPACE_RGB, False, 8, w, h)
        except:
            sys.exit(2)
        if debug: print p

        pixmap, mask=p.render_pixmap_and_mask()
        cmap=pixmap.get_colormap()
        gc=pixmap.new_gc(foreground=cmap.alloc_color('black'))
        gc.set_foreground(gc.background)

        if debug: print gc, gc.foreground
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)
        
        gc.set_foreground(cmap.alloc_color('red'))
        dummy=rox.g.Window()
        layout=dummy.create_pango_layout(tstr)
        if w>40:
            layout.set_width((w-10)*pango.SCALE)
            #layout.set_wrap(pango.WRAP_CHAR)
        pixmap.draw_layout(gc, 10, 4, layout)
        if debug: print pixmap

        self.add_time=False
        
        return p.get_from_drawable(pixmap, cmap, 0, 0, 0, 0, -1, -1)

    def check_executable(cls):
        try:
            return binaryInPath(cls._binary)
        except Exception, e:
            if debug:
                print e
            return False
    check_executable = classmethod(check_executable)
        
        

class VidThumbTotem(VidThumbNail):
    """Generate thumbnail for video files understood by totem"""
    _binary = "totem-video-thumbnailer"
    def __init__(self, debug=False):
        """Initialize Video thumbnailler"""
        VidThumbNail.__init__(self, debug)


    def get_image(self, inname, rsize):
        outfile = os.path.join(self.work_dir, "out.png")
        if options.scale.int_value:
            cmd = 'totem-video-thumbnailer -s %i \"%s\" %s' % (rsize, inname, outfile)
        else:
            cmd = 'totem-video-thumbnailer \"%s\" %s' % (inname, outfile)
        errmsg=execute_return_err(cmd)
        if not os.path.exists(outfile):
            return self.failed_image(rsize, errmsg)

        # Now we load the raw image in
        return rox.g.gdk.pixbuf_new_from_file(outfile)


class VidThumbMPlayer(VidThumbNail):
    """Generate thumbnail for video files understood by mplayer"""
    _binary = "mplayer"
    def __init__(self, debug=False):
        """Initialize Video thumbnailler"""
        VidThumbNail.__init__(self, debug)

        self.add_time=options.time_label.int_value
        self.right_align=options.right_align.int_value

    def post_process_image(self, img, w, h):
        """Add the optional film strip effect"""

        if not options.sprocket.int_value and not self.add_time:
            return img
        
        pixmap, mask=img.render_pixmap_and_mask()
        cmap=pixmap.get_colormap()
        gtk=rox.g
        gc=pixmap.new_gc(foreground=cmap.alloc_color('black'))
            
        if options.sprocket.int_value:
            # Draw the film strip effect
            pixmap.draw_rectangle(gc, True, 0, 0, 8, h)
            pixmap.draw_rectangle(gc, True, w-8, 0, 8, h)

            gc.set_foreground(cmap.alloc_color('#DDD'))
            for y in range(1, h, 8):
                pixmap.draw_rectangle(gc, True, 2, y, 4, 4)
                pixmap.draw_rectangle(gc, True, w-8+2, y, 4, 4)

        if self.add_time and self.total_time:
            secs=self.total_time
            hours=int(secs/3600)
            if hours>0:
                secs-=hours*3600
            mins=int(secs/60)
            if mins>0:
                secs-=mins*60
            tstr='%d:%02d:%02d' % (hours, mins, secs)
            if debug: print tstr
            dummy=gtk.Window()
            layout=dummy.create_pango_layout(tstr)

            xpos=10
            if self.right_align:
                lw, lh=layout.get_pixel_size()
                xpos=w-xpos-lw
            gc.set_foreground(cmap.alloc_color('black'))
            pixmap.draw_layout(gc, xpos+1, 5, layout)
            gc.set_foreground(cmap.alloc_color('white'))
            pixmap.draw_layout(gc, xpos, 4, layout)
            if debug: print layout
                               
        return img.get_from_drawable(pixmap, cmap, 0, 0, 0, 0, -1, -1)


    def get_image(self, inname, rsize):
        """Generate the raw image from the file.  We run mplayer (twice)
        to do the hard work."""
        #print self.work_dir
        def get_length(fname):
            """Get the length in seconds of the source. """
            # -frames 0 might be needed on debian systems
            unused, inf, junk=os.popen3(
                'mplayer -frames 0 -vo null -vf-clr -ao null -identify "%s"' % fname,
                'r')

            for l in inf.readlines():
                # print l[:10]
                if l[:10]=='ID_LENGTH=':
                    return float(l.strip()[10:])
                
            return 0.

        def write_frame(fname, pos):
            """Return filename of a single frame from the source, taken 
            from pos seconds into the video"""

            # Ask for 3 frames.  Seems to work better
            cmd='mplayer -really-quiet -vo png -vf-clr -ss %f -frames 3 -nosound -noloop "%s"' % (pos, fname)
            cmd+=' > /dev/null 2>&1'

            # If we have 2 frames ignore the first and return the second, else
            # if we have 1 return it.  Otherwise mplayer couldn't cope and we
            # return None
            def frame_ok(ofile):
                if debug: print 'look for', ofile
                try:
                    os.stat(ofile)
                except:
                    if debug: print 'exception', sys.exc_info()[:2]
                    if debug: os.system('pwd')
                    if debug: os.system('ls -al')
                    return False
                return True

            if debug: print cmd
            os.system(cmd)

            mtype=rox.mime.get_type(fname)
            #print >>sys.stderr, mtype, first_by_types
            try:
                #print >>sys.stderr, str(mtype)
                first=first_by_types[str(mtype)]
            except:
                #print >>sys.stderr, 'oops'
                first=take_first
            #print >>sys.stderr, first
            
            if first:
                id=1
            else:
                id=2
            ofile='%08d.png' % id
            if debug: print ofile
            if not frame_ok(ofile):
                if not first:
                    id=1
                    ofile='%08d.png' % id
                    if not frame_ok(ofile):
                        ofile=None
                else:
                    ofile=None
                
            return ofile

        try:
            vlen=get_length(inname)
        except:
            self.report_exception()
            return self.failed_image(rsize, _('Bad length'))
        os.wait()

        self.total_time=vlen
        if debug: print vlen
    
        # Select a frame 5% of the way in, but not more than 60s  (Long files
        # usually have a fade in).
        pos=vlen*0.05
        if pos>60:
            pos=60

        frfname=write_frame(inname, pos)
        if debug: print inname, pos, frfname
        if frfname is None:
            frfname=write_frame(inname, 0)
            if debug: print inname, pos, frfname
        if frfname is None:
            # Yuck
            try:
                raise _('Bad or missing frame file')
            except:
                self.report_exception()
            return self.failed_image(rsize, _('Bad or missing frame file'))

        # Now we load the raw image in

        return rox.g.gdk.pixbuf_new_from_file(frfname)

thumbnailers = {"mplayer": VidThumbMPlayer,
                "totem" : VidThumbTotem }

def get_generator(debug=None):
    """Return the current generator of thumbnails"""
    copy=dict(thumbnailers)
    thumbC = copy.pop(options.generator.value)
    if not thumbC.check_executable():
        origbin = thumbC._binary
        for (name, cls) in copy.iteritems():
            if cls.check_executable():
                thumbC = cls
                msg = _("""VideoThumbnail could not find the program "%s", but another thumbnail generator is available.
                
Should "%s" be used from now on?""")
                if rox.confirm(msg % (origbin, thumbC._binary), rox.g.STOCK_YES):
                    options.generator.value = name
                    rox.app_options.save()
                    pass
                break
        else:
            msg = _("""VideoThumbnail could not find any usable thumbnail generator.
            
You need to install either MPlayer (http://www.mplayerhq.hu)
or Totem (http://www.gnome.org/projects/totem/).""")
            rox.croak(msg)

    if debug is None:
        debug=options.report.int_value
    #print debug
    return thumbC(debug)

def main(argv):
    """Process command line args.  Although the filer always passes three args,
    let the last two default to something sensible to allow use outside
    the filer."""
    global rsize, outname
    
    #print argv
    inname=argv[0]
    try:
        outname=argv[1]
    except:
        pass
    if debug: print 'save to', outname
    try:
        rsize=int(argv[2])
    except:
        pass

    orig=inname
    #if os.path.islink(inname):
    #    inname=os.readlink(inname)
    if not os.path.isabs(inname):
        inname=os.path.join(os.path.dirname(orig), inname)

    # Out file name is based on MD5 hash of the URI
    if not outname:
        uri='file://'+inname
        tmp=md5.new(uri).digest()
        leaf=''
        for c in tmp:
            leaf+='%02x' % ord(c)
        outname=os.path.join(os.environ['HOME'], '.thumbnails', 'normal',
                         leaf+'.png')
    elif not os.path.isabs(outname):
        outname=os.path.abspath(outname)
    if debug: print 'save to', outname
    #print inname, outname, rsize

    thumb=get_generator()
    thumb.run(inname, outname, rsize)

        
def configure():
    """Configure the app"""
    options.edit_options()
    rox.mainloop()

if __name__=='__main__':
    main(sys.argv[1:])
