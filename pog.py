import os.path
from itertools import chain
from util import load_yaml_file, write_yaml_file, plu, SQ


def reduce_group_from_file(name):
    """Aggregates all the group IDs given in a "groups" YAML file, both those given as integers keyed by "types" and
    those given indirectly by including other groups files named under the key "include". May be called recursively by
    reduce_groups().

    :param name: filename (extension should be included) from which the data should be loaded
    :return: set of group IDs that results from combining this file's group IDs along with the group IDs given by
     other included "groups" files
    """
    group = load_yaml_file("groups", name)
    return reduce_groups(group.get('types', []), group.get('include', []))


def reduce_groups(types, names):
    """Aggregates group IDs given by 'types' with the group IDs given by the "groups" files given in 'names'.
    May be called recursively by reduce_group_from_file().

    :param types: an iterable with group IDs to be included
    :param names: an iterable with filenames (no extensions) giving the groups files to be included
    :return: set of (unique) group IDs resulting from the union
    """
    try:
        return set(types).union(chain.from_iterable(map(reduce_group_from_file, names)))
    except KeyError:
        return set()


def merge_groups(group_names):
    """Aggregates the group IDs given by all the named "groups" files.

    :param group_names: an iterable with filenames (no extensions) giving the groups files to be included
    :return: sorted list of unique group IDs from all indicated files
    """
    return list(sorted(reduce_groups([], group_names)))


def format_tabs(tabs):
    """Parses tab information to be in a YAML-friendly format.

    :param tabs: a dictionary of tabs information
    :return: a dictionary keyed by 'tabSetup' ready for export to an overview YAML file
    """
    tabs = [[i, [
            ['name', format_tab_name(v)],
            ['overview', format_preset_name(load_preset(v['overview']))],
            ['bracket', format_preset_name(load_preset(v['bracket']))]
            ]] for (i, v) in enumerate(tabs)]

    return {'tabSetup': tabs}


def merge_states(names):
    """Aggregates show/hide state information given by all the named "states" files.

    :param names: an iterable with filenames (no extensions) giving the states files to be included
    :return: a dictionary of sorted lists giving the 'show' and 'hide' states, keyed respectively
    """
    merged_states = {'show': set(), 'hide': set()}

    states = [load_yaml_file("states", name) for name in names]
    for state in states:
        try:
            merged_states['show'].update(set(state['show']))
        except KeyError:
            pass
        try:
            merged_states['hide'].update(list(state['hide']))
        except KeyError:
            pass

    merged_states['show'] = sorted(list(merged_states['show']))
    merged_states['hide'] = sorted(list(merged_states['hide']))

    return merged_states


def load_preset(name):
    """Load a preset file by name by looking in the 'presets' subdirectory.

    :param name: the filename (no extension) of the preset YAML file
    :return: result of loading the specified file
    """
    return load_yaml_file("presets", name)


def format_preset(preset):
    """Parses preset information to be in a YAML-friendly format.

    :param preset: a dictionary of tabs information
    :return: a list containing the same information, ready for export to an overview YAML file
    """

    states = merge_states(preset['states'])
    return [
        format_preset_name(preset), [
            ['alwaysShownStates', states['show']],
            ['filteredStates', states['hide']],
            ['groups', merge_groups(preset['groups'])],
        ]]


def format_preset_name(preset):
    """Parses the name for a given preset.

    :param preset: a dictionary of preset information
    :return: a Single Quoted string representing the preset's name, ready for export to a YAML file
    """
    #return SQ(f"{preset['symbol']} {'- ' * (4 - preset['level'])}{preset['name']}")
    name = f"{preset['symbol']} {preset['name']}"
    try:
        color = preset['color']
    except KeyError:
        pass
    else:
        name = f"<color=0x{color}>" + name + "</color"
    return SQ(name)


def format_tab_name(tab):
    """Parses the name for a given tab.

    :param tab: a dictionary of tab information
    :return: a Single Quoted string representing the tab's name, ready for export to a YAML file
    """
    return SQ(f"<color=0x{tab['color']}>   {tab['name']}   </color>")


def compile_overview(path, ov):
    """Combines all given information to produce a single YAML file formatted to be imported as an EVE overview.

    :param path: the destination path for the new overview file (will over-write existing files)
    :param ov: dictionary of overview information
    """
    merged_overviews = {}
    overview = ov.copy()

    presets = []
    for k, v in overview.items():
        k_plural = plu.plural(k) if plu.singular_noun(k) is False else k  # overkill

        if k == "tabs":
            pass
        elif k == "presets":
            for p in v:
                presets.append(
                    format_preset(
                        load_preset(p)
                    )
                )
        else:
            opts = load_yaml_file(k_plural, v)
            if k == "tab":
                merged_overviews.update(format_tabs(opts))
            else:
                merged_overviews.update(opts)

    merged_overviews['presets'] = presets

    write_yaml_file(merged_overviews, path)


def compile_overviews():
    """Compile all overview files given in the "overviews" (lower-case 'o') subdirectory.
    """

    def get_all_presets():
        if len(get_all_presets.all) < 1:
            get_all_presets.all = [format_preset(load_yaml_file("presets", filename[:-4])) for filename in
                                   sorted(os.listdir("presets"))
                                   if filename[-4:] == ".yml" and os.path.isfile(os.path.join("presets", filename))
                                   ]
        return get_all_presets.all
    get_all_presets.all = []

    for filename in os.listdir("overviews"):
        f = os.path.join("overviews", filename)
        if filename[-4:] == ".yml" and os.path.isfile(f):
            filename = filename[:-4]

            print(f"Working with overview file {filename}")
            overview = load_yaml_file("overviews", filename)
            presets = overview.get('presets', {})

            for tab_name in overview['tabs']:
                overview['tab'] = tab_name
                overview['presets'] = presets.get(tab_name, get_all_presets())

                print(f" {tab_name}.yaml")
                compile_overview(os.path.join("Overview", f"{filename}_{tab_name}.yaml"), overview)


if __name__ == "__main__":
    compile_overviews()
