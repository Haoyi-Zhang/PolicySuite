"""Draw the manuscript schematics directly as font-embedded vector PDFs.

Run: python figures/draw_schematics.py --output figures
Requires Python 3.9+ and Matplotlib. No TeX engine or network is used.
The diagrams express the defined model; they are not measurement plots.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)


import math

def segment(d, start, end, radius, dashed=False, thick=False):
    dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
    ux=dx/length;uy=dy/length
    d.line([(start[0]+radius*ux,start[1]+radius*uy),
            (end[0]-radius*ux,end[1]-radius*uy)],dashed=dashed)
    if thick:d.ax.lines[-1].set_linewidth(1.2)

def draw(out):
    # Undirected support intersections. B2 is above B1, as in the example.
    d=Drawing((-2.0,-.62,5.8,1.82))
    positions={'a1':(0,1.2),'a2':(0,0),'b2':(3.45,1.2),'b1':(3.45,0)}
    segment(d,positions['a1'],positions['b1'],.4,dashed=True)
    segment(d,positions['a1'],positions['b2'],.4,thick=True)
    segment(d,positions['a2'],positions['b1'],.4,thick=True)
    for key,label in [('a1',r'$A_1$'),('a2',r'$A_2$'),('b2',r'$B_2$'),('b1',r'$B_1$')]:
        x,y=positions[key];d.box(key,x,y,.8,.8,label,shape='circle')
        if key.startswith('b'):d.ax.patches[-1].set_facecolor('.88')
    d.text(1.725,1.46,r'$q_1$');d.text(1.725,-.27,r'$q_2$')
    label=d.text(1.725,.82,r'$q_0$');label.set_rotation(math.degrees(math.atan2(-1.2,3.45)))
    label.set_bbox({'facecolor':'white','edgecolor':'none','pad':1})
    for x,y,label,ha in [(-.5,1.2,r'$\{q_0,q_1\}$','right'),
                         (-.5,0,r'$\{q_2\}$','right'),
                         (3.95,1.2,r'$\{q_1\}$','left'),
                         (3.95,0,r'$\{q_0,q_2\}$','left')]:d.text(x,y,label,size=8.5,ha=ha)
    d.save(out,'matching')

    # Requests are vertices, supports are undirected edges. A solid; B dashed.
    d=Drawing((-.7,-.72,4.7,2.0))
    positions={'a':(0,0),'b':(2,1.3),'c':(4,0)}
    segment(d,positions['a'],positions['b'],.3)
    segment(d,positions['b'],positions['c'],.3)
    segment(d,positions['a'],positions['c'],.3,dashed=True)
    for key,(x,y) in positions.items():d.box(key,x,y,.6,.6,'$'+key+'$',shape='circle')
    angle=math.degrees(math.atan2(1.3,2))
    d.text(.85,1.02,r'$F_A=\{a,b\}$').set_rotation(angle)
    d.text(3.15,1.02,r'$E_A=\{b,c\}$').set_rotation(-angle)
    d.text(2,-.43,r'$F_B=E_B=\{a,c\}$')
    d.save(out,'error-triangle')

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path(__file__).resolve().parent)
    output=parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    draw(output)
