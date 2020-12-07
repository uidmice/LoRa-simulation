from framework.utils import Location
from config import *
from framework.Environment import TempEnvironment
from Simulation import Simulation
import matplotlib.pyplot as plt
import simpy
import matplotlib.animation as animation


plt.ion()
fig = plt.figure(figsize=(10,10))

node_locations = []
gateway_location = [Location(0, 0)]
for i in range(-CORD + 5, CORD + 1, 10):
    for j in range(-CORD + 5, CORD + 1, 10):
        x = j * GRID
        y = i * GRID
        node_locations.append(Location(x, y))

environment = TempEnvironment(None, Location(MAX_DISTANCE, -MAX_DISTANCE), Location(-MAX_DISTANCE, MAX_DISTANCE), 296.15, dx=GRID)
ax = fig.add_subplot(1,1,1)
im = ax.imshow(environment.T, alpha=.5, interpolation='bicubic', cmap='RdYlGn_r', origin='lower'
,extent=[-MAX_DISTANCE, MAX_DISTANCE, - MAX_DISTANCE, MAX_DISTANCE]
)
ax.axes.xaxis.set_visible(False)
ax.axes.yaxis.set_visible(False)
im.set_clim(353, 293)
plt.colorbar(im, orientation='horizontal', pad=0.08)
plt.axis('off')
plt.draw()
plt.show()

deploy_ax = fig.add_axes(ax.get_position(), frameon=False)
deploy_ax.set_xlim([-MAX_DISTANCE, MAX_DISTANCE])
deploy_ax.set_ylim([-MAX_DISTANCE, MAX_DISTANCE])
deploy_ax.scatter(0,0, s = 80, marker='X', c='r')
for n in node_locations:
    deploy_ax.scatter(n.x, n.y, s=20, c='blue')

contour_ax = fig.add_axes(ax.get_position(), frameon=False)
contour_ax.set_xlim([-MAX_DISTANCE, MAX_DISTANCE])
contour_ax.set_ylim([-MAX_DISTANCE, MAX_DISTANCE])
contour_ax.axes.xaxis.set_visible(False)
contour_ax.axes.yaxis.set_visible(False)

# plt.colorbar(im, orientation="vertical", pad=0.2)

ax_text = fig.add_axes([0.1, 0.93, 0.1, 0.05])
ax_text.axis("off")
time_label = ax_text.text(0.5, 0.5, "0s", ha="left", va="top")

writer = animation.writers['ffmpeg']
writer = writer(fps=10, metadata=dict(artist='Me'), bitrate=900)
ani = animation.FuncAnimation(fig, environment.draw,400, fargs=(im, contour_ax, time_label, UPDATA_RATE),
                                      interval=200)
ani.save("demo.mp4", writer=writer)