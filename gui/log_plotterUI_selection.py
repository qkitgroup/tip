from enthought.traits.api import HasTraits, Instance
from enthought.traits.ui.api import View, Item
from enthought.chaco.api import Plot, ArrayPlotData
from chaco.tools.api import PanTool, ZoomTool, DragZoom
from enthought.enable.component_editor import ComponentEditor
import h5py


def measure(l1, l2):
    
    if (l1[0] > l2[0]):
        start = l2[0]
    else:
        start = l1[0]
    if (l1[len(l1) - 1] > l2[len(l2) - 1]):
        end = l1[len(l1) - 1]
    else:
        end = l2[len(l2) - 1]
    
    return [start, end]    
    



def timegrid(start, end, unit, tlist, vlist):
    
    pointnumber = int((end - start)/unit)
    grid = []
    
    vingrid = []
    
    for i in range(0, pointnumber + 1):
        grid.append((i * unit) + start)
        
    for n in grid:
        midvalue = 0
        midnumber = 0
        isin = 0
        for j in range(0,(len(tlist))):
            if ((tlist[j] >= n) and (tlist[j] < (n + unit))):
                midvalue = midvalue + vlist[j]
                midnumber = midnumber + 1
                isin = 1
        if (isin == 1):
            vingrid.append(midvalue/float(midnumber))
            #midvalue = 0
            #midnumber = 0
            #isin = 0
        else:
            vingrid.append('none')
            
    return vingrid
            
                
        
def mfilter(l1,l2):
    rl1 = []
    rl2 = []
    for i in range(0,len(l1)):
        if ((l1[i] != 'none') and (l2[i] != 'none')):
            rl1.append(l1[i])
            rl2.append(l2[i])
    return [rl1, rl2]
    

#if __name__ == '__main__':
#    l1 = [0,1.1,1.2,6.0,6.2,6.3,9.1,9.4]
#    l2 = [0,1,2,3,4,5.2,6,7]
#    
#    l3 = [3,3.1,3.2,6.0,6.2,6.3,9.1,9.4]
#    l4 = [0,1,2,3,4,5.2,6,7]
#    
#startend = measure(l1,l3)
#vlist1 = timegrid(startend[0], startend[1], 3, l1, l2)
#vlist2 = timegrid(startend[0], startend[1], 3, l3, l4)
#result = mfilter(vlist1,vlist2)
#print [vlist1, vlist2]
#print result

class doubleplott(HasTraits):
    plot = Instance(Plot)
    traits_view = View(
        Item('plot',editor=ComponentEditor(), show_label=False),
        width=500, height=500, resizable=True, title='the plot')

    def __init__(self, filename, dataname1, dataname2, unit):
        super(doubleplott, self).__init__()
        
        with h5py.File(filename, 'r') as f:
            vdata1 = f['log'][dataname1].value [1:]
            tdata1 = f['log'][dataname2+'_time'].value [1:]
            vdata2 = f['log'][dataname2].value [1:]
            tdata2 = f['log'][dataname2+'_time'].value [1:]
        
        startend = measure(tdata1, tdata2)
        vlist1 = timegrid(startend[0], startend[1], unit, tdata1, vdata1)
        vlist2 = timegrid(startend[0], startend[1], unit, tdata2, vdata2)
        #print[vlist1]
        #print[vlist2]
        result = mfilter(vlist1,vlist2)
            
        
        plotdata = ArrayPlotData(x = result[0], y = result[1])
        plotm = Plot(plotdata)
        plotm.plot(("x", "y"), type="scatter", color="red")
        plotm.title = dataname1+'-'+dataname2+'-plot'
        self.plot = plotm
        
        plotm.tools.append(PanTool(plotm))
        plotm.tools.append(ZoomTool(plotm))
        plotm.tools.append(DragZoom(plotm, drag_button="right"))

            
if __name__ == "__main__":
    new = doubleplott('/home/j.k./Documents/HiWi/a.h5', 'RandomNumbers', 'RandomNumbers2', 0.05)
    new.configure_traits()    
                      
         
       

    
    
    


