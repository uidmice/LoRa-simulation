import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from scipy import interpolate
import numpy as np

thr = [10,20,30,45,60,75]
dT = 5000
deltaT = 5

inp = False
cor = np.load('coordinate.npy')

for t in thr:

    Srate = np.load('Srate_%d_%d_2.npy' %(dT, t))
    Trate = np.load('Trate_%d_%d_2.npy'%(dT, t))

    N = 12
    fps = 10 # frame per sec
    frn = Trate.shape[1] # frame number of the animation

    X = np.reshape(cor[0,:], (N,N))
    Y = np.reshape(cor[1,:], (N,N))

    fig = plt.figure(figsize=(18,9))
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')

    ax1.set_zlim(0,1.1)
    ax2.set_zlim(0,1.1)
    axtext = fig.add_axes([0.0,0.95,0.1,0.05])
    axtext.axis("off")
    time = axtext.text(0.5,0.5, "0s", ha="left", va="top")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='Me'), bitrate=1800)


    if inp:
        X_s = range(-1500,1500,20)
        x, y = np.meshgrid(X_s,X_s)
        z1 = np.zeros((frn, len(X_s), len(X_s)))
        z2 = np.zeros((frn, len(X_s), len(X_s)))
        for i in range(frn):
            # Z1 = np.reshape(Srate[:,i], (N,N))
            # Z2 = np.reshape(Trate[:,i], (N,N))
            # f1 = interpolate.interp2d(X, Y, Z1)
            # f2 = interpolate.interp2d(X, Y, Z2)
            # z1[i,:,:] = f1(X_s, X_s)
            # z2[i,:,:] = f2(X_s, X_s)
            xi = np.zeros((len(X_s)*len(X_s), 2))
            xi[:,0] = x.flatten()
            xi[:,1] = y.flatten()
            Z1 = interpolate.griddata(cor.T, Srate[:,i],xi)
            Z2 = interpolate.griddata(cor.T, Trate[:,i],xi)
            z1[i,:,:] = np.reshape(Z1, (len(X_s), len(X_s)))
            z2[i,:,:] = np.reshape(Z2, (len(X_s), len(X_s)))


    else:
        z1 = np.zeros((frn, N, N))
        z2 = np.zeros((frn, N, N))
        x = X
        y = Y
        for i in range(frn):
            z1[i, :, :] = np.reshape(Srate[:,i], (N,N))
            z2[i, :, :] = np.reshape(Trate[:,i], (N,N))

    def update_plot(frame_number):
        ax1.clear()
        ax2.clear()
        ax1.set_title("Success rate")
        ax2.set_title(r"$1-\frac{|dT|}{T_{true}}$")
        #
        # Z = f(range(-1000,1000,20), range(-1000,1000,20))
        # ax.plot_surface(x, y, Z,  cmap="jet" )

        ax1.scatter3D(x, y, z1[frame_number, :, :],  cmap="winter_r", c = z1[frame_number, :, :].flatten(), vmin=0, vmax=2)
        ax2.scatter3D(x, y, z2[frame_number, :, :],  cmap="winter_r", c = z2[frame_number, :, :].flatten(), vmin=0, vmax=2)
        ax1.set_zlim(0,1.1)
        ax2.set_zlim(0,1.1)
        time.set_text(str(frame_number * deltaT) + "s")


    ax1.scatter3D(x, y, z1[0, :, :], cmap="winter_r", c = z1[0, :, :].flatten(), vmin=0, vmax=2)
    ax2.scatter3D(x, y, z2[0, :, :],  cmap="winter_r", c = z2[0, :, :].flatten(), vmin=0, vmax=2)
    ax1.set_title("Success rate")
    ax2.set_title(r'$1-\frac{|dT|}{T_{true}}$')
    ani = animation.FuncAnimation(fig, update_plot, frn, interval=2000/fps)


    # plt.show()

    #
    fn = 'plot_surface_animation_funcanimation'
    ani.save('T_%d_%d_2.mp4' %(dT,t),writer=writer)


    Srate = np.load('Srate_%d_%d_1.npy' %(dT, t))
    Trate = np.load('Trate_%d_%d_1.npy'%(dT, t))

    N = 12
    fps = 10 # frame per sec
    frn = Trate.shape[1] # frame number of the animation

    X = np.reshape(cor[0,:], (N,N))
    Y = np.reshape(cor[1,:], (N,N))

    fig = plt.figure(figsize=(18,9))
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')

    ax1.set_zlim(0,1.1)
    ax2.set_zlim(0,1.1)
    axtext = fig.add_axes([0.0,0.95,0.1,0.05])
    axtext.axis("off")
    time = axtext.text(0.5,0.5, "0s", ha="left", va="top")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='Me'), bitrate=1800)


    if inp:
        X_s = range(-1500,1500,20)
        x, y = np.meshgrid(X_s,X_s)
        z1 = np.zeros((frn, len(X_s), len(X_s)))
        z2 = np.zeros((frn, len(X_s), len(X_s)))
        for i in range(frn):
            # Z1 = np.reshape(Srate[:,i], (N,N))
            # Z2 = np.reshape(Trate[:,i], (N,N))
            # f1 = interpolate.interp2d(X, Y, Z1)
            # f2 = interpolate.interp2d(X, Y, Z2)
            # z1[i,:,:] = f1(X_s, X_s)
            # z2[i,:,:] = f2(X_s, X_s)
            xi = np.zeros((len(X_s)*len(X_s), 2))
            xi[:,0] = x.flatten()
            xi[:,1] = y.flatten()
            Z1 = interpolate.griddata(cor.T, Srate[:,i],xi)
            Z2 = interpolate.griddata(cor.T, Trate[:,i],xi)
            z1[i,:,:] = np.reshape(Z1, (len(X_s), len(X_s)))
            z2[i,:,:] = np.reshape(Z2, (len(X_s), len(X_s)))


    else:
        z1 = np.zeros((frn, N, N))
        z2 = np.zeros((frn, N, N))
        x = X
        y = Y
        for i in range(frn):
            z1[i, :, :] = np.reshape(Srate[:,i], (N,N))
            z2[i, :, :] = np.reshape(Trate[:,i], (N,N))

    def update_plot(frame_number):
        ax1.clear()
        ax2.clear()
        ax1.set_title("Success rate")
        ax2.set_title(r"$1-\frac{|dT|}{T_{true}}$")
        #
        # Z = f(range(-1000,1000,20), range(-1000,1000,20))
        # ax.plot_surface(x, y, Z,  cmap="jet" )

        ax1.scatter3D(x, y, z1[frame_number, :, :],  cmap="winter_r", c = z1[frame_number, :, :].flatten(), vmin=0, vmax=2)
        ax2.scatter3D(x, y, z2[frame_number, :, :],  cmap="winter_r", c = z2[frame_number, :, :].flatten(), vmin=0, vmax=2)
        ax1.set_zlim(0,1.1)
        ax2.set_zlim(0,1.1)
        time.set_text(str(frame_number * deltaT) + "s")


    ax1.scatter3D(x, y, z1[0, :, :], cmap="winter_r", c = z1[0, :, :].flatten(), vmin=0, vmax=2)
    ax2.scatter3D(x, y, z2[0, :, :],  cmap="winter_r", c = z2[0, :, :].flatten(), vmin=0, vmax=2)
    ax1.set_title("Success rate")
    ax2.set_title(r'$1-\frac{|dT|}{T_{true}}$')
    ani = animation.FuncAnimation(fig, update_plot, frn, interval=2000/fps)


    # plt.show()

    #
    fn = 'plot_surface_animation_funcanimation'
    ani.save('T_%d_%d_1.mp4' %(dT,t),writer=writer)
