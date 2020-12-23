# simple gui script to display tip devives
# HR @KIT 2020 / GPL
# you need dash: 
#   pip install dash
# start it with from the tip folder with tip running:
# python web/webgui.py 
# or 
# python -m web.webgui
import pprint
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import flask

from datetime import datetime
import zmq

from lib.tip_zmq_client_lib import TIP_clients

from .webgui_settings_local import hostlist




#print(dir(twv.app.server))

class tip_webview(object):

    def __init__(self):
        
        
        tip_hosts = []
        for host in hostlist:
            tip_hosts.append(aquire_data(tip_server = host))
        #print(tip_hosts)

        self.server = flask.Flask(__name__) # define flask app.server
        # create the dash instance
        self.app = dash.Dash(__name__,
            meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            server = self.server
        )
        self.app.config['suppress_callback_exceptions']=True

        webview_layout = []
        webview_layout.append(self.create_outer_layout())
        webview_layout.append(self.create_inner_layout(tip_hosts))

        self.app.layout = html.Div(webview_layout)
        
        for tip_host in tip_hosts:
            for output_element in tip_host.output_elements:
                output_list = []
                input_list  = []
                dynamically_generated_function = self.create_callback(tip_host,output_element)
                output_list.append(Output(self.create_ID("",tip_host.name,output_element), 'figure'))
                output_list.append(Output(self.create_ID("label-",tip_host.name,output_element), 'children'))
                if tip_host.oe_wv_wd[output_element]:
                    print('img callback for ',tip_host.name, output_element)
                    output_list.append(Output(self.create_ID("img-label-",tip_host.name,output_element), 'children'))
                input_list.append(Input(self.create_ID('interval-component-',tip_host.name,output_element), 'n_intervals'))
                
                self.app.callback(output_list, input_list)(dynamically_generated_function)

    def create_ID(self,type,*args):
        id_delim  = ":"
        return type+id_delim.join(args)

    def create_outer_layout(self):
        row = []
        row.append(html.Div(
                        [
                        html.Div(
                            html.Img(src="assets/TIP_logo.png",alt="TIP"),id="TipLogo"),
                            html.H3("webview"),
                            html.Div(
                                [   html.A("TIP",href="https://github.com/qkitgroup/tip"),
                                    html.A("#",href="#")
                                ],className="topnav"),html.Br(),
                        ],className="header"))
        return html.Div(row)


    def create_inner_layout(self,tip_hosts):
        web_items = [] # this is the list of dash items
        
        for tip_host in tip_hosts:
            tip_host.data_x = {}
            tip_host.data_y = {}
            # reset elements
            for oe in tip_host.output_elements: 
                tip_host.data_x[oe] = []
                tip_host.data_y[oe] = []

        #for tip_host in tip_hosts:
        #    table_elements = [self.create_ID("",tip_host.name,oe) for oe in tip_host.output_elements]
        #print(table_elements)
        row = []
            #dbc.Row(dbc.Col(html.Div("A single column"))),
        cols = []
        for tip_host in tip_hosts:
            #cols.append(dbc.Col('',width=1))
            cols.append(dbc.Col(self.define_table_widget(tip_host),width = 3))
            
            cols.append(dbc.Col(self.define_imagemap(tip_host),width = 2))
             
            #dbc.Col(self.define_table_widget(tip_host),width = 2)
            cols.append(dbc.Col(self.define_tank(tip_host),width = 1))
            #dbc.Col(self.define_imagemap(tip_host))
            #dbc.Col(self.define_image_list()),
            #cols.append(dbc.Col(' ',width = 'auto'))
        row.append(dbc.Row(cols,no_gutters=True,justify="start"))
        
        row.append(html.Br())
        for tip_host in tip_hosts:
            cols =  [   
                dbc.Col(html.Div(dcc.Graph(id="%s"%(te))),width = 3) 
                for te in [self.create_ID("",tip_host.name,oe) for oe in tip_host.output_elements]
            ]
            row.append(dbc.Row(cols))
        
        web_items.append(html.Div(row))

        for tip_host in tip_hosts:
            for oe in tip_host.output_elements:
                web_items.append(
                    dcc.Interval(
                            id = self.create_ID('interval-component-',tip_host.name,oe),
                            interval = 1000 * float(tip_host.get_param(oe,'interval')), # in milliseconds
                            n_intervals = 0
                        )
                )
            
        #print(web_items)
        #print("create layout",web_items)
        
        return html.Div(web_items)


    def define_table_widget(self,tip_host):
        #output_elements = [self.create_ID("",tip_host.name,oe) for oe in tip_host.output_elements]
        #print("##############",output_elements)
        return html.Div(html.Table(
            # Header
            [
                #html.Tr([html.Th(col) for col in ['Device','Property','Value']])
                html.Tr([html.Th(col) for col in [tip_host.name,'','']])
            ] +
            # Body
            [
            html.Tr(
                [
                    #html.Td("%s"%(tip_host.oe_items[oe][0])),
                    html.Td("%s"%(oe)), 
                    html.Td(id="label-"+self.create_ID("",tip_host.name,oe)), 
                ]
                ) for oe in tip_host.output_elements 
            ]
            ),id=self.create_ID("","mytable",tip_host.name)
            )
    def define_imagemap(self,tip_host):

        img_dict = {}
        img_dict['0'] = html.Img(src = "assets/cryo_all_stages_small_tip.jpg", height = "400")
        for oe in tip_host.output_elements:
            if not tip_host.oe_wv_wd[oe]:
                continue
            if tip_host.oe_wv_wt[oe] == 'image_map' and tip_host.oe_wv_wm[oe] in ['Tmxc','Tstill','Tfk','Tffk']:
                img_dict[tip_host.oe_wv_wm[oe]] = html.Div(id=self.create_ID("img-label-",tip_host.name,oe),  
                    className = tip_host.oe_wv_wm[oe])
            
        return html.Div( list(img_dict.values()), className = "img_container")


    def define_tank(self,tip_host):
        img_dict = {}
        for oe in tip_host.output_elements:
            if not tip_host.oe_wv_wd[oe]:
                continue
            if tip_host.oe_wv_wt[oe] == 'tank':
                print ('tank', oe)
                print(self.create_ID("img-label-",tip_host.name,oe))
                img_dict[oe] = html.Div(
                [ 
                html.Label(['lN',html.Sub('2')]),
                daq.GraduatedBar(
                    id = self.create_ID("img-label-",tip_host.name,oe),
                    color={"ranges":{"red":[0,0.4],"yellow":[0.4,0.7],"green":[0.7,1]}},
                    showCurrentValue=True,
                    vertical=True,
                    value = 1,
                    min = 0,
                    max = 1,
                    step = 0.05,
                    labelPosition = "bottom",
                    size=365,
                    #label = 'lN2',
                    )
                ],
                )
        return html.Div( list(img_dict.values()))

    def create_callback(self,tip_host,device):
        #print(tip_host, device)
        def update_figure(device_):

            MAXLENGTH = 150
            if len(tip_host.data_x[device]) > MAXLENGTH:
                tip_host.data_x[device].pop(0)
                tip_host.data_y[device].pop(0)
            
            dtime = datetime.fromtimestamp(float(tip_host.get_param(device,'change_time')))

            tip_host.data_x[device].append(dtime)
            
            #values = float(tip_host.get_param(device,'temperature'))
            values = float(tip_host.get_param(device,tip_host.oe_items[device][0]))
            tip_host.data_y[device].append(values)

            traces = []

            traces.append(
                dict(
                x = tip_host.data_x[device],
                y = tip_host.data_y[device],
                text = self.create_ID("",tip_host.name,device),
                mode = 'markers',
                opacity = 0.7,
                marker = {
                    'size': 7,
                    'line': {'width': 1, 'color': 'white'}
                },
                name = self.create_ID("",tip_host.name,device)
            ))

            #
            # returns
            #
            graph = {
                'data': traces,
                'layout': dict(
                    xaxis = {
                        'type': 'lin', 'title': 'time', 
                        'gridwidth': '0.1','gridcolor' : 'gray'
                        },#'tickformat':'%d',},
                    #'range':[2.3, 4.8]},
                    yaxis = {
                        'title': tip_host.oe_items[device][0] +' ('+ tip_host.oe_unit[device][0]+")" , #'Temperature',
                        'gridwidth': '0.1','gridcolor' : 'gray'
                        }, #'range': [20, 90]},
                    #margin={'l': 20, 'b': 20, 't': 20, 'r': 20},
                    #legend={'x': 0, 'y': 1},
                    #hovermode='closest',
                    width = 400, height = 400,
                    transition = {'duration': 500},
                    title = {'text': tip_host.name+" "+device},
                    #template = "plotly_white",
                    #template = "plotly_dark",
                    #template = "seaborn",
                    showgrid = False,
                    gridcolor = "rgb(100,1000,100)",
                    margin = dict(l=120, r=20, t=40, b=50),
                    #showlegend= True,
                    paper_bgcolor = "rgba(0,0,0,0)",
                    plot_bgcolor =  'rgba(0,0,0,0)',
                    font = {"color": "rgb(247, 223, 146)"},
                    autosize= True,
                )
            }

            last_val  = float(tip_host.data_y[device][-1])   
            table_str = "%.04f %s"%(last_val,tip_host.oe_unit[device][0])    
            img_str   = table_str
            
            retval = (graph,table_str)

            if tip_host.oe_wv_wd[device]:
                if tip_host.oe_wv_wt[device] == 'image_map':
                    return retval + (img_str,)
                elif tip_host.oe_wv_wt[device] == 'tank':
                    return retval + (last_val,)
                else:
                    return None
            else:
                return retval
            

        return update_figure

class aquire_data(object):
    def __init__(self,tip_server = "localhost:5000"):
        TC = self.connect_to_TIP_instance(tip_server)
        print(tip_server)
        system = TC.get_device('system')

        self.name = system['name']
        self.output_elements  = []
        self.active_devices = system['active_devices']

        self.get_param=self.catch_tip(TC.get_param)
        self.get_device=self.catch_tip(TC.get_device)

        self.check_webview_prop()

    def check_webview_prop(self):
        self.oe_intervals = {}
        self.oe_items = {}
        self.oe_unit = {}
        self.oe_wv_wd = {}
        self.oe_wv_wt = {}
        self.oe_wv_wm = {}

        for device in self.active_devices:
            print ('active device:',device)
            wv =  self._boolean(self.get_param(device, 'webview'))
            
            if wv:
                self.output_elements.append(device)
            else:
                continue

            wv_items = self.get_param(device, 'webview_items').split(' ')
            self.oe_items[device] = wv_items

            wv_interval = float(self.get_param(device, 'webview_interval'))
            if wv_interval > 0:
                pass
            else:
                wv_interval = float(self.get_param(device, 'interval'))


            unit = self.get_param(device, 'unit').split(' ')
            self.oe_unit[device]=unit
            
            self.oe_intervals[device] = wv_interval

            #
            # is web widget display enabled  ?
            #
            self.oe_wv_wd[device] = self._boolean(self.get_param(device, 'webview_widget_display'))
            if self.oe_wv_wd[device]:
                self.oe_wv_wt[device] = self.get_param(device, 'webview_widget_type')
                self.oe_wv_wm[device] = self.get_param(device, 'webview_widget_map')
                #'webview_widget_display'      : False,          # should device be e.g. displayed in cryo image?
                #'webview_widget_type'         : 'image_map',    # one of image_map, tank, graph,...
                #'webview_widget_map'          : 'Tmxc', 

        print("oe_items",self.oe_items)

    def _boolean(self,s): return s.lower() in ("yes", "true", "t", "1")

    def connect_to_TIP_instance(self,tip_server):
        try:
            TC = TIP_clients(tip_server)
            return TC
        except zmq.error.ZMQError as e:
            print("Error connecting to tip.py: "+str(e))
            exit(1)

    def catch_tip(self, getit):
        def getfunc(*args):
            try:
                return getit(*args)
            except zmq.error.ZMQError as e:
                print("ZMQError: "+str(e))
                print(args)
                return 0
        return getfunc


if __name__ == '__main__':
    #app.run_server(debug=True)
    #app.run_server()
    app = tip_webview()
    app.app.run_server()
else:
    # prepare for gunicorn server, e.g. exec
    # 'gunicorn web.webgui:server -w 4 -b :8000'
    # from tip root directory and open http://localhost:8000
    twv = tip_webview() 
    server = twv.server