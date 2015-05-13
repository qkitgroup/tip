from enthought.traits.api import HasTraits, Instance
from enthought.traits.ui.api import View, Item
from enthought.chaco.api import Plot, ArrayPlotData
from chaco.tools.api import PanTool, ZoomTool, DragZoom
from enthought.enable.component_editor import ComponentEditor
import h5py

class plott(HasTraits):
    plot = Instance(Plot)
    traits_view = View(
        Item('plot',editor=ComponentEditor(), show_label=False),
        width=500, height=500, resizable=True, title='the plot')

    def __init__(self, filename, dataname):
        super(plott, self).__init__()
        
        with h5py.File(filename, 'r') as f:
            tdata = f['log'][dataname+'_time'].value [1:]
            vdata = f['log'][dataname].value [1:]
            
        
        plotdata = ArrayPlotData(x = tdata, y = vdata)
        plotm = Plot(plotdata)
        plotm.plot(("x", "y"), type="scatter", color="red")
        plotm.title = dataname+'-plot'
        self.plot = plotm
        
        plotm.tools.append(PanTool(plotm))
        plotm.tools.append(ZoomTool(plotm))
        plotm.tools.append(DragZoom(plotm, drag_button="right"))