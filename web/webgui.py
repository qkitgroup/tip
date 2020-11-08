# simple gui script to display tip devives
# HR @KIT 2020 / GPL
# you need dash: 
#   pip install dash
# start it with from the tip folder with tip running:
# python gui/webgui.py 


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime, timezone
import zmq

#from lib.tip_zmq_client_lib import setup_connection, get_param, get_device
from lib.tip_zmq_client_lib import TIP_clients

from .webgui_settings_local import hostlist

def connect_to_TIP_instances():
    try:
        TC = TIP_clients(hostlist[0])
        #setup_connection(url="tcp://localhost:5000")
        return TC
    except zmq.error.ZMQError as e:
        print("Error connecting to tip.py: "+str(e))
        exit(1)

TC = connect_to_TIP_instances()
system = TC.get_device('system')
output_elements = system['active_thermometers']
#print(output_elements)

def catch_tip(getit):
    def getfunc(*args):
        try:
            return getit(*args)
        except zmq.error.ZMQError as e:
            print("ZMQError: "+str(e))
            return 0
    return getfunc

get_param=catch_tip(TC.get_param)
get_device=catch_tip(TC.get_device)


def generate_table(output_elements):
    return html.Div(html.Table(
        # Header
        [html.Tr([html.Th(col) for col in [' ','Device','Value','Unit']])] +

        # Body
        [html.Tr([html.Td(" "),html.Td("%s"%(oe)), 
            html.Td(id="label-"+oe), 
            html.Td("K")]) for oe in output_elements ]
    ),id="mytable"
    )

app = dash.Dash(__name__,
meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.config['suppress_callback_exceptions']=True


data_x = {}
data_y = {}
for oe in output_elements: 
    data_x[oe] = []
    data_y[oe] = []

plots= []
row = []

COLUMNS = 3
#for hd in range(COLUMNS):
#    row.append(html.Th(""))
#plots.append(html.Tr(row))
row = []
table_elements = output_elements[:]
table_elements.insert(0,"xyz")
#print(table_elements)
for i,at in enumerate(table_elements):
    if i == 0:
        row.append(html.Td(generate_table(output_elements)))
        continue
    elif (i+1)%COLUMNS == 0:
        row.append(html.Td(dcc.Graph(id="%s"%(at))))
        plots.append(html.Tr(row))
        row=[]
    else:
        row.append(html.Td(dcc.Graph(id="%s"%(at))))
if (i+1)%COLUMNS != 0:
    plots.append(html.Tr(row))

print (plots)
print (output_elements)
for dev in output_elements:
    plots.append(
        dcc.Interval(
                id='interval-component-'+dev,
                interval=1000*float(get_param(dev,'interval')), # in milliseconds
                n_intervals=0
            )
    )

app.layout = html.Div([
    html.Table(plots)
])



def create_callback(device):
    def update_figure(device_):

        MAXLENGTH = 150
        if len(data_x[device]) > MAXLENGTH:
            data_x[device].pop(0)
            data_y[device].pop(0)
        dtime = datetime.fromtimestamp(float(get_param(device,'change_time')))
        data_x[device].append(dtime)
        values = float(get_param(device,'temperature'))
        data_y[device].append(values)

        
        

        traces = []

        traces.append(
            dict(
            x=data_x[device],
            y=data_y[device],
            text=device,
            mode='markers',
            opacity=0.7,
            marker={
                'size': 8,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name=device
        ))

        return {
            'data': traces,
            'layout': dict(
                xaxis={'type': 'lin', 'title': 'time'},#'tickformat':'%d',},
                    #'range':[2.3, 4.8]},
                yaxis={'title': 'Temperature'}, #'range': [20, 90]},
                #margin={'l': 20, 'b': 20, 't': 20, 'r': 20},
                #legend={'x': 0, 'y': 1},
                #hovermode='closest',
                width=400, height=400,
                transition = {'duration': 500},
                title = {"text": device},
                template="plotly_dark",
                margin= dict(l=120, r=20, t=40, b=50),
                #showlegend= True,
                paper_bgcolor= "rgba(0,0,0,0)",
                plot_bgcolor =  "rgba(0,0,0,0)",
                font = {"color": "rgb(255, 196, 0)"},
                #autosize= True,
            )
        }, "%03g"%(float(data_y[device][-1]))
    return update_figure

for output_element in output_elements:
    dynamically_generated_function = create_callback(output_element)
    app.callback([Output(output_element, 'figure'),Output("label-"+output_element, 'children')], 
    [Input('interval-component-'+output_element, 'n_intervals')])(dynamically_generated_function)


if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server()