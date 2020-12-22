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
                dynamically_generated_function = self.create_callback(tip_host,output_element)
                self.app.callback(
                    [
                        Output(self.create_ID("",tip_host.name,output_element), 'figure'),
                        Output(self.create_ID("label-",tip_host.name,output_element), 'children'),
                        Output(self.create_ID("img-label-",tip_host.name,output_element), 'children')

                    ], 
                    [
                        Input(self.create_ID('interval-component-',tip_host.name,output_element), 'n_intervals')
                    ]
                    )(dynamically_generated_function)

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
            cols.append(dbc.Col('',width=1))
            cols.append(dbc.Col(self.define_table_widget(tip_host),width = 3))
            cols.append(dbc.Col(self.define_imagemap(tip_host)))
            
            #dbc.Col(self.define_table_widget(tip_host),width = 2)
            #dbc.Col(self.define_tank(tip_host)),
            #dbc.Col(self.define_imagemap(tip_host))
            #dbc.Col(self.define_image_list()),
        row.append(dbc.Row(cols))
        
        
        for tip_host in tip_hosts:
            cols =  [   
                dbc.Col(html.Div(html.Td(dcc.Graph(id="%s"%(te)))),width = 3) 
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
        print("create layout",web_items)
        
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
                    html.Td("%s"%(oe)), 
                    html.Td("%s"%(tip_host.oe_items[oe][0])),
                    html.Td(id="label-"+self.create_ID("",tip_host.name,oe)), 
                ]
                ) for oe in tip_host.output_elements 
            ]
            ),id=self.create_ID("","mytable",tip_host.name)
            )
    def define_imagemap(self,tip_host):
        #table_elements = [self.create_ID("",tip_host.name,oe) for oe in tip_host.output_elements]
        return html.Div(
        [
            html.Img(src = "assets/cryo_all_stages_small_tip.jpg", height = "400"),#,style = "width:100%"),
            html.Div(id=self.create_ID("img-label-",tip_host.name,'mxc'),  className = "Tmxc"),
            html.Div(id=self.create_ID("img-label-",tip_host.name,'T9884'),  className = "Tstill"),
            html.Div(id=self.create_ID("img-label-",tip_host.name,'A1'),  className = "Tfk"),
            html.Div(id=self.create_ID("img-label-",tip_host.name,'B1'),  className = "Tffk")
        ]
        , className = "img_container",
        )

    def define_image_list(self):
        return html.Div(
                html.Ul([
                    html.Li("testme"),
                    html.Li("now"),
                    html.Li("or"),
                    html.Li("never"),
                ] , className = "vertlist"
                )
        )


    def define_tank(self,tip_host):
        return html.Div(
        [
        daq.GraduatedBar(
            color={"ranges":{"red":[0,4],"yellow":[4,7],"green":[7,10]}},
            showCurrentValue=True,
            vertical=True,
            value = 9,
            min = 0,
            max = 10,
            step = 0.25,
            labelPosition = "bottom",
            label = tip_host.name,
        )
        ],
        )


        """
    <div class="container">
    <img src="img_snow_wide.jpg" alt="Snow" style="width:100%;">
    <div class="bottom-left">Bottom Left</div>
    <div class="top-left">Top Left</div>
    <div class="top-right">Top Right</div>
    <div class="bottom-right">Bottom Right</div>
    <div class="centered">Centered</div>
    </div>


css:

.container {
  position: relative;
  text-align: center;
  color: white;
}

/* Bottom left text */
.bottom-left {
  position: absolute;
  bottom: 8px;
  left: 16px;
}

/* Top left text */
.top-left {
  position: absolute;
  top: 8px;
  left: 16px;
}

/* Top right text */
.top-right {
  position: absolute;
  top: 8px;
  right: 16px;
}

/* Bottom right text */
.bottom-right {
  position: absolute;
  bottom: 8px;
  right: 16px;
}

/* Centered text */
.centered {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
        """

    def create_callback(self,tip_host,device):
        print(tip_host, device)
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
            table = "%.04f %s"%(float(tip_host.data_y[device][-1]),tip_host.oe_unit[device][0])
            img = "%.04f %s"%(float(tip_host.data_y[device][-1]),tip_host.oe_unit[device][0])
            return graph,table,img

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