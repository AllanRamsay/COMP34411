
import numpy as np

import matplotlib
matplotlib.use('TKAgg')
from matplotlib import pyplot as plt
from matplotlib import animation

def testanim():
    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure()
    fig.set_size_inches(12, 8)
    ax = plt.axes(xlim=(0, 6), ylim=(-2, 2))
    ax.set_aspect('equal')
    line, = ax.plot([], [], lw=2)
    global xc
    xc = 0
    trace = []
    
    # initialization function: plot the background of each frame
    def init():
        line.set_data([], [])

    def circle(ax, xc, i, colour="r", fill=False, radius=0.25):
        a = 2*np.pi*i/50.0
        x = xc+2*radius*a
        if fill:
            ax.add_artist(plt.Circle((x,0.0), radius+0.1, fill=fill, color=colour))
        else:
            print i, x, a, np.cos(a), np.sin(a)
            ax.add_artist(plt.Circle((x,0.0), radius, fill=fill, color=colour))
            trace.append(plt.Circle((x-radius*np.cos(a), radius*np.sin(a)), 0.02, fill=True, color="k"))
            for c in trace[-10:] if len(trace) > 10 else trace:
                ax.add_artist(c)
    # animation function.  This is called sequentially
    def animate(i):
        global xc
        circle(ax, xc, i, colour="w", fill=True)
        circle(ax, xc, i)

    # call the animator.  blit=True means only re-draw the parts that have changed.
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=100, interval=40, blit=False, repeat=False)

    # save the animation as an mp4.  This requires ffmpeg or mencoder to be
    # installed.  The extra_args ensure that the x264 codec is used, so that
    # the video can be embedded in html5.  You may need to adjust this for
    # your system: for more information, see
    # http://matplotlib.sourceforge.net/api/animation_api.html
    """
    FFMpegWriter = animation.writers['ffmpeg']
    anim.save('basic_animation.mp4', writer=FFMpegWriter(), fps=60)
    """
    fig.tight_layout()
    anim.save('basic_animation.mp4', fps=30, extra_args=[])
    plt.show()
