# $Id: thumb.py,v 1.4 2006/05/30 09:24:18 stephen Exp $


"""Template for a thumbnail generation program.  This provides a Python
class which you extend to generate a thumbnail image for a type of file.

An example is included which generates thumbnails for text files.  A more
useful implemetation is VideoThumbnail.
"""

import os, sys
import md5

import rox

# Class for thumbnail programs
class Thumbnailler:
    """Base class for programs which generate thumbnails.  You should
    override the method get_image() to create the image.  You can also
    override post_process_image()."""
    def __init__(self, name, fname, use_wdir=False, debug=False):
        """Initialise the thumbnailler.
        name - name of the program
        fname - a string to use in generated temp file names
        use_wdir - if true then use a temp directory to store files
        debug - if false then suppress most error messages
        """
        self.name=name
        self.fname=fname
        self.use_wdir=use_wdir
        self.debug=debug

    def run(self, inname, outname=None, rsize=96):
        """Generate the thumbnail from the file
        inname - source file
        outname - path to store thumbnail image
        rsize - maximum size of thumbnail (in either axis)
        """
        if not outname:
            uri='file://'+inname
            tmp=md5.new(uri).digest()
            leaf=''
            for c in tmp:
                leaf+='%02x' % ord(c)
            outname=os.path.join(os.environ['HOME'], '.thumbnails',
                                 'normal', leaf+'.png')
        elif not os.path.isabs(outname):
            outname=os.path.abspath(outname)

        if self.use_wdir:
            self.make_working_dir()

        try:
            img=self.get_image(inname, rsize)
            ow=img.get_width()
            oh=img.get_height()        
            img=self.process_image(img, rsize)
            self.store_image(img, inname, outname, ow, oh)
        except:
            self.report_exception()

        if self.use_wdir:
            self.remove_working_dir()

    def get_image(self, inname, rsize):
        """Method you must define for your thumbnailler to do anything"""
        raise _("Thumbnail not implemented")

    def process_image(self, img, rsize):
        """Take the raw image and scale it to the correct size.
        Returns the result of scaling img and passing it to
        post_process_image()"""
        ow=img.get_width()
        oh=img.get_height()
        if ow>oh:
            s=float(rsize)/float(ow)
        else:
            s=float(rsize)/float(oh)
        w=int(s*ow)
        h=int(s*oh)

        img=img.scale_simple(w, h, rox.g.gdk.INTERP_BILINEAR)

        return self.post_process_image(img, w, h)

    def post_process_image(self, img, w, h):
        """Perform some post-processing on the image.
        img - gdk-pixbuf of the image
        w - width
        h - height
        Return: modified image
        The default implementation just returns the image unchanged."""
        return img

    def store_image(self, img, inname, outname, ow, oh):
        """Store the thumbnail image it the correct location, adding
        the extra data required by the thumbnail spec."""
        s=os.stat(inname)

        img.save(outname+self.fname, 'png',
             {'tEXt::Thumb::Image::Width': str(ow),
              'tEXt::Thumb::Image::Height': str(oh),
              "tEXt::Thumb::Size": str(s.st_size),
              "tEXt::Thumb::MTime": str(s.st_mtime),
              'tEXt::Thumb::URI': rox.escape('file://'+inname),
              'tEXt::Software': self.name})
        os.rename(outname+self.fname, outname)
        
    def make_working_dir(self):
        """Create the temporary directory and change into it."""
        self.work_dir=os.path.join('/tmp',
                                       '%s.%d' % (self.fname, os.getpid()))
        #print work_dir
        try:
            os.makedirs(self.work_dir)
        except:
            self.report_exception()
            self.work_dir=None
            return

        self.old_dir=os.getcwd()
        os.chdir(self.work_dir)
        
    def remove_working_dir(self):
        """Remove our temporary directory, after changing back to the
        previous one"""
        if not self.work_dir:
            return
        
        os.chdir(self.old_dir)

        for f in os.listdir(self.work_dir):
            path=os.path.join(self.work_dir, f)

            try:
                os.remove(path)
            except:
                self.report_exception()

        try:
            os.rmdir(self.work_dir)
        except:
            self.report_exception()
        
    def report_exception(self):
        """Report an exception (if debug enabled)"""
        if self.debug<1:
            return
        #exc=sys.exc_info()[:2]
        #sys.stderr.write('%s: %s %s\n' % (sys.argv[0], exc[0], exc[1]))
        rox.report_exception()
        
