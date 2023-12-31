import os.path
from itertools import chain
from util import load_yaml_file, write_yaml_file, plu, SQ, write_annotated_groups


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


def format_tab_color(tab):
    """Formats a tab's color (given in 6-digit hex code) into a list of non-negative floats each <= 1.0. """

    def floatify(s):
        # Ex:  "F5" --> 245/255 --> 0.9607
        return int((int(s, 16) / 255) * 10000) / 10000

    color_string = tab.get('color', None)
    try:
        return [
            floatify(color_string[0:2]),
            floatify(color_string[2:4]),
            floatify(color_string[4:6]),
        ]
    except (IndexError, TypeError, ValueError):  # wrong str len, color == None, color == ''
        return None


def format_tabs(tabs):
    """Parses tab information to be in a YAML-friendly format.

    :param tabs: a dictionary of tabs information
    :return: a dictionary keyed by 'tabSetup' ready for export to an overview YAML file
    """
    tabs = [[i, [
            ['name', format_tab_name(v)],
            ['overview', format_preset_name(load_preset(v['overview']))],
            ['bracket', format_preset_name(load_preset(v['bracket']))],
            ['color', format_tab_color(v)]
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
    return SQ(name)


def format_tab_name(tab):
    """Parses the name for a given tab.

    :param tab: a dictionary of tab information
    :return: a Single Quoted string representing the tab's name, ready for export to a YAML file
    """
    return SQ(f"{tab['name']}")


def determine_new_entities(filename="__new"):
    """
    Uses an exported overview file from the game client marked to show 'All' entities to determine new group IDs that
    are not yet included in one of the group files contained in the 'groups' subdirectory.
    Will attempt to annotate the output file with comments, but this depends on invGroups and invCategories files
    being present in the current directory:  https://www.fuzzwork.co.uk/dump/latest/
    :param filename: optional filename where the results will be written
    """
    group_filenames = [f for f in os.listdir('groups') if os.path.isfile(os.path.join("groups", f))]
    group_names = [fn[:-4] for fn in group_filenames]
    merged_groups = set(merge_groups(group_names))
    # Above now contains all groups merged from all group files in 'groups' subdir

    o = load_yaml_file("Overview", "overview_all")
    groups_from_client = set(o['presets'][0][1][2][1])
    # Above now contains all groups according to exported overview from EVE client

    new_groups = sorted(groups_from_client - merged_groups)
    # Take the set difference then sort the result into a list

    write_annotated_groups("groups/" + filename + ".yml", new_groups)  # E.g., "_entity_insurgency-pirates"


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
            try:
                for p in v:
                    presets.append(
                        format_preset(
                            load_preset(p)
                        )
                    )
            except TypeError:  # 'NoneType' is not iterable
                pass
        else:
            try:
                opts = load_yaml_file(k_plural, v)
            except FileNotFoundError as e:
                raise Exception("File not found while processing overview file " + path) from e

            if k == "tab":
                try:
                    merged_overviews.update(format_tabs(opts))
                except FileNotFoundError as e:
                    raise Exception("File not found while processing overview file " + path) from e
            else:
                merged_overviews.update(opts)

    merged_overviews['presets'] = presets

    write_yaml_file(merged_overviews, path)


def compile_overviews():
    """Compile all overview files given in the "overviews" (lower-case 'o') subdirectory.
    """

    def all_preset_names():
        """
        Retrieve all preset names from .YML files in 'presets' directory. This only needs to be done once, so store
        result internal to function and perform checks to ensure we don't subsequently hit disk again.
        :return: list of names for all preset files
        """
        try:
            length_all = len(all_preset_names.all)
        except AttributeError:
            all_preset_names.all = []
            length_all = 0
        if length_all < 1:
            all_preset_names.all = [filename for filename in sorted(os.listdir("presets"))
                                   if filename[-4:] == ".yml" and os.path.isfile(os.path.join("presets", filename))
                                   ]
        return all_preset_names.all

    for filename in os.listdir("overviews"):
        f = os.path.join("overviews", filename)
        if filename[-4:] == ".yml" and os.path.isfile(f):
            filename = filename[:-4]

            print(f"Working with overview file {filename}")
            overview = load_yaml_file("overviews", filename)
            presets = overview.get('presets', {})

            for tab_name in overview['tabs']:
                overview['tab'] = tab_name
                overview['presets'] = presets.get(tab_name, all_preset_names())  # Default for tab is to use ALL presets

                print(f" {tab_name}.yaml")
                compile_overview(os.path.join("Overview", f"{filename}_{tab_name}.yaml"), overview)


if __name__ == "__main__":
    compile_overviews()
