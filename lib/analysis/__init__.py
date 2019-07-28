# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 11:32:00 2019

@author: alessandro
"""

from numpy import loadtxt
from matplotlib.pyplot import plot, imshow, colorbar, figure, savefig, subplots, subplots_adjust, close

# PRELIMINARY ANALYSES

def preliminary_analyses(kind, configs=None, conf_plot=False, path=None,
                         load_path=None, caller_path=None):
    from re import fullmatch
    from lib.utils import find_configs
    import lib.analysis.pre as pre

    if path:
        from os.path import realpath
        path = realpath(caller_path + '/' + path)

    if load_path:
        from os.path import realpath
        load_path = realpath(caller_path + '/' + load_path)

    if configs:
        pattern_configs = []
        pure_configs = []
        all_configs = list(find_configs().keys())
        for config in configs:
            if config[0] == '§':
                pattern_configs += [c for c in all_configs
                                    if fullmatch(config[1:], c)]
            else:
                pure_configs += [config]

        configs = list(set(pure_configs + pattern_configs))
        print(f'Chosen configs are:\n  {configs}')
    else:
        configs = list(find_configs().keys())

    if kind in ['mv', 'mean-volumes']:
        pre.mean_volumes(configs, path)
    elif kind in ['vp', 'volumes-plot']:
        pre.volumes_plot(configs, path)
    elif kind in ['d', 'divergent']:
        pre.divergent_points(configs, conf_plot, path, load_path)
    else:
        raise RuntimeError('preliminary_analyses: kind not recognized')

def sim_paths():
    from lib.utils import find_configs
    from os import scandir

    configs = find_configs()

    d = {}
    for name, path in configs.items():
        sims = [x.path for x in scandir(path)
                if x.is_dir() and 'Lambda' in x.name]
        d[name] = sims

    return d

# FIT MANAGEMENT

def new_fit(name, path, caller_path):
    from os.path import isdir, isfile, abspath, basename
    from os import chdir, mkdir, listdir
    from inspect import cleandoc
    import json
    from lib.utils import find_fits, project_folder

    msg_exist = cleandoc("""The requested fit already exists.
                If you want to reset it, please use the specific command.""")

    fits = find_fits()

    chdir(caller_path)

    # actually creates requested folder
    if not path:
        path = caller_path + '/' + name

    if name in fits.keys() or abspath(path) in fits.values():
        print(msg_exist)
        return
    elif basename(path) != name:
        print('At the present time names different from target '
              'directories are not available.')
        return
    else:
        try:
            mkdir(path)
        except (FileExistsError, FileNotFoundError):
            print('Invalid path given.')
            return

    print(f"Created fit '{name}' at path:\n  {abspath(path)}")

    fits = {**fits, name: abspath(path)}
    with open(project_folder() + '/output/fits.json', 'w') as fit_file:
        json.dump(fits, fit_file, indent=4)

def show_fits(paths):
    from lib.utils import find_fits, project_folder
    import pprint as pp

    fits = find_fits()

    if paths:
        for name, path in sorted(fits.items(), key=lambda x: x[0].lower()):
            print(name, path, sep=':\n\t')
    else:
        if isinstance(fits, dict):
            fits = list(fits.keys())

        for name in sorted(fits, key=str.lower):
            print(name)

def reset_fit(names, delete):
    from os.path import isdir
    from os import chdir, mkdir
    from shutil import rmtree
    from re import fullmatch
    import json
    from lib.utils import (authorization_request, fit_dir, find_fits,
                           project_folder)

    pattern_names = []
    pure_names = []
    all_names = list(find_fits().keys())
    for name in names:
        if name[0] == '§':
            pattern_names += [c for c in all_names
                                if fullmatch(name[1:], c)]
        else:
            pure_names += [name]

    names = list(set(pure_names + pattern_names))
    print(f'Chosen fits are:\n  {names}')

    for name in names:
        fit = fit_dir(name)

        if delete:
            action = 'delete'
            action_p = action + 'd'
        else:
            action = 'reset'
            action_p = action

        what_to_do = 'to ' + action + ' the fit \'' + name + '\''
        authorized = authorization_request(what_to_do)
        if authorized == 'yes':
            rmtree(fit)
            if action == 'reset':
                mkdir(fit)
            elif action == 'delete':
                with open(project_folder() + '/output/fits.json', 'r') as file:
                    fits = json.load(file)
                del fits[name]
                with open(project_folder() + '/output/fits.json', 'w') as file:
                    json.dump(fits, file, indent=4)
            print(f'Fit {name} has been {action_p}.')
        elif authorized == 'quit':
            print('Nothing done on last fit.')
            return
        else:
            print('Nothing done.')

# def rm_conf(config, force):
#     from os import rmdir, remove
#     from os.path import isfile
#     import json
#     from lib.utils import points_recast, config_dir, project_folder
#
#     points_old, _ = points_recast([], [], '', True, config, 'tools')
#     clear_data(points_old, config, force)
#
#     path = config_dir(config)
#     if isfile(path + '/pstop.pickle'):
#         remove(path + '/pstop.pickle')
#     rmdir(path)
#     print(f"Removed config '{config}' at path:\n  {path}")
#
#     with open(project_folder() + '/output/configs.json', 'r') as config_file:
#         configs = json.load(config_file)
#
#     del configs[config]
#
#     with open(project_folder() + '/output/configs.json', 'w') as config_file:
#         json.dump(configs, config_file, indent=4)


def set_fit_props(name, points, config, remove):
    from os import chdir, popen
    from os.path import basename, dirname
    import json
    from lib.utils import (fit_dir, config_dir, point_dir, dir_point,
                           authorization_request)

    if remove:
        if points:
            print('Warning: points specification not compatible with --remove '
                  'option.')
            return
        elif config != 'test':
            print('Warning: config specification not compatible with --remove '
                  'option.')
            return

    chdir(fit_dir(name))

    try:
        with open('sims.json', 'r') as file:
            sims = json.load(file)
    except FileNotFoundError:
        sims = []

    # SIMS UPDATE

    if not remove:
        c_dir = config_dir(config)
        for Point in points:
            p_dir = c_dir + '/' + point_dir(Point)
            if p_dir not in sims:
                sims += [p_dir]

        with open('sims.json', 'w') as file:
            json.dump(sims, file, indent=4)

    # SIMS REMOTION

    else:
        new_sims = sims.copy()
        for sim in sims:
            Point = dir_point(basename(sim))
            config = basename(dirname(sim))

            what = f"to remove sim from fit '{name}'"
            extra = f"\033[38;5;80m  config: '{config}'\033[0m"
            auth = authorization_request(Point=Point, what_to_do=what,
                                         extra_message=extra)

            if auth == 'quit':
                print('Nothing done for last sim.')
                return
            elif auth == 'yes':
                new_sims.remove(sim)
                with open('sims.json', 'w') as file:
                    json.dump(new_sims, file, indent=4)
                print('Sim removed')
            else:
                print('Nothing removed.')

    # inserire un kind e aggiungere come possibilità quella di settare il tipo di osservabili
    # a cui è riferito il fit (1 sola)
    # cioè se è un fit: al volume, all'azione, alla carica topologica, ...

def info_fit(name, kind='sims'):
    from os import chdir
    from os.path import basename, dirname
    from pprint import pprint
    import json
    from lib.utils import fit_dir, config_dir, dir_point

    if kind in ['s', 'sims', None]:
        kind = 'sims'
    elif kind in ['o', 'obs']:
        kind = 'obs'

    chdir(fit_dir(name))

    try:
        with open('sims.json', 'r') as file:
            sims = json.load(file)
    except FileNotFoundError:
        print('No simulation already assigned to this fit.')

    d = {}
    for s in sims:
        if s[-1] == '/':
            s = s[:-1]

        if kind == 'sims':
            config = basename(dirname(s))
            Point = dir_point(basename(s))
            try:
                d[config] += [Point]
            except KeyError:
                d[config] = [Point]
        elif kind == 'obs':
            try:
                with open(s + '/measures.json', 'r') as file:
                    measures = json.load(file)
            except FileNotFoundError:
                measures = {}

            flags = ''
            if 'cut' in measures.keys():
                flags += 'C'
            if 'block' in measures.keys():
                flags += 'B'
            if 'volume' in measures.keys():
                flags += 'V'

            config = basename(dirname(s))
            Point = dir_point(basename(s))
            try:
                d[config] += [Point, flags]
            except KeyError:
                d[config] = [Point, flags]


    if kind == 'sims':
        pprint(d)
    elif kind == 'obs':
        pprint(d)
    else:
        raise ValueError('info-fit: kind {kind} not recognized')

    # inserire un kind e aggiungere come possibilità quella di visualizzare il tipo di osservabili
    # dato che ogni fit sarà un fit di 1 osservabile basterà un 'obs'
    # 'obs' attualmente è per le sole flag, ne va implementato uno più esteso con i valori opportuni

def sim_obs(points, config, plot, fit_name):
    from os import chdir
    from os.path import isfile, basename, dirname, realpath
    from time import time
    from datetime import datetime
    import json
    from pprint import pprint
    from lib.utils import (config_dir, point_dir, dir_point, fit_dir,
                           authorization_request, eng_not)
    from lib.analysis.fit import (set_cut, set_block, eval_volume,
                                  compute_torelons, compute_profiles_corr)

    if fit_name:
        f_dir = fit_dir(fit_name)
        try:
            with open(f_dir + '/sims.json', 'r') as file:
                sims = json.load(file)
        except FileNotFoundError:
            print('No simulation already assigned to this fit.')

        points = []
        points_configs = {}
        for s in sims:
            if s[-1] == '/':
                s = s[:-1]

            Point = dir_point(basename(s))
            points += [Point]
            points_configs = {**points_configs, Point: realpath(dirname(s))}
    else:
        points_configs = None
        c_dir = config_dir(config)

    col = 216 # color
    print(f'Number of selected points: \033[38;5;{col}m{len(points)}\033[0m')
    print(f'\033[38;5;{col}m', end='')
    pprint(points)
    print('\033[0m')

    i = 0
    for Point in points:
        if points_configs:
            c_dir = points_configs[Point]
        p_dir = c_dir + '/' + point_dir(Point)
        chdir(p_dir)
        vol = None

        if isfile(p_dir + '/max_volume_reached'):
            print(f'\033[38;5;41m(λ, β) = {Point}\033[0m skipped because '
                  '\033[38;5;80mmax_volume_reached\033[0m is present.')
            # print(f"\033[38;5;80m  config: '{config}'\033[0m")
            continue

        try:
            with open('state.json', 'r') as file:
                state = json.load(file)
        except FileNotFoundError:
            print(f'\033[1mCRITICAL:\033[0m no state.json file in sim'
                  f'\033[38;5;41m(λ, β) = {Point}\033[0m')
            return

        try:
            with open('measures.json', 'r') as file:
                measures = json.load(file)

            if 'cut' in measures.keys() and 'block' in measures.keys():
                cb_exist = True
            else:
                cb_exist = False
        except FileNotFoundError:
            measures = {}
            cb_exist = False

        what = 'to select cut & block'
        extra = ('\033[92m(existing value present for both)\033[0m'
                 if cb_exist else None)
        auth = authorization_request(what_to_do=what, Point=Point,
                                     extra_message=extra)

        if auth == 'quit':
            print('Nothing done on the last sim.')
            return
        elif auth == 'yes':
            try:
                measures['cut'] = state['linear-history-cut']
                cut = state['linear-history-cut']
                with open('measures.json', 'w') as file:
                    json.dump(measures, file, indent=4)
                print("\033[38;5;80m'linear-history-cut'\033[0m "
                      "has been used as cut")
            except KeyError:
                cut = set_cut(p_dir, i)
                if cut:
                    measures['cut'] = cut
                    with open('measures.json', 'w') as file:
                        json.dump(measures, file, indent=4)
                try :
                    cut = measures['cut']
                except KeyError:
                    pass
            if cut:
                print(f'cut = {eng_not(cut)} ({cut})', end='   ')

            block = set_block(p_dir, i)
            if block:
                measures['block'] = block
                with open('measures.json', 'w') as file:
                    json.dump(measures, file, indent=4)
            try:
                block = measures['block']
            except KeyError:
                pass
            print(f'block = {eng_not(block)} ({block})', end='   ')

            if not cut or not block:
                print('\nNothing modified on last sim.')
                return

            vol = eval_volume(p_dir)

        what = 'to compute/recompute observables'
        auth = authorization_request(what_to_do=what)

        if auth == 'yes':
            try:
                with open('measures.json', 'r') as file:
                    measures = json.load(file)
            except FileNotFoundError:
                measures = {}

            measures['volume'] = vol if vol else eval_volume(p_dir)
            measures['torelon-decay'] = compute_torelons(p_dir, plot)
            measures['profiles_corr'] = compute_profiles_corr(p_dir, plot)
            measures['time'] = datetime.fromtimestamp(time()
                                        ).strftime('%d-%m-%Y %H:%M:%S')

            with open('measures.json', 'w') as file:
                json.dump(measures, file, indent=4)
        elif auth == 'quit':
            print('Observables have not been recomputed.')
            return
        else:
            print('Observables have not been recomputed.')

        i += 1

def export_data(name, unpack):
    from os import chdir
    from os.path import basename, dirname, isfile
    import json
    from lib.utils import fit_dir, dir_point

    fit_d = fit_dir(name)
    chdir(fit_d)

    if not unpack:
        try:
            with open('sims.json', 'r') as file:
                sims = json.load(file)
        except FileNotFoundError:
            print('No simulation assigned to this fit.')
            return

        data = []
        for s in sims:
            if s[-1] == '/':
                s = s[:-1]

            config = basename(dirname(s))
            Point = dir_point(basename(s))
            point_data = {}

            if isfile(s + '/max_volume_reached'):
                print(f'\033[38;5;41m{Point}\033[0m not included in fit, '
                      'because '
                      '\033[38;5;80mmax_volume_reached\033[0m is present.')
                print(f"\033[38;5;80m  config: '{config}'\033[0m")
                continue
            try:
                with open(s + '/measures.json', 'r') as file:
                    measures = json.load(file)
            except FileNotFoundError:
                print(f'\033[38;5;41m{Point}\033[0m no measure file present.')
                print(f"\033[38;5;80m  config: '{config}'\033[0m")
                continue

            point_data['lambda'] = Point[0]
            point_data['beta'] = Point[1]
            point_data['config'] = config
            point_data.update(measures.copy())

            for prop in ['cut', 'block', 'time']:
                try:
                    del point_data[prop]
                except KeyError:
                    pass

            data += [point_data]
            print(f'\033[38;5;41m{Point}\033[0m collected.')

        with open('data.json', 'w') as file:
            json.dump(data, file, indent=4)

    elif unpack in ['v', 'volumes']:
        try:
            with open('data.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            print("No data file (\033[38;5;80m'data.json'\033[0m) to unpack.")
            return

        vol_data = []
        for point_data in data:
            Point = (point_data['lambda'], point_data['beta'])
            config = point_data['config']
            try:
                volume = point_data['volume']
            except KeyError:
                continue
            # print(f'\033[38;5;41m{Point}\033[0m, {config}:')
            # print('\t', volume)
            vol_data += [[Point[0], Point[1], volume[0], volume[1], config]]

        with open('volumes.csv', 'w') as file:
            sep = ' '
            end = '\n'
            file.write('# Lambda Beta Volume Error Config' + end)
            for point_vol in vol_data:
                str_point_vol = []
                for x in point_vol:
                    str_point_vol += [str(x)]
                file.write(sep.join(str_point_vol) + end)

        print(f"\033[38;5;41m({name})\033[0m volumes from "
              "\033[38;5;80m'data.json'\033[0m unpacked to "
              "\033[38;5;80m'volumes.csv'\033[0m")
    elif unpack in ['p', 'profiles']:
        try:
            with open('data.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            print("No data file (\033[38;5;80m'data.json'\033[0m) to unpack.")
            return

        profile_data = []
        for point_data in data:
            Point = (point_data['lambda'], point_data['beta'])
            config = point_data['config']
            try:
                # print(Point)
                profile, errors = point_data['profiles_corr']
                # print(len(point_data['profiles_corr']))
            except KeyError:
                continue

            profile_data += [[Point[0], Point[1], config, *profile, *errors]]

        with open('profiles.csv', 'w') as file:
            sep = ' '
            end = '\n'
            file.write('# Lambda[0] Beta[1] Config[2] Profile[3:3+t}] ' +
                  'Errors[3+t:3+2t]' + end)
            for point_profile in profile_data:
              str_point_profile = []
              for x in point_profile:
                  str_point_profile += [str(x)]
              file.write(sep.join(str_point_profile) + end)

        print(f"\033[38;5;41m({name})\033[0m profiles from "
            "\033[38;5;80m'data.json'\033[0m unpacked to "
            "\033[38;5;80m'profiles.csv'\033[0m")
    elif unpack in ['t', 'torelons']:
        try:
            with open('data.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            print("No data file (\033[38;5;80m'data.json'\033[0m) to unpack.")
            return

        torelon_data = []
        for point_data in data:
            Point = (point_data['lambda'], point_data['beta'])
            config = point_data['config']
            try:
                # print(Point)
                torelon, errors = point_data['torelon-decay']
                # print(len(point_data['torelon-decay']))
            except KeyError:
                continue

            torelon_data += [[Point[0], Point[1], config, *torelon, *errors]]

        with open('torelons.csv', 'w') as file:
            sep = ' '
            end = '\n'
            file.write('# Lambda[0] Beta[1] Config[2] Torelon[3:3+t}] ' +
                  'Errors[3+t:3+2t]' + end)
            for point_torelon in torelon_data:
              str_point_torelon = []
              for x in point_torelon:
                  str_point_torelon += [str(x)]
              file.write(sep.join(str_point_torelon) + end)

        print(f"\033[38;5;41m({name})\033[0m torelons from "
               "\033[38;5;80m'data.json'\033[0m unpacked to "
               "\033[38;5;80m'torelons.csv'\033[0m")

def fit_divergence(name, kind='volumes', reload=False):
    from os import chdir
    from os.path import basename, dirname, isfile
    from datetime import datetime
    import json
    from pprint import pprint
    from numpy import genfromtxt
    from lib.utils import fit_dir, dir_point
    from lib.analysis.fit import fit_divergence

    if kind in ['v', 'volumes']:
        kind = 'volumes'
        kind_file = 'volumes'
    elif kind in ['p', 'profiles']:
        kind = 'profiles'
        kind_file = 'profiles_length'
    elif kind in ['t', 'torelons']:
        kind = 'torelons'
        kind_file = 'torelons_length'
    else:
        raise ValueError(f'{kind} not available for divergence fit.')

    fit_d = fit_dir(name)
    chdir(fit_d)

    try:
        with open('sims.json', 'r') as file:
            sims = json.load(file)
    except FileNotFoundError:
        print('No simulation already assigned to this fit.')
        # do not return, because if 'kind.csv' is present it can use that

    if not isfile(f'{kind_file}.csv') or reload:
        d = {}
        lambdas = []
        betas = []
        means = []
        errors = []
        for s in sims:
            if s[-1] == '/':
                s = s[:-1]

            config = basename(dirname(s))
            Point = dir_point(basename(s))

            if isfile(s + '/max_volume_reached'):
                print(f'\033[38;5;41m{Point}\033[0m not included in fit, '
                      'because '
                      '\033[38;5;80mmax_volume_reached\033[0m is present.')
                print(f"\033[38;5;80m  config: '{config}'\033[0m")
                continue

            try:
                with open(s + '/measures.json', 'r') as file:
                    measures = json.load(file)
            except FileNotFoundError:
                measures = {}

            with open(s + '/state.json', 'r') as file:
                state = json.load(file)

            if 'time' in measures.keys():
                s_time = datetime.strptime(state['end_time'],
                                           '%d-%m-%Y %H:%M:%S')
                m_time = datetime.strptime(measures['time'],
                                           '%d-%m-%Y %H:%M:%S')
            else:
                print(f'Mising time in {Point}, in config: {config}.')
                return

            # print(Point)
            # print(s_time, type(s_time), '\n' + str(m_time), type(m_time))
            if(s_time > m_time):
                print('\033[38;5;203mWarning:\033[0m in Point '
                      f'\033[38;5;41m{Point}\033[0m in '
                      f"\033[38;5;80mconfig: '{config}'\033[0m measures are "
                      '\033[38;5;210mnot up to date\033[0m '
                      'with last simulation\'s data')
                print()

            d[Point] = {'config': config, **measures,
                        'time_sim_end': state['end_time']}

            k_key = f'{kind}'[:-1]
            if k_key in measures.keys():
                lambdas += [Point[0]]
                betas += [Point[1]]
                means += [measures[k_key][0]]
                errors += [measures[k_key][1]]
            else:
                print(f"Missing {k_key} in {Point}, in config: {config}.")
                return

        with open(f'{kind_file}.csv', 'w') as file:
            file.write('# Lambda Beta Volume Error Config\n')
            for Point, attr in d.items():
                mean, err = attr[f'{kind}'[:-1]]
                data = [Point[0], Point[1], mean, err, attr['config']]
                line = ' '.join([str(x) for x in data])
                file.write(line + '\n')
    else:
        data = genfromtxt(f'{kind_file}.csv', unpack=True)
        lambdas, betas = data[:2]
        means, errors = data[2:4]

    fit_divergence(lambdas, means, errors, betas, kind=kind)
