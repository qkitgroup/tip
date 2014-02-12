from traits.api import HasTraits, List, Instance, Str, on_trait_change, Button, Float
from traitsui.api import Item, Group, View, CheckListEditor, Label
import h5py

import plotter
import selection
import Data_class

class plot_choice(HasTraits): 
    
    data = Data_class.Data()
    Draw = Button
            
    myfile = h5py.File(data.hdf_path,'r')
    mlist = []
    
    for i in myfile['log']:
        if '_time' not in i:
            mlist.append(i)
    

    checklist = List(editor = CheckListEditor(values = mlist), label = 'Items to plot')
    show = Item('checklist', style = 'custom')
    traits_view = View(show, Item(name='Draw'), 
                    title = 'HDF-Plotter', 
                    buttons = ['Cancel'], 
                    resizable = True)
    
    @on_trait_change('Draw')
    def do_plot(self):
        for i in self.checklist:
            new = plotter.plott(self.data.hdf_path,i)
            new.configure_traits()
            
          
class double_plot_choice(HasTraits):
    
    data = Data_class.Data()
    Unit = Float(1.0)
    Draw = Button 
    
    myfile = h5py.File(data.hdf_path,'r')
    mlist = []
    
    for i in myfile['log']:
        if '_time' not in i:
            mlist.append(i)
    
    hdf_content1 = List(editor = CheckListEditor(values = mlist))
    hdf_content2 = List(editor = CheckListEditor(values = mlist))
    show1 = Item('hdf_content1', style = 'simple', label = "1st item")
    show2 = Item('hdf_content2', style = 'simple', label = '2nd item')
    show3 = Item('Unit', label = 'time unit /s')
    traits_view = View(show1, show2, show3, Item(name = 'Draw'))
        
    @on_trait_change('Draw')    
    def return_choice(self):
        if (len(self.hdf_content1) > 0 and len(self.hdf_content2) > 0):
            plotlist = [self.hdf_content1[0], self.hdf_content2[0], self.Unit]
        elif (len(self.hdf_content1) > 0 and len(self.hdf_content2) == 0):
            plotlist = [self.hdf_content1[0], self.mlist[0], self.Unit]       
        elif (len(self.hdf_content1) == 0 and len(self.hdf_content2) > 0):
            plotlist = [self.mlist[0], self.hdf_content2[0], self.Unit]
        else:
            plotlist = [self.mlist[0], self.mlist[0], self.Unit]
            
        new = selection.doubleplott(self.data.hdf_path, 
                                    plotlist[0], 
                                    plotlist[1], 
                                    plotlist[2])
        new.configure_traits() 
    
            
            
class draw_class(HasTraits):
    
    Parameters = Instance(double_plot_choice)
    B = Instance(plot_choice)
    
    def __init__(self):
        self.Parameters = double_plot_choice()
        self.B = plot_choice()
    
    view = View(Item(name = 'Parameters', style = 'custom', label = 'Correlation plot'),
                Item(name = 'B', style = 'custom', label = 'Data-time plot'), 
                title = 'Select data to plot', 
                buttons = ['Cancel'],
                resizable = True)
    
    #def now_plot(self):
    #    new = selection.doubleplott('/home/j.k./Documents/HiWi/a.h5', 
    #                                self.Parameters.return_choice()[0], 
    #                                self.Parameters.return_choice()[1], 
    #                                self.Parameters.return_choice()[2])
    #    new.configure_traits()
        #print self.A.return_choice()         
    
if __name__ == '__main__':
    #demo = plot_choice()
    #demo.configure_traits()
    mfile = draw_class()
    mfile.configure_traits()
    #mfile.now_plot()
    #print demo.return_choice()
    #for i in demo.return_choice():
    #    new = plotter.plott('/home/j.k./Documents/HiWi/a.h5', i)
    #    new.configure_traits()