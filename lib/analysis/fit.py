def select_from_plot(Point, indices, values, i=0, dot=None, proj_axis='x',
                     block=False):
    from matplotlib.pyplot import figure, show, figtext, close
    from lib.utils import point_str

    imin = min(indices)
    imax = max(indices)
    vmin = min(values)
    vmax = max(values)

    color_cycle = ['xkcd:carmine', 'xkcd:teal', 'xkcd:peach', 'xkcd:mustard',
                   'xkcd:cerulean']

    n_col = len(color_cycle)

    fig = figure()
    ax = fig.add_subplot(111)
    canvas = fig.canvas

    fig.set_size_inches(7, 5)
    ax.plot(indices, values, color=color_cycle[i % n_col])
    ax.set_title('λ = ' + point_str(Point))
    figtext(.5,.03,' '*10 +
            'press enter to convalid current selection', ha='center')
    if block:
        ax.set_ylim(top=vmax*1.1)
    if not dot == None:
        ax.plot(*dot, 'o', mec='w')

    fig.canvas.draw()

    def on_press(event):
        on_press.p = True
    on_press.p = False

    def on_click(event):
        on_press.p = False
        if event.inaxes is not None:
            x = event.xdata
            y = event.ydata

            vmax_ = vmax*1.1 if block else vmax
            inarea = x > imin and x < imax and y > vmin and y < vmax_
            if inarea and not on_motion.drag:
                on_click.x = x
                on_click.y = y
                if on_click.i > 0:
                    on_click.m[0].remove()
                on_click.m = ax.plot(x, y, 'o', mec='w')
                event.canvas.draw()
                on_click.i += 1
        on_motion.drag = False
    on_click.i = 0
    on_click.m = None
    on_click.x = None
    on_click.y = None

    def on_motion(event):
        if on_press.p == True:
            on_motion.drag = True
            hide_drag = not event.canvas.manager.toolbar._active == None
        else:
            hide_drag = False
        if event.inaxes is not None and not hide_drag:
            x = event.xdata
            y = event.ydata

            vmax_ = vmax*1.1 if block else vmax
            inarea = x > imin and x < imax and y > vmin and y < vmax_
            if inarea:
                m = ax.plot(x, y, 'wo', mec='k')
                if 'x' in proj_axis:
                    n = ax.plot(x, vmin, 'k|', ms=20)
                if 'y' in proj_axis:
                    o = ax.plot(imin, y, 'k_', ms=20)
                event.canvas.draw()
                m[0].remove()
                if 'x' in proj_axis:
                    n[0].remove()
                if 'y' in proj_axis:
                    o[0].remove()
        else:
            event.canvas.draw()
    on_motion.drag = False

    def on_key(event):
        if event.key == 'enter':
            close()
            if on_click.x == None:
                on_click.x = -1
        if event.key == 'q':
            on_click.x = None
            on_click.y = None
            close()


    canvas.mpl_connect('button_press_event', on_press)
    canvas.mpl_connect('button_release_event', on_click)
    canvas.mpl_connect('motion_notify_event', on_motion)
    canvas.mpl_connect('key_press_event', on_key)
    show()

    return on_click.x, on_click.y

def set_cut(p_dir, i=0):
    from os import chdir
    from os.path import basename
    from math import ceil
    from numpy import loadtxt
    from lib.utils import dir_point

    chdir(p_dir)
    Point = dir_point(basename(p_dir))

    vol_file = 'history/volumes.txt'
    indices, volumes = loadtxt(vol_file, unpack=True)

    index, _ = select_from_plot(Point, indices, volumes, i)

    if index:
        return ceil(index)
    else:
        return index

def blocked_mean_std(indices, volumes, block_size):
    from numpy import mean, std
    from math import sqrt

    bs = block_size
    buffer_start = indices[0]
    buffer = []
    block_means = []
    for i in range(0,len(indices)):
        if (indices[i] - buffer_start) > bs:
            block_means += [mean(buffer)]
            buffer = []
            buffer_start = indices[i]
        buffer += [volumes[i]]

    vol = mean(block_means)
    err = std(block_means) / sqrt(len(block_means) - 1)

    return vol, err

def set_block(p_dir, i=0):
    from os import chdir
    from os.path import basename
    from math import log
    import json
    from numpy import loadtxt
    from lib.utils import dir_point

    chdir(p_dir)
    Point = dir_point(basename(p_dir))

    with open('measures.json', 'r') as file:
        measures = json.load(file)

    cut = measures['cut']
    if not cut:
        print("No 'cut' found, so it's not possible to go on with the 'block'.")
        return None

    vol_file = 'history/volumes.txt'
    indices, volumes = loadtxt(vol_file, unpack=True)
    imax = indices[-1]

    volumes_cut = volumes[indices > cut]
    indices_cut = indices[indices > cut]

    ratio = 1.3
    block_sizes = [ratio**k for k in
                   range(0, int(log(imax - cut, ratio)) - 3)]
    stdevs = []
    for bs in block_sizes:
        _, stdev = blocked_mean_std(indices_cut, volumes_cut, bs)
        stdevs += [stdev]

    block, _ = select_from_plot(Point, block_sizes, stdevs, i, proj_axis='y',
                                block=True)
    if block == None or block == -1:
        print('Nothing done.')
        return None
    block = int(block)

    return block

def eval_volume(p_dir):
    from os import chdir, getcwd
    import json
    from numpy import loadtxt

    cwd = getcwd()
    chdir(p_dir)

    with open('measures.json', 'r') as file:
        measures = json.load(file)

    cut = measures['cut']
    block = measures['block']

    vol_file = 'history/volumes.txt'
    indices, volumes = loadtxt(vol_file, unpack=True)

    volumes_cut = volumes[indices > cut]
    indices_cut = indices[indices > cut]

    vol, err = blocked_mean_std(indices_cut, volumes_cut, block)

    chdir(cwd)

    return vol, err

def compute_torelons(p_dir, plot):
    from os import chdir, getcwd
    import json
    import numpy as np
    from matplotlib import pylab as pl

    cwd = getcwd()
    chdir(p_dir)

    with open('measures.json', 'r') as file:
        measures = json.load(file)

    cut = measures['cut']
    block = measures['block']

    toblerone = 'history/toblerone.txt'
    A = np.loadtxt(toblerone, unpack=True)

    indices = A[0]
    torelons = A[1:].transpose()

    torelons_cut = torelons[indices > cut]
    indices_cut = indices[indices > cut]

    # the sum over 'i' is the sum over
    torelons_shift = np.array([np.roll(torelons_cut, Δt, axis=1)
                               for Δt in range(1, torelons_cut.shape[1])])
    torelons_decay = (np.einsum('kij,ij->k', torelons_shift, torelons_cut) -
                      torelons_cut.mean()**2)
           # np.einsum('ij,ij', torelons_cut, torelons_cut) / torelons_cut.size)

    # Run the following to be sure that the previous is the right formula
    # -------------------------------------------------------------------
    #
    # torelons_decay = np.einsum('kij,ij->ik', torelons_shift, torelons_cut)
    #
    # print(torelons_decay.shape)
    # torelons_decay1 = []
    # for torelon in torelons_cut:
    #     l = []
    #     for t in range(1, torelons_cut.shape[1]):
    #         l += [torelon @ np.roll(torelon, t)]
    #     torelons_decay1 += [np.array(l)]
    # torelons_decay1 = np.array(torelons_decay1)
    # print(torelons_decay1.shape)
    # print(((torelons_decay1 - torelons_decay) > 1e-7).any())

    if plot:
        pl.title(f'Number of points: {len(indices_cut)}')
        pl.plot(torelons_decay)
        pl.show()

    chdir(cwd)

    return list(torelons_decay)

def fit_volume(lambdas, volumes, errors, betas):
    import sys
    import json
    from pprint import pprint
    import numpy as np
    from scipy.optimize import curve_fit
    from scipy.stats import chi2
    from matplotlib.pyplot import figure, show, savefig

    if len(set(betas)) > 1:
        print('Volume fit is possible only for fixed β.')
        print('Instead following β were given:\n{set(betas)}')
        return

    class MyPrint:
        def __init__(self, filename):
            self.file = open(filename, 'w')

        def __del__(self):
            self.file.close()

        def write(self, *args, sep=' ', end='\n'):
            from re import sub
            print(*args, sep=sep, end=end)
            new_args = []
            for x in args:
                new_args += [sub('\033.*?m', '', str(x))]
            self.file.write(sep.join(new_args) + end)

    my_out = MyPrint('output.txt')
    my_fit_msg = MyPrint('fit_messages.txt')

    lambdas = np.array(lambdas)
    volumes = np.array(volumes)
    errors = np.array(errors)

    fig = figure()
    ax = fig.add_subplot(111)

    ax.errorbar(lambdas, volumes, yerr=errors, fmt='none', capsize=5)

    def vol_fun(l, l_c, alpha, A):
        return A*(l - l_c)**(-alpha)

    my_fit_msg.write('\033[36m')
    my_fit_msg.write('Messages from fit (if any):')
    my_fit_msg.write('--------------------------')
    my_fit_msg.write('\033[0m')
    stderr_save = sys.stderr
    sys.stderr = my_fit_msg

    par, cov = curve_fit(vol_fun, lambdas, volumes, sigma=errors,
                         absolute_sigma=True, p0=(min(lambdas)*0.7, 2.4, 61))
                         # bounds=((min(lambdas), -np.inf, -np.inf), (np.inf, np.inf, np.inf)))
    err = np.sqrt(np.diag(cov))

    sys.stderr = stderr_save
    my_fit_msg.write('\033[36m', end='')
    my_fit_msg.write('--------------------------')
    my_fit_msg.write('End fit')
    my_fit_msg.write('\033[0m')

    residuals_sq = ((volumes - np.vectorize(vol_fun)(lambdas, *par))/errors)**2
    χ2 = residuals_sq.sum()
    dof = len(lambdas) - len(par)
    p_value = chi2.sf(χ2, dof)
    p_al = 31 if 0.99 < p_value or p_value < 0.01 else 0

    β = str(betas[0])
    my_out.write('\033[38;5;87m┌──', '─' * len(β), '──┐', sep='')
    my_out.write(f'│β = {β}│')
    my_out.write('└──', '─' * len(β), '──┘\033[0m\n', sep='')

    my_out.write('\033[94mFunction:\033[0m')
    my_out.write('\tf(λ) = A*(λ - λ_c)**(-α)')

    my_out.write('\033[94mFit evaluation:\033[0m')
    my_out.write('\t\033[93mχ²\033[0m =', χ2)
    my_out.write('\t\033[93mdof\033[0m =', dof)
    my_out.write(f'\t\033[93mp-value\033[0m = \033[{p_al}m', p_value,
                  '\033[0m')

    names = ['λ_c', 'α', 'A']

    my_out.write('\033[94mOutput parameters:\033[0m')
    for x in zip(names, zip(par, err)):
        my_out.write(f'\t\033[93m{x[0]}\033[0m = {x[1][0]} ± {x[1][1]}')

    n = len(par)
    corr = np.zeros((n, n))
    for i in range(0, n):
        for j in range(0, n):
            corr[i,j] = cov[i,j]/np.sqrt(cov[i,i]*cov[j,j])

    my_out.write('\033[94mCorrelation coefficients:\033[0m')
    my_out.write("\t" + str(corr).replace('\n','\n\t'))

    l_inter = np.linspace(min(lambdas), max(lambdas), 1000)
    ax.plot(l_inter, vol_fun(l_inter, *par))

    savefig('fit.pdf')
    show()