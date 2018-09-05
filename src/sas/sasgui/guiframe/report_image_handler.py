import wx


class ReportImageHandler:


    class _ReportImageHandler:

        def __init__(self):
            self.img_holder = wx.MemoryFSHandler()
            wx.FileSystem.AddHandler(wx.MemoryFSHandler())
            self.refs = {}
            self.indices = []

        def set_figs(self, figs, bitmaps, perspective):
            imgs = []
            refs = []
            if figs is None or len(figs) == 0:
                figs = [None]
            for fig in figs:
                if fig is not None:
                    ind = figs.index(fig)
                    bitmap = bitmaps[ind]

                # name of the fig
                name = self.create_unique_name(perspective)
                # AddFile, image can be retrieved with 'memory:filename'
                ref = 'memory:' + name
                self.refs[ref] = fig
                self.img_holder.AddFile(name, bitmap, wx.BITMAP_TYPE_PNG)
                refs.append(ref)
                imgs.append(fig)
            return imgs, refs

        def create_unique_name(self, perspective, index=None):
            if not index:
                index = len(self.indices)
            if index in self.indices:
                name = self.create_unique_name(index + 1)
            else:
                self.indices.append(index)
                name = 'img_{}_{:03d}.png'.format(str(perspective), index)
            return name


    instance = None

    def __init__(self):
        if not ReportImageHandler.instance:
            ReportImageHandler.instance = ReportImageHandler._ReportImageHandler()
