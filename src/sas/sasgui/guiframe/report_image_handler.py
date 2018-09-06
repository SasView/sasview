import wx


class ReportImageHandler:
    # Singleton class that manages all report plot images
    # To call the handler, call the static method set_figs

    class _ReportImageHandler:

        def __init__(self):
            self.img_holder = wx.MemoryFSHandler()
            wx.FileSystem.AddHandler(wx.MemoryFSHandler())
            self.refs = {}
            self.indices = []

        def set_figs(self, figs, bitmaps, perspective):
            """
            Save figures and images to memory and return refernces
            :param figs: A list of matplotlib Figures
            :param bitmaps: A list of bitmaps
            :param perspective: A String with the perspective name
            :return: A tuple of a list of Figures and a list of memory refs
            """
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
            """
            Create a unique key for each item in memory
            :param perspective: The perspective name as a string
            :param index: The base index used for incrementing the name
            :return: A unique file name not currently in use
            """
            if not index:
                index = len(self.indices)
            if index in self.indices:
                name = self.create_unique_name(index + 1)
            else:
                self.indices.append(index)
                name = 'img_{}_{:03d}.png'.format(str(perspective), index)
            return name

    instance = None

    @staticmethod
    def set_figs(figs, bitmaps, perspective):
        if not ReportImageHandler.instance:
            ReportImageHandler.instance = ReportImageHandler._ReportImageHandler()
        return ReportImageHandler.instance.set_figs(figs, bitmaps, perspective)
