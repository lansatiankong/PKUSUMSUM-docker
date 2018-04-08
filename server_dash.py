from typing import List, Callable
import json
import codecs
import logging
import os
from string import Template
import sys

from flask import jsonify

import dash
#import dash_auth
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

introduction = '''
- [PKUSUMSUM](https://github.com/PKULCWM/PKUSUMSUM)(PKU’s SUMmary of SUMmarization methods) is an integrated toolkit for automatic document summarization. 
- This demo is generated by [Dash](https://plot.ly/products/dash/).
'''

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def make_app(user: str = 'admin',
             password: str = 'pkusumsum') -> dash.Dash:
    """
    Creates a Flask app that serves up the provided ``Predictor``
    along with a front-end for interacting with it.

    If you want to use the built-in bare-bones HTML, you must provide the
    field names for the inputs (which will be used both as labels
    and as the keys in the JSON that gets sent to the predictor).

    If you would rather create your own HTML, call it index.html
    and provide its directory as ``static_dir``. In that case you
    don't need to supply the field names -- that information should
    be implicit in your demo site. (Probably the easiest thing to do
    is just start with the bare-bones HTML and modify it.)

    In addition, if you want somehow transform the JSON prediction
    (e.g. by removing probabilities or logits)
    you can do that by passing in a ``sanitizer`` function.
    """
    
    app = dash.Dash('PKUSUMSUM Demo')
    app.config.supress_callback_exceptions = True
    
    #VALID_USERNAME_PASSWORD_PAIRS = [[user or 'admin', password or 'pkusumsum']]
    #auth = dash_auth.BasicAuth(
    #    app,
    #    VALID_USERNAME_PASSWORD_PAIRS
    #)

    app.layout = html.Div(children=[html.Div(style={'width': '49%','float':'left','margin-top':10},children=[
    html.H3(style={'margin-top':10},children='PKUSUMSUM Demo'),
    dcc.Markdown(children=introduction),
    html.H4('Parameters:'),
    dcc.RadioItems(
      id = 'T',
      options=[
          {'label': "1: single-document", 'value': 1},
          {'label': '2: multi-document', 'value': 2},
          {'label': "3: topic-based multi-document", 'value': 3},
      ],
      value=1,
      labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
      id = 'L',
      options=[
          {'label': "1 – Chinese", 'value': 1},
          {'label': '2 – English', 'value': 2},
          {'label': "3 - other Western languages", 'value': 3},
      ],
      value=1,
      labelStyle={'display': 'inline-block'}
    ),
    html.Span('Specify the expected number of words in the final summary:'),
    html.Div(style={'margin-bottom':20},children=[
    dcc.Slider(
    id='n',
    min=0,
    max=300,
    marks={i:str(i) for i in range(0,300,50)},
    step=1,
    value=60,
    ),]),
    html.Span('Specify which method is used to solve the problem:'),
    dcc.RadioItems(
      id = 'm',
      options=[
          {'label': "1 - Lead", 'value': 1},
          {'label': '2 - Centroid', 'value': 2},
          {'label': "3 - ILP", 'value': 3},
          {'label': "4 - LexPageRank", 'value': 4},
          {'label': "5 - TextRank", 'value': 5},
          {'label': "6 - Submodular", 'value': 6},
      ],
      value=1,
      labelStyle={'display': 'inline-block'}
    ),
    html.Span('Specify whether to remove the stopwords.'),
    dcc.RadioItems(
    id='stop',
    options=[
        {'label': 'y', 'value': 'y'},
        {'label': 'n', 'value': 'n'}
    ],
    value='n',
    labelStyle={'display': 'inline-block'}
    ),
    html.Span('Specify whether you want to conduct word stemming (Only for English language):'),
    dcc.RadioItems(
    id='stem',
    options=[
        {'label': 'stem', 'value': 1},
        {'label': 'no stem', 'value': 2},
    ],
    value=1,
    labelStyle={'display': 'inline-block'}
    ),
    html.Span('Specify which redundancy removal method is used for summary sentence selection:'),
    dcc.RadioItems(
    id='redundancy ',
    options=[
        {'label': '1 – MMR-based method', 'value': 1},
        {'label': '2 – Threshold-based method', 'value': 2},
        {'label': '3 – Penalty imposing method', 'value': 3},
    ],
    value=3,
    labelStyle={'display': 'inline-block'}
    ),
    html.Span('Specify internal parameter of the redundancy removal methods:[0,1]'),
    dcc.Slider(
    id='p',
    min=0,
    max=1,
    step=0.1,
    value=0.7,
    ),
    html.Span('Specify a scaling factor of sentence length when we choose sentences:[0,1]'),
    dcc.Slider(
    id='beta',
    min=0,
    max=1,
    step=0.1,
    value=0.1,
    ),
    html.Span('Specify the similarity threshold for linking two sentences:[0,1]'),
    dcc.Slider(
    id='link',
    min=0,
    max=1,
    step=0.1,
    value=0.1,
    ),
    html.Span('Specify the type of the submodular method:'),
    dcc.RadioItems(
    id='sub',
    options=[
        {'label': "1 – (Li at el, 2012)", 'value': 1},
        {'label': "2 - modification(Lin and Bilmes, 2010)", 'value': 2}
    ],
    value=1,
    labelStyle={'display': 'inline-block'}
    ),
    html.Span('Specify the threshold coefficient:[0,1]'),
    dcc.Slider(
    id='A',
    min=0,
    max=1,
    step=0.1,
    value=0.5,
    ),
    html.Span('Specify the trade-off coefficient:[0,1]'),
    dcc.Slider(
    id='lam',
    min=0,
    max=1,
    step=0.1,
    value=0.5,
    ),
    ]),
    html.Div(style={'width': '49%','float':'right','margin-top':20},children=[html.H4('article:'),
    dcc.Textarea(style={'width': '100%','height':300},id='article', placeholder='E.g. "bla bla..."'),
    html.Button('Submit', id='submit'),
    html.H4('summarization:'),
    dcc.Textarea(style={'width': '100%','height':200},id='summarization', placeholder='summarization will be here')]),
    ])

    @app.callback(
                  Output('summarization', 'value'),
                  [Input('submit', 'n_clicks')],
                  [State('T', 'value'),
                  State('L', 'value'),
                  State('n', 'value'),
                  State('m', 'value'),
                  State('stop', 'value'),
                  State('stem', 'value'),
                  State('redundancy ', 'value '),
                  State('p', 'value'),
                  State('beta', 'value'),
                  State('link', 'value'),
                  State('sub', 'value'),
                  State('A', 'value'),
                  State('lam', 'value'),
                  State('article', 'value')]
                  )
    def update_output(n_clicks,T,L,n,m,stop,stem,redundancy,p,beta,link,sub,A,lam,article):
        '''
        java -jar PKUSUMSUM.jar –T 1 –input ./article.txt –output ./summay.txt –L 1 –n 100 –m 2 –stop n
        '''
        #return ' '.join(map(str,[n_clicks,T,L,n,m,stop,stem,redundancy,p,beta,link,sub,A,lam,article]))
        return sumsum(T,L,n,m,stop,stem,redundancy,p,beta,link,sub,A,lam,article)
    return app

def sumsum(T,L,n,m,stop,stem,redundancy,p,beta,link,sub,A,lam,article):
    with codecs.open('article.txt','w',encoding='utf-8') as f:
        f.write(article)
    output = codecs.open('summay.txt','w',encoding='utf-8')
    output.close()
    cmd = 'java -jar PKUSUMSUM.jar –T {} –input ./article.txt –output ./summay.txt –L {} –n {} –m {} –stop {}'.format(T,L,n,m,stop)
    cmd += ' -s {}'.format(stem)
    cmd += ' -R {}'.format(redundancy)
    cmd += ' -p {}'.format(p)
    cmd += ' -beta {}'.format(beta)
    if L == 2:
        cmd += ' -s {}'.format(stem)
    if m == 4:
        cmd += ' -link {}'.format(link)
    if m == 6:
        cmd += ' -sub {}'.format(sub)
        cmd += ' -A {}'.format(A)
        cmd += ' -lam {}'.format(lam)
    os.popen(cmd)
    output = codecs.open('summay.txt','r',encoding='utf-8')
    summay = output.read()
    output.close()
    return summay
    
def main():
    app = make_app()
                   
    app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
    #app.css.append_css({'external_url': 'static_html/demo.css'})
    app.run_server(port=8080, debug=True)

if __name__ == "__main__":
    main()
